"""Tests zu E26 aus der unabhängigen Gegenprüfung (21.11.2026), angepasst an die Korrekturen danach (DIA ohne Kontrakt,
CL und BZ keine Aktien, WTI ab 22.04.2020, Zeilen für alle Krypto-Kontrakte). Nur künstliche Kurse oder ersetzte Lader."""
import csv
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(os.environ.get("E26_ROOT", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(ROOT / "forschung"))
pytest.importorskip("numba")
from experimente import e26_jeder_markt as X  # noqa: E402


def kurse(von, bis, seed, drift=0.0):
    idx = pd.bdate_range(von, bis)
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.normal(drift, 0.012, len(idx))))
    return pd.DataFrame({"open": np.concatenate([[100.0], c[:-1]]) * (1 + rng.normal(0, 0.003, len(idx))), "close": c}, index=idx)


def steigend(von, bis="2026-10-16"):
    idx = pd.bdate_range(von, bis)
    c = 100 * np.exp(0.0005 * np.arange(len(idx)))
    return pd.DataFrame({"open": c * 0.999, "close": c}, index=idx)


# ------------------------------------------------------------------------------------------------- Zeitablauf
@pytest.mark.parametrize("stress", [False, True])
def test_spaetere_kurse_aendern_fruehere_tage_nicht(stress):
    d = kurse("2019-06-03", "2026-10-16", 11)
    basis = X.markt_reihe(d, 0.0003, stress)
    rng = np.random.default_rng(5)
    for k in (40, 600, 1500, len(d) - 2):
        e = d.copy()
        e.iloc[k:] = e.iloc[k:].to_numpy() * np.exp(rng.normal(0, 0.05, (len(d) - k, 2)))
        neu = X.markt_reihe(e, 0.0003, stress)
        vor = basis.index < d.index[k]
        assert np.array_equal(basis[vor].to_numpy(), neu[vor].to_numpy())                     # kein Blick voraus
        assert not np.array_equal(basis[~vor].to_numpy(), neu[~vor].to_numpy())


def test_kuerzere_daten_aendern_nur_den_letzten_tag():
    d = kurse("2019-06-03", "2026-10-16", 12)
    basis = X.markt_reihe(d, 0.0003)
    for k in (300, 900, 1700):
        kurz = X.markt_reihe(d.iloc[:k], 0.0003)
        assert kurz.index[0] == d.index[0] and kurz.index[-1] == d.index[k - 1]
        vor = kurz.index < d.index[k - 1]
        assert np.array_equal(kurz[vor].to_numpy(), basis[basis.index < d.index[k - 1]].to_numpy())


def test_ein_lauf_ueber_alles_und_schluss_nur_am_datenende(monkeypatch):
    rufe, echt = [], X.T.lauf_markt

    def spion(d, kal, S, slip, geb, fund=0.0, tage=14):
        t = echt(d, kal, S, slip, geb, fund, tage)
        rufe.append((kal, (S, slip, geb, fund, tage), t))
        return t
    monkeypatch.setattr(X.T, "lauf_markt", spion)
    d = steigend("2016-01-04")
    idx, o, c = d.index, d["open"].to_numpy(), d["close"].to_numpy()
    netto, stress = X.markt_reihe(d, 0.0002), X.markt_reihe(d, 0.0002, stress=True)
    assert len(rufe) == 2                                                                       # je Rechnung genau ein Lauf über die ganze Historie
    for (kal, arg, t), soll in zip(rufe, ((1.0, 0.0002, 0.0008, 0.0, 14), (1.0, 0.0004, 0.0016, 0.10, 14))):
        assert kal[0] == idx[0] and kal[-1] == idx[-1] and arg == soll
        handel = t.index[t["umsatz"].to_numpy() > 0]
        assert list(handel) == [pd.Timestamp("2016-01-19"), idx[-1]]                            # ein Einstieg, ein Schluss am Datenende, nichts an Zeitraumgrenzen
    e = int(idx.get_loc(pd.Timestamp("2016-01-19")))
    pos = 1.0 / (o[e] * 1.0002)
    aus = pos * o[-1] * (1 - 0.0002)
    assert float(netto.sum()) == pytest.approx(aus - 1.0 - 0.15 * 0.0008 * (1.0 + aus), abs=1e-12)
    pos_s = 1.0 / (o[e] * 1.0004)
    abstand = np.diff(idx.to_numpy(), prepend=idx.to_numpy()[:1]).astype("timedelta64[D]").astype(float)
    for p in ("T", "V1", "V2"):                                                                 # Zeiträume ohne jede Order: nur Kursänderung, keine Kosten
        im = np.nonzero((idx >= X.PERIODEN[p][0]) & (idx <= X.PERIODEN[p][1]))[0]
        assert float(X.periode(netto, p).sum()) == pytest.approx(pos * (c[im[-1]] - c[im[0] - 1]), abs=1e-12)
        fund = 0.10 / 365.0 * pos_s * float((c[im - 1] * abstand[im]).sum())                    # Stress-Funding: Vortagesschluss, je Kalendertag
        assert float(X.periode(stress, p).sum()) == pytest.approx(pos_s * (c[im[-1]] - c[im[0] - 1]) - fund, abs=1e-12)


@pytest.mark.parametrize("von, erster", [("2016-01-04", "2016-01-19"), ("2020-01-02", "2020-01-17"), ("2023-05-01", "2023-05-16")])
def test_erster_handel_nach_14_kalendertagen(von, erster):
    d = steigend(von)
    netto = X.markt_reihe(d, 0.0002)
    assert netto.index[0] == pd.Timestamp(von) and netto[netto != 0].index[0] == pd.Timestamp(erster)
    z = X.zeile(netto, X.markt_reihe(d, 0.0002, stress=True), d.index)
    if von == "2023-05-01":                                                                     # Beginn mitten in T: T hat 45 Börsentage und zählt nicht
        assert z["je_zeitraum_pct"]["T"] is None and z["zeitraeume"] == 3
        assert z["summe_pct"] == pytest.approx(float(netto[netto.index >= "2023-07-01"].sum() * 100), abs=0.006)
    else:
        assert z["zeitraeume"] == 5 and z["je_zeitraum_pct"]["P0"] is not None


# ------------------------------------------------------------------------------------------ Zeiträume, Kriterium
def test_genau_60_boersentage_zaehlen_59_nicht():
    for n, zaehlt in ((60, True), (59, False)):
        idx = pd.bdate_range(end="2023-06-30", periods=n).union(pd.bdate_range("2023-07-03", "2024-12-31"))
        x = pd.Series(0.0, index=pd.date_range(idx[0], idx[-1]))
        x[idx] = 0.001
        s = x.copy()
        s[idx[:n]] += 1.0                                                                       # Stress-Reihe weicht nur in T ab
        z = X.zeile(x, s, idx)
        assert (z["je_zeitraum_pct"]["T"] is not None) == zaehlt and z["zeitraeume"] == (3 if zaehlt else 2)
        assert z["stress_pct"] == pytest.approx(z["summe_pct"] + (100.0 * n if zaehlt else 0.0), abs=0.011)   # auch der Stress nur über gezählte Zeiträume
        assert z["summe_pct"] == pytest.approx(0.1 * (len(idx) - (0 if zaehlt else 59)), abs=0.006)   # nicht gezählter Zeitraum fehlt auch in der Summe


def test_grenzen_der_zeitraeume():
    kal = pd.date_range("2021-08-01", "2025-04-30")
    x = pd.Series(1.0, index=kal)
    soll = {"P0": ("2021-08-01", "2021-08-14"), "T": ("2021-08-15", "2023-06-30"), "V1": ("2023-07-01", "2024-06-30"),
            "V2": ("2024-07-01", "2025-03-31"), "P3": ("2025-04-01", "2025-04-30")}
    teile = {p: X.periode(x, p) for p in X.PERIODEN}
    assert {p: (str(t.index[0].date()), str(t.index[-1].date())) for p, t in teile.items()} == soll
    assert sum(len(t) for t in teile.values()) == len(kal)                                      # lückenlos und ohne Überschneidung


def test_vier_zeitraeume_reichen_und_kennzahlen_nach_definition():
    idx = pd.bdate_range("2021-08-16", "2026-10-16")
    rng = np.random.default_rng(8)
    x = pd.Series(0.0, index=pd.date_range(idx[0], idx[-1]))
    x[idx] = rng.normal(0.002, 0.01, len(idx))
    z = X.zeile(x, x - 0.0001, idx)
    assert z["zeitraeume"] == 4 and z["je_zeitraum_pct"]["P0"] is None and z["auffaellig"]
    xt, xa = x[idx].to_numpy(), x.to_numpy()
    assert z["t_wert"] == round(float(xt.mean() / xt.std(ddof=1) * np.sqrt(len(xt))), 2)          # t-Wert: nur Börsentage
    assert z["t_wert"] != round(float(xa.mean() / xa.std(ddof=1) * np.sqrt(len(xa))), 2)
    assert z["sharpe"] == round(float(xa.mean() / xa.std(ddof=1) * np.sqrt(365)), 3)            # Sharpe-Zahl: Kalendertage, Jahr = 365
    assert z["stress_pct"] == round(float((x - 0.0001).sum() * 100), 2)


@pytest.mark.parametrize("t_soll, auffaellig", [(1.8, False), (2.2, True)])
def test_schwelle_t_wert(t_soll, auffaellig):
    idx = pd.bdate_range("2020-01-02", "2026-10-16")
    a = 0.01
    x = pd.Series(0.0, index=pd.date_range(idx[0], idx[-1]))
    x[idx] = t_soll * a / np.sqrt(len(idx)) + a * (-1.0) ** np.arange(len(idx))
    z = X.zeile(x, x, idx)
    assert z["zeitraeume"] == 5 and z["alle_zeitraeume_positiv"] and abs(z["t_wert"] - t_soll) < 0.05
    assert z["auffaellig"] == auffaellig


def test_null_ist_nicht_positiv():
    idx = pd.bdate_range("2020-01-02", "2026-10-16")
    x = pd.Series(0.0, index=pd.date_range(idx[0], idx[-1]))
    x[idx] = 0.001 + 0.0001 * (-1.0) ** np.arange(len(idx))
    assert X.zeile(x, x, idx)["auffaellig"]
    x[(x.index >= "2024-07-01") & (x.index <= "2025-03-31")] = 0.0                              # ein Zeitraum genau null
    z = X.zeile(x, x, idx)
    assert z["je_zeitraum_pct"]["V2"] == 0.0 and not z["alle_zeitraeume_positiv"] and not z["auffaellig"]


# ------------------------------------------------------------------------------------------------ Daten, Kosten
def test_labor_etf_doppelte_zeilen_reihenfolge_und_spalten(tmp_path, monkeypatch):
    a = tmp_path / "buy_and_hold__ABC__1D__aaaaaaaaaa/artifacts"
    a.mkdir(parents=True)
    (a / "ohlcv_ABC.csv").write_text("trade_date,open,high,low,close,volume\n2016-01-06,3,9,9,30,1\n2016-01-04,1,9,9,10,1\n2016-01-05,2,9,9,20,1\n2016-01-05,7,9,9,70,1\n")
    b = tmp_path / "buy_and_hold__ABC__1D__bbbbbbbbbb/artifacts"
    b.mkdir(parents=True)
    (b / "ohlcv_ABC.csv").write_text("trade_date,open,high,low,close,volume\n2016-01-04,5,9,9,50,1\n")
    monkeypatch.setattr(X, "LABOR", tmp_path)
    d = X.labor_etf("ABC")
    assert [str(t.date()) for t in d.index] == ["2016-01-04", "2016-01-05", "2016-01-06"]
    assert d["open"].tolist() == [1.0, 2.0, 3.0] and d["close"].tolist() == [10.0, 20.0, 30.0]


def test_kosten_zuordnung_je_markt():
    k = X.kosten()
    k14 = json.loads((ROOT / "reports/runde14_kosten.json").read_text())
    stich = X.X25.spannen()
    info = json.loads((ROOT / "reports/runde17_aktien.json").read_text())
    for n in ["SPY", "QQQ", "IWM"] + X.RUNDE14:
        assert k[n] == max(0.00005, k14[n]["spanne_bp"] / 1e4)
    assert k["XLE"] == stich["XLEUSDT"] / 1e4
    median = float(np.median([k14[n]["spanne_bp"] for n in ("SPY", "QQQ", "IWM", "EWJ", "EWY")] + [stich["XLEUSDT"]])) / 1e4
    for n in ("DIA", "EEM", "EFA", "XLF", "XLK", "XLV"):                                        # ohne Yubit-Kontrakt (DIAUSDT ist ein Krypto-Token)
        assert k[n] == pytest.approx(median) and k[n] != stich["DIAUSDT"] / 1e4
    assert stich["DIAUSDT"] > 5 and stich["XLEUSDT"] < 5
    assert k14["XAU"]["spanne_bp"] < 0.5 and k["XAU"] == 0.00005                                # Boden 0,5 bp greift
    aktien = {a: v for a, v in info.items() if v["ok"] and a not in ("CL", "BZ")}
    assert len(aktien) == 132 and "AKTIE:CL" not in k and "AKTIE:BZ" not in k                   # CL und BZ sind bei Yubit die Öl-Kontrakte
    for a, v in aktien.items():
        assert k["AKTIE:" + a] == max(0.00005, v["spanne_bp"] / 1e4)
    assert set(k) == set(X.LABOR_ETF) | set(X.RUNDE14) | {"AKTIE:" + a for a in aktien}
    assert len(X.LABOR_ETF) == 10 and len(X.RUNDE14) == 11 and not set(X.LABOR_ETF) & set(X.RUNDE14)
    assert sorted(X.RUNDE14) == sorted(["EWJ", "EWY", "XAU", "XAG", "XPT", "XPD", "COPPER", "CL", "BZ", "NATGAS", "TBT"])


@pytest.mark.skipif(not (ROOT / "data/candles/aktien_1d").exists() or not X.LABOR.exists(), reason="Kursdaten fehlen")
def test_marktliste_vollstaendig_und_ohne_verwechslung():
    m, k = X.maerkte(), X.kosten()
    assert pd.Series([g for g, _, _ in m.values()]).value_counts().to_dict() == {"aktie": 132, "runde14": 11, "labor_etf": 10}
    assert set(m) == set(k) and len({name for _, name, _ in m.values()}) == len(m)              # die CSV nennt nur den Anzeigenamen
    for n in ("CL", "BZ"):                                                                      # nur als Öl, nicht als Aktie
        assert m[n][0] == "runde14" and "AKTIE:" + n not in m
    for n in X.LABOR_ETF:
        assert m[n][2].index[0] == pd.Timestamp("2016-01-04") and m[n][2].index[-1] == pd.Timestamp("2026-10-16")
    for n in X.RUNDE14:
        assert m[n][2].index[0] == (pd.Timestamp("2020-04-22") if n == "CL" else pd.Timestamp("2020-01-02"))   # WTI erst nach den negativen Kursen
    for _, _, d in m.values():
        assert list(d.columns) == ["open", "close"] and len(d) >= 30 and d.notna().all().all() and d.index.is_unique and d.index.is_monotonic_increasing
        assert (d > 0).all().all()


def test_gruppen_korb_je_zeitraum():
    a = pd.Series(0.01, index=pd.date_range("2021-08-10", "2021-08-19"))
    b = pd.Series(0.03, index=pd.date_range("2021-08-15", "2021-08-24"))
    zeilen = {"A": {"gruppe": "aktie"}, "B": {"gruppe": "aktie"}, "C": {"gruppe": "runde14"}, "D": {"gruppe": "labor_etf"}}
    g = X.gruppen_koerbe(zeilen, {"A": a, "B": b, "C": b, "D": a})
    assert "aktie" not in X.gruppen_koerbe({"C": {"gruppe": "runde14"}}, {"C": b})                # eine Gruppe ohne Markt fehlt einfach
    assert g["aktie"]["maerkte"] == 2 and g["runde14"]["maerkte"] == 1 and g["labor_etf"]["maerkte"] == 1
    assert g["aktie"]["je_zeitraum_pct"] == {"P0": 5.0, "T": 25.0, "V1": 0.0, "V2": 0.0, "P3": 0.0} and g["aktie"]["summe_pct"] == 30.0
    assert g["runde14"]["je_zeitraum_pct"]["T"] == 30.0 and g["labor_etf"]["je_zeitraum_pct"]["P0"] == 5.0


# ------------------------------------------------------------------------------------------------------ Krypto
def test_krypto_je_kontrakt_mit_ersetzten_ladern(monkeypatch):
    kal = pd.date_range("2021-07-01", "2024-06-30")
    n = len(kal)

    def reihe(start, g, w=0.02):
        c = np.full(n, np.nan)
        i0 = int(kal.get_loc(pd.Timestamp(start)))
        i = np.arange(n - i0)
        c[i0:] = 100 * np.exp(g * i + w * np.sin(i))
        return c

    def dreieck():
        i = np.arange(n) % 28
        return 100.0 + np.where(i < 14, i, 28 - i)
    cs = {"AAAUSDT": reihe("2021-07-01", 0.004), "BBBUSDT": reihe("2021-07-01", -0.004), "CCCUSDT": dreieck(), "DDDUSDT": reihe("2023-03-01", 0.004),
          "EEEUSDT": reihe("2023-03-05", 0.004), "FFFUSDT": reihe("2024-04-15", 0.004)}
    slip = {"AAAUSDT": 2.0, "BBBUSDT": 2.0, "CCCUSDT": 2.0, "DDDUSDT": 10.0, "EEEUSDT": 2.0, "FFFUSDT": 2.0, "TTTUSDT": 2.0, "SPAETUSDT": 2.0}
    inv = pd.DataFrame({"symbol": list(cs) + ["TTTUSDT", "SPAETUSDT"],
                        "erster_tag": pd.to_datetime(["2021-07-01", "2021-07-01", "2021-07-01", "2023-03-01", "2023-03-05", "2024-04-15", "2023-01-01", "2024-07-01"]),
                        "tradfi": [False] * 6 + [True, False]})

    def laden(syms, bis):
        assert bis == pd.Timestamp("2024-06-30") and list(syms) == list(cs)                    # nichts nach V1, keine Aktien-Kontrakte, nichts ab 07/2024
        c = np.array([cs[s] for s in syms])
        o = np.concatenate([c[:, :1], c[:, :-1]], axis=1)
        o = np.where(np.isfinite(o), o, c)
        fr = np.where(np.isfinite(c), 0.0, np.nan)
        fr[0] = np.where(np.isfinite(c[0]), 0.0001, np.nan)
        return kal, o, c, np.where(np.isfinite(c), 1e6, np.nan), fr
    monkeypatch.setattr(X.X25, "symbole", lambda: inv)
    monkeypatch.setattr(X.X25, "laden", laden)
    monkeypatch.setattr(X.X25, "spannen", lambda: slip)
    kr = X.krypto()
    assert set(kr) == set(cs) and kr["FFFUSDT"] == {"zu_kurz": True, "je_zeitraum_pct": {"T": None, "V1": None}}   # FFF: nie 60 Tage dabei -> Zeile mit Vermerk
    assert not any(kr[s]["zu_kurz"] for s in cs if s != "FFFUSDT")
    tT, tV = kal.get_loc(pd.Timestamp("2021-08-15")), kal.get_loc(pd.Timestamp("2023-07-01"))
    c = cs["AAAUSDT"]                                                                           # long ab Tag 15 (Einstieg zur Eröffnung = Schluss von Tag 14), zahlt 0,01 % Funding je Tag
    soll_T = (c[tV - 1] - c[tT - 1]) / c[14] - 0.0001 * (tV - tT)
    soll_V = (c[-1] - c[tV - 1]) / c[14] - 0.0001 * (n - tV)
    assert kr["AAAUSDT"]["je_zeitraum_pct"] == {"T": round(soll_T * 100, 2), "V1": round(soll_V * 100, 2)}
    assert kr["AAAUSDT"]["summe_pct"] == pytest.approx((soll_T + soll_V) * 100, abs=0.006) and kr["AAAUSDT"]["beide_positiv"] and kr["AAAUSDT"]["auffaellig"]
    assert kr["BBBUSDT"]["beide_positiv"] and kr["BBBUSDT"]["je_zeitraum_pct"]["V1"] > 0        # fallender Kurs: short verdient
    assert kr["CCCUSDT"]["je_zeitraum_pct"]["T"] < 0 and not kr["CCCUSDT"]["beide_positiv"] and not kr["CCCUSDT"]["auffaellig"]
    d, ab = cs["DDDUSDT"], int(kal.get_loc(pd.Timestamp("2023-04-30")))                         # 60 Tage nach dem 01.03.2023; 62 Tage in T
    soll = (d[tV - 1] - d[ab - 1]) / d[ab - 1] - (10.0 + 1.2) / 1e4                             # eine Order im Zeitraum: Spanne + Gebühr mit Rebate
    assert kr["DDDUSDT"]["je_zeitraum_pct"]["T"] == round(soll * 100, 2) and kr["DDDUSDT"]["beide_positiv"]
    assert round(kr["DDDUSDT"]["summe_pct"] - kr["DDDUSDT"]["stress_pct"], 2) == 0.10           # Krypto-Stress wie E25: nur die Slippage doppelt
    x = np.diff(d[ab - 1:]) / d[ab - 1]
    x[0] -= (10.0 + 1.2) / 1e4
    assert kr["DDDUSDT"]["t_wert"] == round(float(x.mean() / x.std(ddof=1) * np.sqrt(len(x))), 2)   # t-Wert: Tage ab dem ersten Teilnahmetag
    e = kr["EEEUSDT"]                                                                           # 58 Tage in T: T zählt nicht, Kontrakt nie auffällig
    assert e["je_zeitraum_pct"]["T"] is None and e["je_zeitraum_pct"]["V1"] > 0 and e["t_wert"] >= 2 and not e["beide_positiv"] and not e["auffaellig"]


def test_krypto_ohne_t_wert_nicht_auffaellig(monkeypatch):
    kal = pd.date_range("2021-07-01", "2024-06-30")
    n = len(kal)
    c = (100.0 + 0.01 * np.arange(n))[None, :]                                                 # steigt langsam: immer long, etwa 0,01 % je Tag
    fr = (0.01 * (-1.0) ** np.arange(n))[None, :]                                               # Funding abwechselnd +1 % und −1 %: viel Streuung, kein Ertrag
    inv = pd.DataFrame({"symbol": ["GGGUSDT"], "erster_tag": pd.to_datetime(["2021-07-01"]), "tradfi": [False]})
    monkeypatch.setattr(X.X25, "symbole", lambda: inv)
    monkeypatch.setattr(X.X25, "laden", lambda syms, bis: (kal, np.concatenate([c[:, :1], c[:, :-1]], axis=1), c, np.full((1, n), 1e6), fr))
    monkeypatch.setattr(X.X25, "spannen", lambda: {"GGGUSDT": 2.0})
    g = X.krypto()["GGGUSDT"]
    assert g["je_zeitraum_pct"]["T"] > 0 and g["je_zeitraum_pct"]["V1"] > 0 and g["beide_positiv"]
    assert 0 < g["t_wert"] < 2 and not g["auffaellig"]


# ---------------------------------------------------------------------------------------------------- Zählung
def test_hauptlauf_zaehlung_und_csv(tmp_path, monkeypatch):
    def z(g, je, summe, auff=False):
        gueltig = [v for v in je.values() if v is not None]
        return {"gruppe": g, "name": "N" + str(summe), "von": "2020-01-02", "bis": "2026-10-23", "slippage_bp": 1.0, "je_zeitraum_pct": je, "zeitraeume": len(gueltig),
                "summe_pct": summe, "stress_pct": summe - 1.0, "sharpe": 0.1, "t_wert": 0.5, "alle_zeitraeume_positiv": bool(gueltig) and all(v > 0 for v in gueltig), "auffaellig": auff}
    zeilen = {"A": z("labor_etf", {"P0": 1.0, "T": 1.0, "V1": 1.0, "V2": 1.0, "P3": 1.0}, 5.0, True),
              "B": z("aktie", {"P0": None, "T": 1.0, "V1": 1.0, "V2": 1.0, "P3": 1.0}, 4.0),
              "C": z("aktie", {"P0": None, "T": None, "V1": 1.0, "V2": 1.0, "P3": 1.0}, 3.0),      # drei Zeiträume: zählt nicht bei "alle positiv"
              "D": z("runde14", {"P0": 1.0, "T": -9.0, "V1": 1.0, "V2": 1.0, "P3": 1.0}, -5.0),
              "E": {"gruppe": "aktie", "name": "E", "ohne_daten": True}}
    reihen = {k: pd.Series(0.001, index=pd.date_range("2020-01-02", "2020-03-01")) for k in "ABCD"}

    def kz(t, v, beide, auff, eigen=False):
        return {"zu_kurz": False, "je_zeitraum_pct": {"T": t, "V1": v}, "summe_pct": 3.0, "stress_pct": 2.5, "t_wert": 2.5, "beide_positiv": beide,
                "auffaellig": auff, "eigenstaendig_auffaellig": eigen}
    kr = {"XUSDT": kz(1.0, 2.0, True, True), "YUSDT": kz(None, 2.0, False, False), "WUSDT": kz(-1.0, 2.0, False, False),
          "KUSDT": {"zu_kurz": True, "je_zeitraum_pct": {"T": None, "V1": None}}}
    neu = {"N1USDT": {"gruppe": "krypto_neu", "zu_kurz": False, "von": "2025-01-01", "tage": 300, "summe_pct": 5.0, "t_wert": 0.3, "groesster_tag_pct": 9.0},
           "N2USDT": {"gruppe": "kontrakt_aktie_index_rohstoff", "zu_kurz": False, "von": "2026-05-01", "tage": 100, "summe_pct": -2.0, "t_wert": -0.4, "groesster_tag_pct": 3.0},
           "N3USDT": {"gruppe": "kontrakt_aktie_index_rohstoff", "zu_kurz": True, "tage": 0}}
    monkeypatch.setattr(X, "nicht_krypto", lambda: ({k: v for k, v in zeilen.items() if k != "E"}, reihen))
    monkeypatch.setattr(X, "krypto", lambda: kr)
    monkeypatch.setattr(X, "neue_kontrakte", lambda: neu)
    monkeypatch.setattr(X, "ohne_kursdaten", lambda: ["OHNEUSDT"])
    monkeypatch.setattr(X, "ERGEBNIS", tmp_path / "e26.json")
    out = X.hauptlauf()
    assert out["zaehlung"] == {"nicht_krypto_maerkte": 4, "mit_mindestens_vier_zeitraeumen": 3, "davon_alle_zeitraeume_positiv": 2,
                               "auffaellig": ["A"], "summe_positiv": 3, "krypto_kontrakte": 4, "krypto_mit_zeile": 3, "krypto_mit_T_und_V1": 2,
                               "krypto_beide_positiv": 1, "krypto_auffaellig": ["XUSDT"], "krypto_eigenstaendig_auffaellig": [],
                               "neue_kontrakte": 3, "neue_kontrakte_mit_60_tagen": 2,
                               "neue_kontrakte_im_plus": {"krypto_neu": [1, 1], "kontrakt_aktie_index_rohstoff": [0, 1]}, "yubit_symbole_ohne_kursdaten": 1}
    assert json.loads((tmp_path / "e26.json").read_text())["zaehlung"] == out["zaehlung"] and set(out["gruppen"]) == {"labor_etf", "runde14", "aktie"}
    with open(tmp_path / "e26.csv", newline="") as f:
        rows = list(csv.reader(f))
    assert len(rows) == 1 + 4 + 4 + 3 and all(len(r) == 14 for r in rows) and rows[0][4:9] == ["P0", "T", "V1", "V2", "P3"]
    assert rows[5][:2] == ["XUSDT", "krypto"] and rows[5][5:7] == ["1.0", "2.0"] and rows[5][9:11] == ["3.0", "2.5"] and rows[5][12:] == ["2.5", "True"]
    assert rows[8][0] == "KUSDT" and rows[8][-1] == "zu kurz" and rows[9][-1] == "nur Bericht" and rows[11][-1] == "zu kurz"
