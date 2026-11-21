"""E24: bessere Einstiege und ein breiterer Pool (H21 bis H23).

Festlegung: forschung/protokoll.md, Abschnitt 45. Teil A (Krypto, Ausdehnung des Trends) nutzt den geprüften Rechenkern
von E23 unverändert; Teil B (Aktien) und Teil C (QQQ nach dem Bitcoin-Trend) rechnen auf Tageskursen wie Runde 14.

  .venv/bin/python -I forschung/experimente/e24_einstieg_und_pool.py        # T und V1 (nichts danach wird geladen)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

F = Path(__file__).resolve().parents[1]
ROOT = F.parent
sys.path.insert(0, str(F))
sys.path.insert(0, str(ROOT / "src"))
from experimente import e23_marktstruktur as E  # noqa: E402
from fabrik import daten as D  # noqa: E402
from hybrid import tagestrend as T  # noqa: E402

ZMAX, ZMIN = (1.0, 1.5, 2.0), (0.25, 0.5, 1.0)
Z_STUFEN = ((0.0, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, 2.0), (2.0, np.inf))
ALTER_STUFEN = ((0, 24), (24, 72), (72, 168), (168, 336), (336, 10 ** 9))
TAKER, REBATE = 0.0008, 0.85
T_START, V1_ENDE = pd.Timestamp("2021-08-15"), pd.Timestamp("2024-06-30")
KAL = pd.date_range(T_START, V1_ENDE, freq="D")
ERGEBNIS = F / "ergebnisse/e24_einstieg_und_pool.json"


# ------------------------------------------------------------------------------------------------ Teil A (Krypto)
def ausdehnung(c: np.ndarray) -> np.ndarray:
    """z je Stundenkerze t: |ln(C_t / C_{t−336})| / (σ_t × √336); σ_t aus den 720 Stunden-Renditen bis t. Sonst nan."""
    ch = c[11::12]
    lr = np.diff(np.log(ch), prepend=np.nan)                         # lr[u] = ln(C_u / C_{u−1}), lr[0] unbestimmt
    sig = pd.Series(lr).rolling(720).std(ddof=1).to_numpy()          # Fenster u = t−719 … t, erst ab t = 720 vollständig
    z = np.full(len(ch), np.nan)
    z[E.RUECK:] = np.abs(np.log(ch[E.RUECK:] / ch[:-E.RUECK]))
    with np.errstate(divide="ignore", invalid="ignore"):
        z = z / (sig * np.sqrt(E.RUECK))
    z[~np.isfinite(z)] = np.nan
    return z


def alter_stunden(d: np.ndarray) -> np.ndarray:
    """Stunden seit dem letzten Wechsel von d (auf den jetzigen Wert); 0 an der Kerze des Wechsels."""
    out, seit = np.zeros(len(d), np.int64), 0
    for t in range(len(d)):
        seit = 0 if (t == 0 or d[t] != d[t - 1]) else seit + 1
        out[t] = seit
    return out


def kandidaten_a():
    return [(f"A1_z_bis_{x}", "max", x) for x in ZMAX] + [(f"A2_z_ab_{x}", "min", x) for x in ZMIN]


def richtung_gefiltert(d: np.ndarray, z: np.ndarray, art: str, schwelle: float) -> np.ndarray:
    """Richtung d, wo die Bedingung gilt, sonst 0 (auch wenn z nicht bestimmt ist)."""
    ok = (z <= schwelle) if art == "max" else (z >= schwelle)        # Vergleiche mit nan sind falsch
    return np.where(ok, d, 0).astype(np.int8)


def _felder(ntage):
    return {"brut": np.zeros((len(D.COINS), 2, ntage)), "nord": np.zeros((len(D.COINS), 2, ntage)), "slipb": np.zeros((len(D.COINS), 2, ntage)),
            "markt": np.zeros((len(D.COINS), ntage)), "zahl": np.zeros((len(D.COINS), 7)), "slip_coin": np.zeros(len(D.COINS))}


def rechne_a(i_ende: int = E.ENDE_V1, mit_orders: int = 0):
    """Tagesreihen je Regel (Basis, sechs Kandidaten, Zerlegungen) und Coin, über den Kern von E23 mit Art B0."""
    ntage = D.N // E.TAG
    regeln = ["B0"] + [k for k, _, _ in kandidaten_a()] + [f"z_{i}" for i in range(len(Z_STUFEN))] + [f"alter_{i}" for i in range(len(ALTER_STUFEN))]
    erg = {k: _felder(ntage) for k in regeln}
    orders = {k: {} for k in regeln}
    leer = np.zeros(1)
    for ci, coin in enumerate(D.COINS):
        o, h, l, c, g, fs, slip = E.coin_daten(ci, i_ende)
        d, z = E.richtung_stunden(c), ausdehnung(c)
        alt = alter_stunden(d)
        richt = {"B0": d}
        for ken, art, x in kandidaten_a():
            richt[ken] = richtung_gefiltert(d, z, art, x)
        for i, (a, b) in enumerate(Z_STUFEN):
            richt[f"z_{i}"] = np.where((z >= a) & (z < b), d, 0).astype(np.int8)
        for i, (a, b) in enumerate(ALTER_STUFEN):
            richt[f"alter_{i}"] = np.where((alt >= a) & (alt < b), d, 0).astype(np.int8)
        for ken in regeln:
            r = erg[ken]
            od = np.zeros((mit_orders, 4))
            n = E.lauf(o, h, l, c, g, fs, slip, richt[ken], 12, 3, leer, leer, leer, leer, leer.astype(np.int8), leer.astype(np.int8), E.B0, i_ende,
                       r["brut"][ci], r["nord"][ci], r["slipb"][ci], r["markt"][ci], r["zahl"][ci], od)
            r["slip_coin"][ci] = slip
            if mit_orders:
                orders[ken][coin] = od[:min(n, mit_orders)]
    return erg, orders


def urteil_a(reihen: dict) -> dict:
    """Die vier Bedingungen wie in E23, Nachbar = nächstliegende Schwelle derselben Art."""
    for x in reihen.values():
        if not np.isfinite(x).all():
            raise SystemExit("Tagesreihe mit ungültigen Werten: kein Urteil.")
    sh = {key: E.sharpe(x) for key, x in reihen.items()}
    ueber = lambda k: all(sh[(k, zr)] > sh[("B0", zr)] for zr in ("T", "V1"))
    out = {}
    for fam in ("A1", "A2"):
        ks = [k for k, _, _ in kandidaten_a() if k.startswith(fam)]
        for i, ken in enumerate(ks):
            u = {}
            for zr in ("T", "V1"):
                p = E.stichprobe(reihen[(ken, zr)], reihen[("B0", zr)])
                u[zr] = {"differenz": sh[(ken, zr)] - sh[("B0", zr)], "anteil_ohne_vorteil": p,
                         "bedingung": bool(sh[(ken, zr)] > sh[("B0", zr)] and p <= E.GRENZE[zr])}
            nb = [ks[j] for j in (i - 1, i + 1) if 0 <= j < len(ks)]
            u["urteil"] = {"1_T": u["T"]["bedingung"], "2_V1": u["V1"]["bedingung"],
                           "3_netto_positiv": bool(reihen[(ken, "T")].sum() > 0 and reihen[(ken, "V1")].sum() > 0),
                           "4_nachbar": bool(any(ueber(x) for x in nb))}
            u["urteil"]["besteht_T_und_V1"] = all(u["urteil"].values())
            out[ken] = u
    return out


# ---------------------------------------------------------------------------------- Teil B und C (Tageskurse)
def lauf_signal(d: pd.DataFrame, sig: pd.Series, kalender: pd.DatetimeIndex, S: float, slip: float, gebuehr: float,
                funding_jahr: float = 0.0) -> pd.DataFrame:
    """Wie tagestrend.lauf_markt, aber mit vorgegebenem Signal: sig[Tag] gilt ab der Eröffnung dieses Börsentags."""
    d = d[(d.index >= kalender[0] - pd.Timedelta(days=60)) & (d.index <= kalender[-1])]
    o, c, s = d["open"].to_numpy(), d["close"].to_numpy(), sig.reindex(d.index).fillna(0.0).to_numpy()
    n = len(d)
    brutto, geb, fund, ums = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
    pos, richtung, cash, wert_alt = 0.0, 0.0, 0.0, 0.0
    tag_abstand = np.diff(d.index.to_numpy(), prepend=d.index.to_numpy()[:1]).astype("timedelta64[D]").astype(float)
    aktiv = d.index >= kalender[0]
    for i in range(n):
        if pos != 0.0:
            fund[i] -= funding_jahr / 365.0 * abs(pos) * c[i - 1] * tag_abstand[i]
        ziel = s[i] if aktiv[i] and i < n - 1 else 0.0
        if ziel != richtung:
            if pos != 0.0:
                px = o[i] * (1.0 - np.sign(pos) * slip)
                cash += pos * px; ums[i] += abs(pos) * px; pos = 0.0
            if ziel != 0.0:
                px = o[i] * (1.0 + ziel * slip)
                pos = ziel * S / px
                cash -= pos * px; ums[i] += abs(pos) * px
            richtung = ziel
        wert = cash + pos * c[i]
        brutto[i] = wert - wert_alt
        wert_alt = wert
        geb[i] = gebuehr * ums[i]
    return pd.DataFrame({"brutto": brutto, "gebuehr": geb, "funding": fund, "umsatz": ums}, index=d.index).reindex(kalender).fillna(0.0)


def aktien_laden(bis: pd.Timestamp = V1_ENDE):
    info = json.loads((ROOT / "reports/runde17_aktien.json").read_text())
    titel = sorted(k for k, v in info.items() if v["ok"])
    kurse = {}
    for k in titel:
        d = pd.read_parquet(ROOT / f"data/candles/aktien_1d/{k}.parquet")
        kurse[k] = d[d.index <= bis]                                 # nichts nach dem Ende des Rechenfensters
    gemessen = pd.Series({k: info[k]["spanne_bp"] for k in titel}, dtype=float)
    slip = (gemessen.fillna(gemessen.median()) / 1e4).clip(lower=0.00005)
    return kurse, slip.to_dict(), {"anzahl": len(titel), "spanne_median_bp": float(gemessen.median()), "ohne_messwert": int(gemessen.isna().sum())}


def baustein_aktien(kurse: dict, slip: dict, kal: pd.DatetimeIndex = KAL, stress: bool = False) -> pd.Series:
    """Tagesergebnis des Aktien-Bausteins (Einsatz 1 über alle Titel), netto mit Rebate; Aktien ohne Kurse im Fenster bleiben leer."""
    S = 1.0 / len(kurse)
    f = 2.0 if stress else 1.0
    summe = pd.Series(0.0, index=kal)
    for k, d in kurse.items():
        if len(d[d.index <= kal[-1]]) < 2:
            continue
        t = T.lauf_markt(d, kal, S, f * slip[k], f * TAKER, 0.10 if stress else 0.0)
        summe = summe + t["brutto"] - (1.0 - REBATE) * t["gebuehr"] + t["funding"]
    return summe


def btc_signal(bis: pd.Timestamp = V1_ENDE) -> pd.Series:
    """Signal je Kalendertag D (gültig ab der Eröffnung des Börsentags D): Vorzeichen von BTC-Schluss(D−1) − BTC-Schluss(D−15)."""
    i_ende = int(np.searchsorted(D.RASTER.values, np.datetime64(bis + pd.Timedelta(days=1))))
    c = np.array(D.laden("c")[D.COINS.index("BTC"), :i_ende], np.float64)
    tag = pd.Series(c[E.TAG - 1::E.TAG], index=pd.date_range("2021-07-01", periods=len(c) // E.TAG, freq="D"))   # Schluss der letzten Kerze des UTC-Tages
    return signal_vortag(tag)


def signal_vortag(tag: pd.Series) -> pd.Series:
    """tag: Tagesschlüsse je Kalendertag. Ergebnis je Tag D: Vorzeichen von Schluss(D−1) − Schluss(D−15), sonst 0."""
    roh = np.sign(tag - tag.shift(14))                               # an Tag X bekannt: Schluss(X) − Schluss(X−14)
    return roh.shift(1).fillna(0.0)                                  # Tag D nutzt X = D−1


def baustein_qqq(art: str, kal: pd.DatetimeIndex = KAL, stress: bool = False) -> pd.Series:
    k14 = json.loads((ROOT / "reports/runde14_kosten.json").read_text())
    slip = max(0.00005, k14["QQQ"]["spanne_bp"] / 1e4)
    d = pd.read_parquet(ROOT / "data/candles/tradfi_1d/QQQ.parquet")
    d = d[d.index <= kal[-1]]
    f = 2.0 if stress else 1.0
    if art == "eigen":                                               # QQQ nach dem eigenen 14-Tage-Trend (Runde 14)
        t = T.lauf_markt(d, kal, 1.0, f * slip, f * TAKER, 0.10 if stress else 0.0)
    else:
        sig = btc_signal(kal[-1]) if art == "btc" else pd.Series(1.0, index=pd.date_range("2020-01-01", kal[-1], freq="D"))
        t = lauf_signal(d, sig, kal, 1.0, f * slip, f * TAKER, 0.10 if stress else 0.0)
    return t["brutto"] - (1.0 - REBATE) * t["gebuehr"] + t["funding"]


def zeitraum(x: pd.Series, zr: str) -> np.ndarray:
    a, b = E.ZEITRAUM[zr]
    return x[(x.index >= a) & (x.index <= b)].to_numpy()


def baustein_urteil(netto: pd.Series, stress: pd.Series, b0: dict) -> dict:
    """Hürden 1 bis 3 für einen Baustein auf Tageskursen. b0: {Zeitraum: Tagesreihe der Basis aus E23}."""
    out = {}
    for zr in ("T", "V1"):
        x, s = zeitraum(netto, zr), zeitraum(stress, zr)
        if len(x) != len(b0[zr]) or not (np.isfinite(x).all() and np.isfinite(s).all()):
            raise SystemExit("Tagesreihen passen nicht zusammen: kein Urteil.")
        mix = 0.5 * b0[zr] + 0.5 * x
        p = E.stichprobe(mix, b0[zr])
        out[zr] = {"summe_pct": round(float(x.sum() * 100), 2), "sharpe": round(E.sharpe(x), 3), "einbruch_pct": round(E.einbruch(x) * 100, 2),
                   "stress_summe_pct": round(float(s.sum() * 100), 2), "korrelation_mit_basis": round(float(np.corrcoef(x, b0[zr])[0, 1]), 3),
                   "mischung_sharpe": round(E.sharpe(mix), 3), "basis_sharpe": round(E.sharpe(b0[zr]), 3), "mischung_einbruch_pct": round(E.einbruch(mix) * 100, 2),
                   "basis_einbruch_pct": round(E.einbruch(b0[zr]) * 100, 2), "anteil_ohne_vorteil": round(p, 4),
                   "h1": bool(x.sum() > 0), "h2": bool(s.sum() > 0), "h3": bool(E.sharpe(mix) > E.sharpe(b0[zr]) and p <= E.GRENZE[zr])}
    out["huerden"] = {"1_netto_positiv": out["T"]["h1"] and out["V1"]["h1"], "2_stress_positiv": out["T"]["h2"] and out["V1"]["h2"],
                      "3_mischung_besser": out["T"]["h3"] and out["V1"]["h3"]}
    out["besteht_T_und_V1"] = all(out["huerden"].values())
    return out


# --------------------------------------------------------------------------------------------------- Hauptlauf
def hauptlauf():
    out = {"experiment": "E24", "festlegung": "forschung/protokoll.md Abschnitt 45", "gerechnet_bis": "2024-06-30"}
    # Teil A
    erg, _ = rechne_a()
    reihen, a = {}, {}
    for ken, r in erg.items():
        e = {}
        for zr in ("T", "V1"):
            e[zr], reihen[(ken, zr)] = E.kennzahlen(r, zr)
            sl = E.tage(zr)
            halte = float(r["markt"][:, sl].sum() / E.TAG)           # Coin-Tage mit Position
            e[zr]["vor_orderkosten_je_100_haltetage_pct"] = round(float(r["brut"][:, :, sl].sum() / halte * 100 * 100), 2) if halte > 0 else None
            e[zr]["vor_orderkosten_summe_pct"] = round(float(r["brut"][:, :, sl].sum() / len(D.COINS) * 100), 2)
        a[ken] = e
    basis_alt = np.load(F / "ergebnisse/e23_marktstruktur_tage.npz")
    for zr in ("T", "V1"):                                           # die Basis muss genau die von E23 sein
        if not np.allclose(reihen[("B0", zr)], basis_alt[f"B0_{zr}"], atol=1e-12):
            raise SystemExit("Die Basis weicht von E23 ab.")
    kand = {(k, zr): v for (k, zr), v in reihen.items() if k == "B0" or k[0] == "A"}
    for ken, u in urteil_a(kand).items():
        for zr in ("T", "V1"):
            a[ken][zr].update(sharpe_minus_basis=round(u[zr]["differenz"], 3), anteil_ohne_vorteil=round(u[zr]["anteil_ohne_vorteil"], 4), bedingung=u[zr]["bedingung"])
        a[ken]["urteil"] = u["urteil"]
    out["teil_a"] = {"regeln": a, "z_stufen": [list(map(float, s)) for s in Z_STUFEN], "alter_stufen_h": [list(s) for s in ALTER_STUFEN],
                     "besteher": [k for k, e in a.items() if e.get("urteil", {}).get("besteht_T_und_V1")]}
    # Teil B und C
    b0 = {zr: reihen[("B0", zr)] for zr in ("T", "V1")}
    kurse, slip, info = aktien_laden()
    nb, sb = baustein_aktien(kurse, slip), baustein_aktien(kurse, slip, stress=True)
    out["teil_b"] = {"aktien": info, **baustein_urteil(nb, sb, b0)}
    nc, sc = baustein_qqq("btc"), baustein_qqq("btc", stress=True)
    out["teil_c"] = baustein_urteil(nc, sc, b0)
    out["teil_c"]["einordnung"] = {art: {zr: {"summe_pct": round(float(zeitraum(baustein_qqq(art), zr).sum() * 100), 2),
                                              "sharpe": round(E.sharpe(zeitraum(baustein_qqq(art), zr)), 3)} for zr in ("T", "V1")}
                                   for art in ("eigen", "halten")}
    out["einstufung"] = {"teil_a": "offen: V2 für " + ", ".join(out["teil_a"]["besteher"]) if out["teil_a"]["besteher"] else "A (verworfen)",
                         "teil_b": "offen: Nachprüfung" if out["teil_b"]["besteht_T_und_V1"] else "A (verworfen)",
                         "teil_c": "offen: Nachprüfung" if out["teil_c"]["besteht_T_und_V1"] else "A (verworfen)"}
    ERGEBNIS.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    np.savez_compressed(ERGEBNIS.with_name("e24_einstieg_und_pool_tage.npz"), **{f"{k}_{z}": v for (k, z), v in reihen.items()},
                        aktien=nb.to_numpy(), aktien_stress=sb.to_numpy(), qqq_btc=nc.to_numpy(), qqq_btc_stress=sc.to_numpy())
    return out


if __name__ == "__main__":
    e = hauptlauf()
    print(json.dumps(e["einstufung"], ensure_ascii=False))
