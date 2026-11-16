"""Audit RSK (Risk Engineering): Regressionstests, die den IST-ZUSTAND der risikorelevanten Berechnungen festhalten.

Die Tests ändern nichts am Projekt: Papier-Durchläufe laufen in temporären Verzeichnissen gegen eine nachgestellte
Börse, der Rechenkern läuft auf künstlichen Kursen. Sie dokumentieren das heutige Verhalten, auch dort, wo es ein
Risiko ist. Wer das Verhalten später absichtlich ändert (z. B. eine Liquidationsprüfung einbaut), muss den
betreffenden Test bewusst anpassen.

Aufruf (aus swing-hybrid/):
    .venv/bin/python -B -m pytest -q -p no:cacheprovider reports/audit/evidence/RSK/test_rsk_risiko.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("NUMBA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "rsk_numba_cache"))   # nichts ins Repo schreiben

ROOT = Path(__file__).resolve().parents[4]          # swing-hybrid/
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import pytest

from hybrid import research as R, runner
from vorwaertstest import bot, kern

H = kern.STUNDE_MS
TAG = 24 * H
T0 = 1_800_000_000_000 - (1_800_000_000_000 % TAG) + 5 * 60_000        # 00:05 UTC eines Tages
ZEHN = ["C%d" % i for i in range(10)]
STILL = lambda *_: None


class Boerse:
    """Nachgestellte Börse mit einstellbarer Uhrzeit: je Coin Kurs jetzt und Schlusskurs vor 14 Tagen, tiefe Bücher, kein Funding."""
    key = secret = ""

    def __init__(self, kurse, alt):
        self.kurse, self.alt, self.jetzt, self.aufrufe = dict(kurse), dict(alt), T0, 0

    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        c = sym.removesuffix("USDT")
        if start_ms is not None:
            return [{"start": start_ms, "open": 0, "high": 0, "low": 0, "close": self.alt[c]}]
        letzte = self.jetzt - self.jetzt % H - H
        return [{"start": letzte, "open": 0, "high": 0, "low": 0, "close": self.kurse[c]},
                {"start": letzte + H, "open": 0, "high": 0, "low": 0, "close": self.kurse[c]}]

    def kontrakt(self, sym):
        return {"status": "Trading", "min_menge": 0.001, "schritt": 0.001, "tick": 0.01, "funding_minuten": 480}

    def ticker(self, sym):
        p = self.kurse[sym.removesuffix("USDT")]
        return {"geld": p - 0.01, "brief": p + 0.01, "letzter": p, "mark": p, "funding": 0.0, "umsatz24h": 1e6}

    def buch(self, sym, tiefe=25):
        p = self.kurse[sym.removesuffix("USDT")]
        return {"geld": [(p - 0.01, 1e9)], "brief": [(p + 0.01, 1e9)]}


def lauf(cfg, api, daten, jetzt, kurs=None, alt=None):
    if kurs is not None:
        api.kurse = {c: kurs for c in api.kurse}
    if alt is not None:
        api.alt = {c: alt for c in api.alt}
    api.jetzt = jetzt
    r = bot.schritt(cfg, api, daten, jetzt, melden=STILL)
    return r, json.loads((daten / "zustand.json").read_text())


def cfg_wie_test1(**mehr):
    c = bot.konfig(ROOT / "vorwaertstest" / "config_lauf.json")
    return {**c, "coins": ZEHN, **mehr}


# --------------------------------------------------------------- Ist-Konfiguration ----
def test_ist_konfiguration_der_beiden_papier_tests():
    """Beide Papier-Tests: Hebel 3 auf 5.000 $ (1.500 $ je Coin), Tagesverlust-Limit 100 % des Kapitals, also praktisch keins.
    Test 2 zusätzlich Stop 5 % / Ziel 15 %. Der von der Forschung als regelkonform ermittelte Hebel war 0,2 (config.json)."""
    c1 = bot.konfig(ROOT / "vorwaertstest" / "config_lauf.json")
    c2 = bot.konfig(ROOT / "vorwaertstest" / "config_lauf_tpsl.json")
    for c in (c1, c2):
        assert c["modus"] == "papier" and c["hebel"] == 3.0 and c["kapital_usd"] == 5000 and len(c["coins"]) == 10
        assert c["tagesverlust_limit"] == 1.0
        assert c["kapital_usd"] * c["hebel"] / len(c["coins"]) == 1500
    assert (c2["sl"], c2["tp"]) == (0.05, 0.15) and "sl" not in c1 and "tp" not in c1
    assert bot.konfig(ROOT / "vorwaertstest" / "config.json")["hebel"] == 0.2


def test_konfig_prueft_hebel_bis_5_aber_kein_verlustlimit(tmp_path):
    basis = json.loads((ROOT / "vorwaertstest" / "config_lauf.json").read_text())
    p = tmp_path / "c.json"
    p.write_text(json.dumps({**basis, "hebel": 5.0, "tagesverlust_limit": 99.0}))
    assert bot.konfig(p)["hebel"] == 5.0                       # Hebel 5 und ein sinnloses Limit werden angenommen
    p.write_text(json.dumps({**basis, "hebel": 5.01}))
    with pytest.raises(ValueError):
        bot.konfig(p)


# ----------------------------------------------- Papier-Bot: keine Liquidation, kein Margin-Call ----
def test_papier_bot_kennt_weder_liquidation_noch_margin_call_noch_konto_untergrenze(tmp_path):
    """Zehn Shorts zu je 1.500 $, Konto 5.000 $. Der Korb steigt über Nacht um 30 %, am nächsten Tag weiter auf +50 %.
    Eine Börse hätte spätestens bei rund +30 bis +33 % liquidiert. Der Papier-Bot hält alle Positionen, meldet nichts
    und führt das Konto ins Negative."""
    cfg, api = cfg_wie_test1(), Boerse({c: 100.0 for c in ZEHN}, {c: 110.0 for c in ZEHN})
    r, z = lauf(cfg, api, tmp_path, T0)
    assert r["orders"] == 10 and all(z["pos"][c] < 0 for c in ZEHN)
    stueck = dict(z["pos"])
    wert = sum(abs(q) * 100.0 for q in stueck.values())
    assert wert == pytest.approx(15000, rel=1e-3)                                  # Positionswert = 3 x Konto

    r, z = lauf(cfg, api, tmp_path, T0 + TAG, kurs=130.0, alt=140.0)               # +30 % gegen die Shorts, Signal bleibt Short
    konto = cfg["kapital_usd"] + r["vermoegen"]["netto_mit_rebate"]
    assert r["orders"] == 0 and z["pos"] == stueck and z["gesperrt_tag"] == ""
    assert 400 < konto < 520                                                        # Konto bei rund 10 % des Startkapitals
    assert konto / (wert * 1.3) < 0.03                                              # Margin-Quote unter 3 %
    assert not any(w for w in r["warnungen"])                                       # keine Warnung, kein Margin-Call

    r, z = lauf(cfg, api, tmp_path, T0 + TAG + 6 * H, kurs=150.0, alt=160.0)       # weiter auf +50 %
    konto = cfg["kapital_usd"] + r["vermoegen"]["netto_mit_rebate"]
    assert konto < -2400                                                            # Konto NEGATIV: -50 % des Startkapitals
    assert r["orders"] == 0 and z["pos"] == stueck and z["gesperrt_tag"] == "" and not r["warnungen"]
    st = bot.lesen(tmp_path / "stand.csv")
    assert float(st[-1]["netto_mit_rebate"]) < -7400 and int(st[-1]["short"]) == 10  # wird so ins Protokoll geschrieben


def test_tagesverlust_limit_100_prozent_greift_erst_nach_dem_totalverlust(tmp_path):
    """Mit tagesverlust_limit = 1.0 schließt der Bot erst, wenn an EINEM Tag das ganze Startkapital verloren ist."""
    cfg, api = cfg_wie_test1(), Boerse({c: 100.0 for c in ZEHN}, {c: 110.0 for c in ZEHN})
    lauf(cfg, api, tmp_path, T0)
    r, z = lauf(cfg, api, tmp_path, T0 + 6 * H, kurs=133.0, alt=140.0)             # -4.950 $ am selben Tag: noch keine Reaktion
    assert r["orders"] == 0 and z["gesperrt_tag"] == ""
    r, z = lauf(cfg, api, tmp_path, T0 + 12 * H, kurs=134.0, alt=140.0)            # -5.100 $: jetzt greift das Limit
    assert z["gesperrt_tag"] != "" and all(z["pos"][c] == 0 for c in ZEHN)
    assert cfg["kapital_usd"] + r["vermoegen"]["netto_mit_rebate"] < 0             # geschlossen wird mit negativem Konto


def test_verlust_ueber_nacht_zaehlt_fuer_kein_tageslimit(tmp_path):
    """Der Tagesanfang wird beim ersten Lauf des neuen Tages mit den DANN gültigen Kursen gesetzt. Ein Verlust zwischen dem
    letzten Lauf des alten und dem ersten Lauf des neuen Tages wird keinem Tag zugerechnet (hier mit Limit 3 %)."""
    cfg, api = cfg_wie_test1(tagesverlust_limit=0.03), Boerse({c: 100.0 for c in ZEHN}, {c: 110.0 for c in ZEHN})
    lauf(cfg, api, tmp_path, T0)
    r, z = lauf(cfg, api, tmp_path, T0 + TAG, kurs=120.0, alt=140.0)               # -3.000 $ = -60 % des Kapitals über Nacht
    assert z["gesperrt_tag"] == "" and r["orders"] == 0 and all(z["pos"][c] < 0 for c in ZEHN)


def test_positionswert_waechst_mit_dem_kurs_groesse_wird_nicht_nachgefuehrt(tmp_path):
    """Größe wird nur beim Einstieg festgelegt. Verdoppelt sich der Kurs einer Long-Position, ist der Positionswert das
    Sechsfache des Startkapitals statt des Dreifachen; der Bot reduziert nicht."""
    cfg, api = cfg_wie_test1(), Boerse({c: 100.0 for c in ZEHN}, {c: 90.0 for c in ZEHN})
    lauf(cfg, api, tmp_path, T0)
    r, z = lauf(cfg, api, tmp_path, T0 + H, kurs=200.0, alt=180.0)
    st = bot.lesen(tmp_path / "stand.csv")
    assert r["orders"] == 0 and float(st[-1]["einsatz"]) == pytest.approx(30000, rel=1e-3)
    assert float(st[-1]["einsatz"]) / cfg["kapital_usd"] == pytest.approx(6.0, rel=1e-3)      # Nennhebel laut Konfiguration: 3
    assert cfg["hebel"] == 3.0


# ------------------------------------------------------------- Test 2: Stop und Wiedereinstieg ----
def cfg_wie_test2():
    """Konfiguration von Test 2, auf einen Coin verkleinert: 500 $ Kontoanteil x Hebel 3 = 1.500 $ Positionswert wie im Test."""
    c = bot.konfig(ROOT / "vorwaertstest" / "config_lauf_tpsl.json")
    return {**c, "coins": ["AAA"], "kapital_usd": c["kapital_usd"] / len(c["coins"])}


def test_stop_wird_nur_beim_lauf_geprueft_und_zum_dann_gueltigen_kurs_ausgefuehrt(tmp_path):
    """Kein Stop liegt an der Börse. Springt der Kurs zwischen zwei Läufen um 20 % gegen die Position, wird der „5-%-Stop“
    mit rund 20 % Verlust ausgeführt (hier 300 $ statt 75 $ auf 1.500 $ Positionswert bei 500 $ Kontoanteil)."""
    cfg, api = cfg_wie_test2(), Boerse({"AAA": 100.0}, {"AAA": 110.0})
    lauf(cfg, api, tmp_path, T0)                                                    # Short zu 99,99
    r, z = lauf(cfg, api, tmp_path, T0 + 5 * 60_000, kurs=104.0, alt=110.0)        # -4 %: noch kein Stop
    assert r["orders"] == 0 and z["pos"]["AAA"] < 0
    r, z = lauf(cfg, api, tmp_path, T0 + 10 * 60_000, kurs=120.0, alt=130.0)       # Sprung auf -20 %
    pr = bot.lesen(tmp_path / "protokoll.csv")
    assert pr[-1]["grund"] == "stop" and float(pr[-1]["fuellkurs"]) == pytest.approx(120.01)
    assert z["pos"]["AAA"] == 0 and z["sperre"]["AAA"] == -1
    assert r["vermoegen"]["brutto"] == pytest.approx(-300, abs=2)                   # 20 % von 1.500 $, nicht 5 %


def test_nach_dem_stop_reicht_ein_hin_und_her_des_signals_fuer_den_wiedereinstieg(tmp_path):
    """Nach dem Stop wartet der Coin, bis das Signal dreht. Dreht es und dreht zurück (historisch folgt auf 30 % der Drehs
    binnen einer Stunde der nächste), steht dieselbe Richtung wie vor dem Stop wieder im Buch, jetzt mit neuem Einstiegskurs
    und neuem 5-%-Stop."""
    cfg, api = cfg_wie_test2(), Boerse({"AAA": 100.0}, {"AAA": 110.0})
    lauf(cfg, api, tmp_path, T0)
    _, z = lauf(cfg, api, tmp_path, T0 + H, kurs=106.0, alt=110.0)                 # Stop bei -6 %
    assert z["pos"]["AAA"] == 0 and z["sperre"]["AAA"] == -1
    r, z = lauf(cfg, api, tmp_path, T0 + 2 * H, kurs=106.0, alt=110.0)             # Signal weiter Short: bleibt draußen
    assert r["orders"] == 0 and z["pos"]["AAA"] == 0
    _, z = lauf(cfg, api, tmp_path, T0 + 3 * H, kurs=106.0, alt=105.0)             # Signal dreht auf Long: Einstieg Long
    assert z["pos"]["AAA"] > 0 and z["sperre"]["AAA"] == 0
    _, z = lauf(cfg, api, tmp_path, T0 + 4 * H, kurs=106.0, alt=107.0)             # Signal dreht zurück: wieder Short
    assert z["pos"]["AAA"] < 0 and z["einstieg"]["AAA"] == pytest.approx(105.99)
    assert z["orders"] == 5                                                         # 1 Einstieg, 1 Stop, 1 Long, 1 Schließen, 1 Short


def test_bei_fehlenden_marktdaten_wird_der_stop_nicht_geprueft(tmp_path):
    """Fällt die Abfrage für einen Coin aus (YubitFehler), wird er in diesem Lauf übersprungen: kein Stop, nur ein Hinweis."""
    from vorwaertstest.yubit import YubitFehler

    class Halb(Boerse):
        aus = set()

        def ticker(self, sym):
            if sym.removesuffix("USDT") in self.aus:
                raise YubitFehler("Zeitüberschreitung")
            return super().ticker(sym)

    cfg = {**cfg_wie_test2(), "coins": ["AAA", "BBB"], "kapital_usd": 1000}
    api = Halb({"AAA": 100.0, "BBB": 100.0}, {"AAA": 110.0, "BBB": 110.0})
    lauf(cfg, api, tmp_path, T0)
    api.aus = {"AAA"}
    r, z = lauf(cfg, api, tmp_path, T0 + H, kurs=120.0, alt=130.0)                 # beide -20 %; AAA ohne Daten
    assert z["pos"]["BBB"] == 0 and z["pos"]["AAA"] < 0                             # BBB gestoppt, AAA läuft ungeprüft weiter
    assert any("AAA" in w or "Zeitüberschreitung" in w for w in r["warnungen"])


# ------------------------------------------------------------------ Rechenkern der Forschung ----
def kunstmarkt(kurse: np.ndarray, fund=None):
    """Markt aus Schlusskursen [N, T] auf dem 5-Minuten-Raster; Open = vorheriger Schluss."""
    n, t = kurse.shape
    o = np.concatenate([kurse[:, :1], kurse[:, :-1]], axis=1)
    idx = pd.date_range("2024-01-01", periods=t, freq="5min")
    tage = idx.normalize()
    return SimpleNamespace(index=idx, coins=["K%d" % i for i in range(n)], o=np.ascontiguousarray(o), h=np.maximum(o, kurse),
                           l=np.minimum(o, kurse), c=np.ascontiguousarray(kurse), atr=np.ones((n, t)),
                           fund=np.zeros((n, t)) if fund is None else fund, day=np.asarray((tage - tage[0]).days, dtype=np.int64),
                           days=pd.DatetimeIndex(tage.unique()))


def kandidat_lauf(m, w, hebel):
    return R.lauf(m, np.ascontiguousarray(w, dtype=np.float64), hebel=hebel, taker=True, slip=np.full(len(m.coins), 0.0002), day_limit=9.0)


def test_rechenkern_hebel_ist_linear_und_konto_kann_negativ_werden():
    """Der Backtest kennt keine Liquidation: Zwei Shorts, die Kurse vervierfachen sich. Bei Hebel 3 ist das Konto längst
    negativ, die Positionen laufen weiter. Hebel 3 ist exakt das Dreifache von Hebel 1 (keine Rückkopplung des Kontostands)."""
    t = 3000
    kurse = np.vstack([100.0 * np.linspace(1.0, 4.0, t), 50.0 * np.linspace(1.0, 4.0, t)])
    m = kunstmarkt(kurse)
    w = -np.ones((2, t))
    l1, l3 = kandidat_lauf(m, w, 1.0), kandidat_lauf(m, w, 3.0)
    e1, e3 = l1.equity(runner.MIT), l3.equity(runner.MIT)
    assert np.allclose(e3, 3.0 * e1, atol=1e-12)
    assert e1[-1] == pytest.approx(-3.0, abs=0.02)                 # zwei Shorts zu je 0,5: Verlust 3 x Startkapital bei Hebel 1
    assert (1.0 + e3).min() < -7.9                                 # Konto bei Hebel 3: unter -790 %
    assert len(l3.trades) == 2 and (l3.trades["art"] == "sperre_ende").all()   # erst die Schlussabrechnung schließt
    assert int(l3.st[4]) == 0 and int(l3.st[5]) == 0               # kein Tageslimit, kein Stop ausgelöst


def test_rechenkern_groesse_fest_beim_einstieg_gewinner_wachsen():
    """Größe = S / Einstiegskurs Stück, danach unverändert: Steigt der Kurs einer Long-Position auf das Dreifache, ist ihr
    Wert das Dreifache der Standardgröße. Fällt der Kurs danach um 20 %, kostet das 60 % der Standardgröße, nicht 20 %."""
    t = 2000
    kurs = np.concatenate([np.linspace(100.0, 300.0, t - 100), np.linspace(300.0, 240.0, 100)])[None, :]
    m = kunstmarkt(kurs)
    l = kandidat_lauf(m, np.ones((1, t)), 1.0)                     # ein Coin, S = 1 (ganzes Startkapital), Einstieg bei 100
    e = l.eq_gross
    assert e[t - 101] == pytest.approx(2.0, abs=0.01)              # am Hoch: +200 % des Startkapitals, Positionswert 3 x S
    assert e[t - 101] - e[t - 2] == pytest.approx(0.6, abs=0.01)   # Rückgang um 20 % kostet 0,6 x Startkapital
    assert len(l.trades) == 1                                      # die ganze Zeit eine einzige Position, nie verkleinert


def test_unabhaengiger_nachbau_stimmt_mit_dem_rechenkern_ueberein():
    """Eigene, schlichte Nachrechnung von Einstieg, Dreh, Gebühr (Taker mit 85 % Rebate), Slippage und Funding gegen
    engine2.simulate_target im Taker-Modus, auf Zufallskursen mit zufälligen Richtungswechseln zur vollen Stunde."""
    rng = np.random.default_rng(7)
    n, t = 3, 6000
    kurse = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.003, (n, t)), axis=1))
    fund = np.zeros((n, t)); fund[:, ::96] = rng.normal(0.0001, 0.0003, (n, len(range(0, t, 96))))
    m = kunstmarkt(kurse, fund)
    w = np.repeat(rng.choice([-1.0, 1.0], (n, t // 12)), 12, axis=1)
    w[:, :12] = 0.0
    l = kandidat_lauf(m, w, 1.0)
    slip, fee, S = 0.0002, runner.TAKER * (1 - runner.MIT.rebate), 1.0 / n
    gesamt = np.zeros(t)
    for j in range(n):
        q = cash = vol = f = 0.0
        held = 0.0
        for i in range(t):
            ende = i == t - 1
            if ende and q != 0.0:
                px = m.o[j, i] * (1.0 - np.sign(q) * slip)
                cash += q * px; vol += abs(q) * px; q = 0.0
            if m.fund[j, i] != 0.0 and q != 0.0:
                f -= q * m.o[j, i] * m.fund[j, i]
            if not ende and i > 0 and w[j, i] != held:
                dq = w[j, i] * S / m.o[j, i] - q
                px = m.o[j, i] * (1.0 + np.sign(dq) * slip)
                cash -= dq * px; vol += abs(dq) * px; q += dq; held = w[j, i]
            gesamt[i] += cash + q * m.c[j, i] - fee * vol + f
    assert np.allclose(gesamt, l.equity(runner.MIT), atol=1e-10)
    assert fee == pytest.approx(0.00012)                            # 0,08 % Taker x (1 - 0,85)
