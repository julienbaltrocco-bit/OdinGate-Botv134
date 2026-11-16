"""Tests des Papier-Runners mit künstlichen Daten (ohne Netz): Regel, Konto, Wiederholbarkeit, Sperre, Regelschutz."""
import copy
import datetime as dt
import fcntl
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from forschung.papier import runner as R
from forschung.papier.strategien import orderbuch_stuetze as S

P = {"tiefe_pct": 5, "fenster": 288, "min_perioden": 200, "einstieg_z": 3.0, "ausstieg_z": 1.0, "zeitlimit": 48}
T0 = R.ms("2026-01-01T00:00:00Z")


def _daten(n=900, sprung=(400, 420), kurs=lambda i: 100.0 + 0.01 * i):
    kz = [(T0 + i * R.KERZE_MS, kurs(i), kurs(i) * 1.001, kurs(i) * 0.999, kurs(i + 1)) for i in range(n)]
    u = [0.01 * math.sin(i / 7) + (0.5 if sprung[0] <= i < sprung[1] else 0.0) for i in range(n)]
    return kz, u


def test_regel_einstieg_ausstieg_und_richtung():
    kz, u = _daten()
    t = S.trades(kz, u, P, T0)
    assert len(t) == 1 and t[0]["richtung"] == 1.0
    assert t[0]["ein"] == kz[401][0]                       # Signal am Schluss der Kerze 400, Einstieg zur Eröffnung der nächsten
    assert t[0]["aus"] is not None and kz[401][0] < t[0]["aus"] <= kz[401 + 48][0]
    assert abs(t[0]["ein_kurs"] - kz[401][1]) < 1e-12


def test_kein_einstieg_vor_dem_start_und_offener_trade_am_datenende():
    kz, u = _daten()
    assert S.trades(kz, u, P, kz[500][0]) == []
    kz2, u2 = _daten(n=410, sprung=(400, 410))
    t = S.trades(kz2, u2, P, T0)
    assert len(t) == 1 and t[0]["aus"] is None             # Daten enden vor dem Ausstieg: Trade bleibt offen


def test_z_wert_gegen_direkte_rechnung():
    _, u = _daten()
    z = S.z_werte(u, 288, 200)
    w = u[400 - 287: 401]
    m = sum(w) / 288
    s = math.sqrt(sum((x - m) ** 2 for x in w) / 287)
    assert abs(z[400] - (u[400] - m) / s) < 1e-12 and math.isnan(z[150])


@pytest.fixture
def test_umgebung(tmp_path, monkeypatch):
    monkeypatch.setattr(R, "HIER", tmp_path)
    (tmp_path / "strategien").mkdir()
    (tmp_path / "strategien" / "orderbuch_stuetze.py").write_bytes((Path(R.__file__).parent / "strategien" / "orderbuch_stuetze.py").read_bytes())
    cfg = json.loads((Path(R.__file__).parent / "OS-1.1" / "konfiguration.json").read_text())
    cfg.update(coins=["BTC"], start="2026-01-02T00:00:00Z", vorlauf_tage=1)
    cfg["kosten"]["slippage_bp_je_order"] = {"BTC": 0.5}
    kz, u = _daten(n=3 * 288, sprung=(400, 420))
    monkeypatch.setattr(R, "kerzen_tag", lambda sym, tag, cache: [k for k in kz if R.iso(k[0])[:10] == str(tag)] or None)
    monkeypatch.setattr(R, "tiefe_tag", lambda sym, tag, stufe, cache: {k[0]: x for k, x in zip(kz, u) if R.iso(k[0])[:10] == str(tag)} or None)
    monkeypatch.setattr(R, "funding_monat", lambda sym, monat, cache: {})
    return tmp_path, cfg, dt.date(2026, 1, 4)


def test_konto_und_kosten(test_umgebung):
    tmp, cfg, heute = test_umgebung
    d = R.lauf("X", heute, tmp, schreiben=False, cfg=cfg)
    assert d["status"] == "läuft" and d["trades"] == 1 and d["positionsgroesse_usd"] == 15000.0
    roh = d["roh_je_trade_bp"]
    assert abs(d["netto_je_trade_bp"] - (roh - 1.0 - 2.4)) < 0.011                       # 2 x 0,5 bp Slippage, 16 bp Gebühr, 85 % Rebate
    assert abs(d["realisiert_usd"] - 15000 * d["netto_je_trade_bp"] / 1e4) < 0.02
    assert abs(d["gebuehr_usd"] - 24.0) < 1e-9 and abs(d["rebate_usd_angenommen"] - 20.4) < 1e-9
    assert d["rendite_ohne_rebate_pct"] < d["rendite_mit_rebate_pct"]


def test_wiederholung_verdoppelt_nichts(test_umgebung):
    import sqlite3
    tmp, cfg, heute = test_umgebung
    for _ in range(3):
        d = R.lauf("X", heute, tmp, cfg=cfg)
    db = sqlite3.connect(tmp / "zustand" / "X.sqlite")
    assert db.execute("SELECT COUNT(*) FROM trades").fetchone()[0] == 1 and db.execute("SELECT COUNT(*) FROM laeufe").fetchone()[0] == 3
    assert d["fehler"] == [] and json.loads((tmp / "ausgabe" / "X.json").read_text())["trades"] == 1


def test_veraenderte_regel_wird_erkannt_und_pause_wirkt(test_umgebung):
    tmp, cfg, heute = test_umgebung
    c2 = copy.deepcopy(cfg); c2["parameter"]["einstieg_z"] = 2.5
    assert R.lauf("X", heute, tmp, schreiben=False, cfg=c2)["status"] == "Fehler"
    assert R.lauf("X", heute, tmp, schreiben=False, cfg=cfg, steuer={"status": "pausiert"})["status"] == "pausiert"


def test_liquidation_und_verlustgrenze(test_umgebung, monkeypatch):
    tmp, cfg, heute = test_umgebung
    kz, u = _daten(n=3 * 288, sprung=(400, 500), kurs=lambda i: 100.0 if i < 403 else 60.0)   # Kurs bricht nach dem Long-Einstieg um 40 % ein
    monkeypatch.setattr(R, "kerzen_tag", lambda sym, tag, cache: [k for k in kz if R.iso(k[0])[:10] == str(tag)] or None)
    monkeypatch.setattr(R, "tiefe_tag", lambda sym, tag, stufe, cache: {k[0]: x for k, x in zip(kz, u) if R.iso(k[0])[:10] == str(tag)} or None)
    d = R.lauf("X", heute, tmp, schreiben=False, cfg=cfg)
    assert d["status"] == "gescheitert" and "Liquidation" in d["ereignis"] and d["kontostand"] < 0.05 * 5000
    c2 = copy.deepcopy(cfg); c2["hebel"] = 1.0                                               # ohne Hebel: −40 % auf 5.000 $ -> Verlustgrenze 70 %
    d = R.lauf("X", heute, tmp, schreiben=False, cfg=c2)
    assert d["status"] == "abgebrochen" and "Verlustgrenze" in d["ereignis"]


def test_sperre_gegen_doppellauf(test_umgebung):
    tmp, cfg, heute = test_umgebung
    (tmp / "zustand").mkdir(exist_ok=True)
    with open(tmp / "zustand" / "X.sperre", "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        assert R.haupt("X") == 3
