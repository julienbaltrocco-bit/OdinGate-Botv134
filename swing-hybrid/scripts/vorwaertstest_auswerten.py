"""Vorwärtstest auswerten: echte Slippage aus einem Order-Protokoll messen und gegen die Schmerzgrenze halten.

    .venv/bin/python -I scripts/vorwaertstest_auswerten.py protokoll.csv

Protokoll: eine Zeile je gefüllter Order, Spalten (Komma-getrennt, Kopfzeile):
    zeit        Zeitpunkt des Signals (volle Stunde, UTC), z. B. 2026-11-20 14:00
    coin        z. B. BTC
    seite       kauf oder verkauf
    signalkurs  Kurs im Moment des Signals (letzter Kurs / Eröffnung der neuen Stunde)
    fuellkurs   tatsächlicher Durchschnittskurs der Füllung
    volumen     Nominalwert in USDT
    gebuehr     gezahlte Gebühr in USDT
    rebate      erhaltenes Rebate in USDT (0, wenn noch nicht gutgeschrieben)

Slippage = wie viel schlechter als der Signalkurs gefüllt wurde (Kauf: teurer, Verkauf: billiger), in Prozent.
Die Simulation rechnet mit 0,05 %. Der Kandidat trägt bis etwa 0,07 % (10 Coins) bzw. 0,09 % (breites Portfolio).
"""
import sys

import pandas as pd

ANNAHME, GRENZE = 0.0005, 0.0007


def auswerten(df: pd.DataFrame) -> dict:
    seite = df["seite"].str.lower().map({"kauf": 1.0, "verkauf": -1.0})
    if seite.isna().any():
        raise ValueError("Spalte 'seite' darf nur 'kauf' oder 'verkauf' enthalten")
    slip = seite * (df["fuellkurs"] - df["signalkurs"]) / df["signalkurs"]
    vol = df["volumen"].abs()
    mittel = float((slip * vol).sum() / vol.sum())
    return {
        "orders": int(len(df)), "volumen": float(vol.sum()),
        "slippage_mittel": mittel, "slippage_median": float(slip.median()), "slippage_p90": float(slip.quantile(0.9)),
        "gebuehr_satz": float(df["gebuehr"].sum() / vol.sum()),
        "rebate_anteil": float(df["rebate"].sum() / df["gebuehr"].sum()) if df["gebuehr"].sum() > 0 else float("nan"),
        "je_coin": (slip * vol).groupby(df["coin"]).sum().div(vol.groupby(df["coin"]).sum()).to_dict(),
        "urteil": "unter der Annahme" if mittel <= ANNAHME else "über der Annahme, unter der Schmerzgrenze" if mittel <= GRENZE
                  else "ÜBER der Schmerzgrenze: so trägt der Kandidat nicht",
    }


if __name__ == "__main__":
    e = auswerten(pd.read_csv(sys.argv[1]))
    pz = lambda x: f"{x * 100:.3f} %".replace(".", ",")
    print(f"{e['orders']} Orders, Volumen {e['volumen']:.0f} USDT")
    print(f"Slippage: Mittel {pz(e['slippage_mittel'])}, Median {pz(e['slippage_median'])}, schlechteste 10 % ab {pz(e['slippage_p90'])}")
    print(f"Gebührensatz {pz(e['gebuehr_satz'])} (erwartet 0,080 %), Rebate {e['rebate_anteil'] * 100:.0f} % der Gebühr (erwartet 85 %)")
    print("Je Coin:", {k: pz(v) for k, v in sorted(e["je_coin"].items())})
    print("Urteil:", e["urteil"])
    if e["orders"] < 200:
        print("Hinweis: unter 200 Orders ist das Mittel noch unsicher (bei rund 6 Orders am Tag etwa 5 Wochen).")
