"""E27: Tagesvariante der Trendregel gegen die Stundenregel (H27).

Festlegung: forschung/protokoll.md, Abschnitt 51. Beide Regeln laufen im geprüften Rechenkern von E23 (Art B0); die
Tagesvariante übernimmt die Richtung nur einmal am Tag.

  .venv/bin/python -I forschung/experimente/e27_tagesvariante.py          # Stufe 1: T und V1 (nichts danach wird geladen)
  .venv/bin/python -I forschung/experimente/e27_tagesvariante.py --v2     # Stufe 2: V2, einmal, nur wenn Stufe 1 es freigibt
"""
import json
import sys
from pathlib import Path

import numpy as np

F = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F))
from experimente import e23_marktstruktur as E  # noqa: E402
from fabrik import daten as D  # noqa: E402

PHASEN = (0, 4, 8, 12, 16, 20)                                       # Uhrzeit (UTC), zu der die Tagesvariante die Richtung übernimmt
ABSTAENDE = (4, 12)                                                  # Abfrage alle 4 und alle 12 Stunden: nur Einordnung, nur T und V1
ERGEBNIS = F / "ergebnisse/e27_tagesvariante.json"


def name_phase(p: int) -> str:
    return "TAG" if p == 0 else f"TAG_{p:02d}"


def richtung_abgefragt(d: np.ndarray, abstand: int = 24, phase: int = 0) -> np.ndarray:
    """Richtung d je Stundenkerze, aber nur übernommen an Stundenkerzen, die zu einer vollen Stunde schließen, die `phase`
    (mod `abstand`) entspricht; dazwischen gilt der letzte übernommene Wert, davor 0. Stundenkerze t schließt t+1 Stunden
    nach dem 01.07.2021 00:00 UTC."""
    idx = np.arange(len(d))
    probe = ((idx + 1 - phase) % abstand) == 0
    letzte = np.maximum.accumulate(np.where(probe, idx, -1))
    return np.where(letzte >= 0, d[np.maximum(letzte, 0)], 0).astype(np.int8)


def regeln(mit_abstaenden: bool) -> dict:
    """{Kennung: (Abstand in Stunden, Phase)}; B0 fragt jede Stunde ab."""
    r = {"B0": (1, 0)}
    r.update({name_phase(p): (24, p) for p in PHASEN})
    if mit_abstaenden:
        r.update({f"ALLE_{a}H": (a, 0) for a in ABSTAENDE})
    return r


def v2_geoeffnet() -> bool:
    return ERGEBNIS.exists() and "V2" in json.loads(ERGEBNIS.read_text())


def rechne(i_ende: int, mit_abstaenden: bool, mit_orders: int = 0):
    """Tagesfelder je Regel und Coin bis Kerze i_ende (ausschließlich), über den Kern von E23 mit Art B0.
    Über das Ende von V1 hinaus wird nur gerechnet, wenn die Öffnung von V2 schon in der Ergebnisdatei steht."""
    if i_ende > E.ENDE_V1 and not v2_geoeffnet():
        raise SystemExit("V2 ist nicht geöffnet: Es wird nichts nach dem 30.06.2024 gerechnet.")
    ntage = D.N // E.TAG
    rg = regeln(mit_abstaenden)
    erg = {k: {"brut": np.zeros((len(D.COINS), 2, ntage)), "nord": np.zeros((len(D.COINS), 2, ntage)), "slipb": np.zeros((len(D.COINS), 2, ntage)),
               "markt": np.zeros((len(D.COINS), ntage)), "zahl": np.zeros((len(D.COINS), 7)), "slip_coin": np.zeros(len(D.COINS))} for k in rg}
    orders = {k: {} for k in rg}
    leer, leer8 = np.zeros(1), np.zeros(1, np.int8)
    for ci, coin in enumerate(D.COINS):
        o, h, l, c, g, fs, slip = E.coin_daten(ci, i_ende)
        d = E.richtung_stunden(c)
        for ken, (abstand, phase) in rg.items():
            dh = d if abstand == 1 else richtung_abgefragt(d, abstand, phase)
            r = erg[ken]
            od = np.zeros((mit_orders, 4))
            n = E.lauf(o, h, l, c, g, fs, slip, dh, 12, 3, leer, leer, leer, leer, leer8, leer8, E.B0, i_ende,
                       r["brut"][ci], r["nord"][ci], r["slipb"][ci], r["markt"][ci], r["zahl"][ci], od)
            r["slip_coin"][ci] = slip
            if mit_orders:
                orders[ken][coin] = od[:min(n, mit_orders)]
    return erg, orders


def reihen_zeitraum(erg: dict, zr: str) -> tuple:
    """Tagesreihen des Kontos je Regel für (Kosten, Rebate) und die Zahl der Orders im Zeitraum."""
    sl = E.tage(zr)
    reihen, orders = {}, {}
    for ken, r in erg.items():
        for kosten, bewegt in (("bewegt", True), ("ruhig", False)):
            for reb, rebate in (("mit", True), ("ohne", False)):
                x = E.netto(r, bewegt=bewegt, rebate=rebate)[:, :, sl].sum(1).mean(0)
                if not np.isfinite(x).all():
                    raise SystemExit("Tagesreihe mit ungültigen Werten: kein Urteil.")
                reihen[(ken, kosten, reb)] = x
        orders[ken] = float(r["nord"][:, :, sl].sum())
    return reihen, orders


def bedingungen(reihen: dict, orders: dict) -> dict:
    """Bedingungen A bis D der Festlegung für einen Zeitraum (Hauptrechnung: bewegte Kosten), auf ungerundeten Werten."""
    def a(ken):
        x, b = reihen[(ken, "bewegt", "ohne")], reihen[("B0", "bewegt", "ohne")]
        return bool(x.sum() > b.sum() and E.sharpe(x) > E.sharpe(b))
    b0, tg = float(reihen[("B0", "bewegt", "mit")].sum()), float(reihen[("TAG", "bewegt", "mit")].sum())
    je_phase = {name_phase(p): a(name_phase(p)) for p in PHASEN}
    out = {"A_ohne_rebate_besser": je_phase["TAG"],
           "B_mit_rebate_nicht_schlechter": bool((tg > 0 and tg >= 2.0 / 3.0 * b0) if b0 > 0 else (tg >= b0)),
           "C_hoechstens_ein_drittel_der_orders": bool(orders["TAG"] <= orders["B0"] / 3.0),
           "D_mindestens_vier_von_sechs_uhrzeiten": bool(sum(je_phase.values()) >= 4), "A_je_uhrzeit": je_phase}
    out["alle"] = bool(out["A_ohne_rebate_besser"] and out["B_mit_rebate_nicht_schlechter"] and out["C_hoechstens_ein_drittel_der_orders"]
                       and out["D_mindestens_vier_von_sechs_uhrzeiten"])
    return out


def teile_zeitraum(erg: dict, zr: str) -> dict:
    """Zerlegung je Regel in Punkten des Kontos: Ergebnis vor Kosten (Kurs und Funding), Slippage, Gebühr."""
    sl, nc = E.tage(zr), len(D.COINS)
    out = {}
    for ken, r in erg.items():
        n = r["nord"][:, :, sl]
        out[ken] = {"vor_kosten": float(r["brut"][:, :, sl].sum() / nc), "orders": float(n.sum()),
                    "slippage_bewegt": float(r["slipb"][:, :, sl].sum() / 1e4 / nc),
                    "slippage_ruhig": float((n.sum(axis=(1, 2)) * r["slip_coin"]).sum() / 1e4 / nc),
                    "gebuehr_mit_rebate": float(n.sum() * E.GEB_BP * (1 - E.REBATE) / 1e4 / nc), "gebuehr_ohne_rebate": float(n.sum() * E.GEB_BP / 1e4 / nc)}
    return out


def bericht(reihen: dict, orders: dict, zr: str, teile: dict = None) -> dict:
    n = E.tage(zr).stop - E.tage(zr).start
    out = {}
    for ken in sorted({k for k, _, _ in reihen}):
        e = {"orders_je_tag": round(orders[ken] / n, 2)}
        if teile is not None:
            t, b = teile[ken], teile["B0"]
            e["zerlegung_pct"] = {k: round(v * 100, 2) for k, v in t.items() if k != "orders"}
            if ken != "B0":                                          # Unterschied zur Stundenregel: Zeitpunkt, gesparte Slippage, gesparte Gebühr
                kern_t, kern_b = t["vor_kosten"] - t["slippage_bewegt"], b["vor_kosten"] - b["slippage_bewegt"]
                weniger = b["orders"] - t["orders"]
                e["gegen_b0_pct"] = {"zeitpunkt_vor_kosten": round((t["vor_kosten"] - b["vor_kosten"]) * 100, 2),
                                     "slippage_gespart": round((b["slippage_bewegt"] - t["slippage_bewegt"]) * 100, 2),
                                     "gebuehr_gespart_mit_rebate": round((b["gebuehr_mit_rebate"] - t["gebuehr_mit_rebate"]) * 100, 2),
                                     "gebuehr_gespart_ohne_rebate": round((b["gebuehr_ohne_rebate"] - t["gebuehr_ohne_rebate"]) * 100, 2)}
                # Gebühr je Order in bp, ab der die Regel vor der Stundenregel liegt (negativ: schon ohne jede Gebühr)
                e["gleichstand_gebuehr_bp"] = round((kern_b - kern_t) * 1e4 * len(D.COINS) / weniger, 2) if weniger > 0 else None
        for kosten in ("bewegt", "ruhig"):
            for reb in ("mit", "ohne"):
                x = reihen[(ken, kosten, reb)]
                e[f"{kosten}_{reb}_rebate"] = {"summe_pct": round(float(x.sum() * 100), 2), "sharpe": round(E.sharpe(x), 3), "einbruch_pct": round(E.einbruch(x) * 100, 2)}
        if ken != "B0":
            e["anteil_ohne_vorteil_ohne_rebate"] = round(E.stichprobe(reihen[(ken, "bewegt", "ohne")], reihen[("B0", "bewegt", "ohne")]), 4)
        out[ken] = e
    return out


def stufe1():
    if v2_geoeffnet():
        raise SystemExit("V2 ist schon geöffnet; das Ergebnis wird nicht überschrieben.")
    erg, _ = rechne(E.ENDE_V1, mit_abstaenden=True)
    out = {"experiment": "E27", "festlegung": "forschung/protokoll.md Abschnitt 51", "gerechnet_bis": "2024-06-30 (V2 nicht gerechnet)"}
    tage = {}
    for zr in ("T", "V1"):
        reihen, orders = reihen_zeitraum(erg, zr)
        out[zr] = {"regeln": bericht(reihen, orders, zr, teile_zeitraum(erg, zr)), "bedingungen": bedingungen(reihen, orders)}
        tage.update({f"{k}_{ko}_{rb}_{zr}": v for (k, ko, rb), v in reihen.items()})
    out["v2_frei"] = bool(out["T"]["bedingungen"]["alle"] and out["V1"]["bedingungen"]["alle"])
    out["einstufung"] = "offen: V2 wird geöffnet" if out["v2_frei"] else "A (verworfen): Bedingungen schon in T oder V1 nicht erfüllt; V2 bleibt zu"
    ERGEBNIS.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    np.savez_compressed(ERGEBNIS.with_name("e27_tagesvariante_tage.npz"), **tage)
    return out


def stufe2():
    alt = json.loads(ERGEBNIS.read_text())
    if "V2" in alt:
        raise SystemExit("V2 wurde schon geöffnet (einmalig).")
    if not alt.get("v2_frei"):
        raise SystemExit("Stufe 1 gibt V2 nicht frei.")
    if str(D.RASTER[-1]) != "2025-03-31 23:55:00" or D.N != E.tage("V2").stop * E.TAG:
        raise SystemExit("Der Speicher endet nicht mit V2: Abbruch, damit nichts ab 04/2025 gelesen wird.")
    # Vorprüfungen, die V2 nicht brauchen, vor der Sperre: Stufe 1 muss sich bitgleich wiederholen lassen und bestehen
    datei = ERGEBNIS.with_name("e27_tagesvariante_tage.npz")
    if not datei.exists():
        raise SystemExit("Die Tagesreihen aus Stufe 1 fehlen: erst Stufe 1 rechnen.")
    vorher = np.load(datei)
    probe, _ = rechne(E.ENDE_V1, mit_abstaenden=False)
    for zr in ("T", "V1"):
        reihen, orders = reihen_zeitraum(probe, zr)
        for (k, ko, rb), v in reihen.items():
            if f"{k}_{ko}_{rb}_{zr}" not in vorher.files or not np.array_equal(v, vorher[f"{k}_{ko}_{rb}_{zr}"]):
                raise SystemExit(f"{k} in {zr} lässt sich nicht bitgleich wiederholen: Abbruch vor der Öffnung.")
        if not bedingungen(reihen, orders)["alle"]:
            raise SystemExit(f"Die Bedingungen in {zr} gelten bei der Wiederholung nicht: Abbruch vor der Öffnung.")
    alt["V2"] = {"stand": "geöffnet, Rechnung läuft"}                # Sperre steht, bevor die erste Zahl aus V2 entsteht
    ERGEBNIS.write_text(json.dumps(alt, ensure_ascii=False, indent=1) + "\n")
    erg, _ = rechne(D.N, mit_abstaenden=False)
    for zr in ("T", "V1"):                                           # zweite Sicherung: die früheren Zeiträume kommen unverändert heraus
        reihen, _ = reihen_zeitraum(erg, zr)
        for (k, ko, rb), v in reihen.items():
            if not np.array_equal(v, vorher[f"{k}_{ko}_{rb}_{zr}"]):
                raise SystemExit(f"{k} in {zr} weicht von Stufe 1 ab: Abbruch.")
    reihen, orders = reihen_zeitraum(erg, "V2")
    alt["V2"] = {"regeln": bericht(reihen, orders, "V2", teile_zeitraum(erg, "V2")), "bedingungen": bedingungen(reihen, orders)}
    alt["gerechnet_bis"] = "2025-03-31 (V2 einmal geöffnet)"
    alt["einstufung"] = "C (Kandidat für Test 4 auf Papier)" if alt["V2"]["bedingungen"]["alle"] else "B (interessant): besteht T und V1, nicht V2"
    ERGEBNIS.write_text(json.dumps(alt, ensure_ascii=False, indent=1) + "\n")
    np.savez_compressed(ERGEBNIS.with_name("e27_tagesvariante_tage_v2.npz"), **{f"{k}_{ko}_{rb}": v for (k, ko, rb), v in reihen.items()})
    return alt


if __name__ == "__main__":
    a = stufe2() if "--v2" in sys.argv[1:] else stufe1()
    print(a["einstufung"])
