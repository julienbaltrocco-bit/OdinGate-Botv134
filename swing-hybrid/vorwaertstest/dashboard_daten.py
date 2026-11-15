"""Daten für das Dashboard des Vorwärtstests: eine JSON-Datei aus den Lauf-Dateien (nur Standardbibliothek).

    python3 -m vorwaertstest.dashboard_daten --daten vorwaertstest/lauf --config vorwaertstest/config_lauf.json
"""
import argparse
import datetime as dt
import json
from pathlib import Path

from . import bot

TAKT_MINUTEN = 5


def bauen(cfg: dict, daten: Path) -> dict:
    st, pr, sp = bot.lesen(daten / "stand.csv"), bot.lesen(daten / "protokoll.csv"), bot.lesen(daten / "spannen.csv")
    z = json.loads((daten / "zustand.json").read_text())
    kap = cfg["kapital_usd"]
    pz = lambda x: round(float(x) / kap * 100, 4)
    verlauf = [{"zeit": r["zeit"].replace(" ", "T") + ":00Z", "mit_rebate": pz(r["netto_mit_rebate"]),
                "ohne_rebate": pz(r["netto_ohne_rebate"]), "vor_gebuehren": pz(r["brutto"]),
                "einsatz": round(float(r["einsatz"]) / kap * 100, 2)} for r in st]
    einstieg = {}
    for r in pr:
        if r["grund"] == "einstieg":
            einstieg[r["coin"]] = (float(r["fuellkurs"]), r["zeit"])
    positionen = []
    for coin in cfg["coins"]:
        q, kurs = z["pos"].get(coin, 0.0), z.get("kurs", {}).get(coin, 0.0)
        ein, seit = einstieg.get(coin, (0.0, ""))
        positionen.append({"coin": coin, "richtung": "Long" if q > 0 else "Short" if q < 0 else "keine",
                           "seit": seit, "einstieg": ein if q else None, "kurs": kurs,
                           "betrag": round(abs(q) * kurs, 2), "ergebnis": round(q * (kurs - ein), 2) if q else 0.0,
                           "ergebnis_pct": round((kurs / ein - 1) * (1 if q > 0 else -1) * 100, 3) if q and ein else 0.0})
    orders = [{"nr": i + 1, "zeit": r["zeit"], "coin": r["coin"], "seite": "Kauf" if r["seite"] == "kauf" else "Verkauf",
               "grund": {"einstieg": "Einstieg", "schliessen": "Schließen", "tageslimit": "Tageslimit"}.get(r["grund"], r["grund"]),
               "kurs": float(r["fuellkurs"]), "volumen": round(float(r["volumen"]), 2), "slippage_bp": float(r["slippage_bp"])}
              for i, r in enumerate(pr)][-60:][::-1]
    l = st[-1]
    start, ende = (dt.datetime.fromisoformat(st[i]["zeit"]) for i in (0, -1))
    tage = (ende - start).total_seconds() / 86400
    vol = sum(float(r["volumen"]) for r in pr)
    slip = sum(float(r["slippage_bp"]) * float(r["volumen"]) for r in pr) / vol if vol else 0.0
    mess = [(float(r["kauf_bp"]) + float(r["verkauf_bp"])) / 2 for r in sp if r["kauf_bp"] != "" and r["verkauf_bp"] != ""]
    spitze, dd = 0.0, 0.0
    for r in verlauf:
        spitze = max(spitze, r["mit_rebate"])
        dd = max(dd, (spitze - r["mit_rebate"]) / (100 + spitze) * 100)
    kennzahlen = [{"start": st[0]["zeit"], "letzter_lauf": l["zeit"], "tage": round(tage, 2), "laeufe": len(st), "kapital": kap,
                   "mit_rebate_usd": round(float(l["netto_mit_rebate"]), 2), "mit_rebate_pct": pz(l["netto_mit_rebate"]),
                   "ohne_rebate_usd": round(float(l["netto_ohne_rebate"]), 2), "ohne_rebate_pct": pz(l["netto_ohne_rebate"]),
                   "vor_gebuehren_usd": round(float(l["brutto"]), 2), "vor_gebuehren_pct": pz(l["brutto"]),
                   "gebuehr_usd": round(float(l["gebuehr"]), 2), "rebate_usd": round(float(l["rebate"]), 2),
                   "funding_usd": round(float(l["funding"]), 2), "orders": len(pr), "volumen_usd": round(vol, 0),
                   "slippage_orders_bp": round(slip, 3), "slippage_messung_bp": round(sum(mess) / len(mess), 3) if mess else 0.0,
                   "messungen": len(mess), "long": int(l["long"]), "short": int(l["short"]),
                   "einsatz_pct": round(float(l["einsatz"]) / kap * 100, 1), "einbruch_pct": round(dd, 3),
                   "hebel": cfg["hebel"], "positionswert_usd": round(float(l["einsatz"]), 0),
                   "margin_usd": round(float(l["einsatz"]) / cfg["hebel"], 0),
                   "margin_pct": round(float(l["einsatz"]) / cfg["hebel"] / kap * 100, 1)}]
    if len(verlauf) > 400:                                  # ältere Punkte ausdünnen, die letzten 120 bleiben vollständig
        alt, neu = verlauf[:-120], verlauf[-120:]
        schritt = -(-len(alt) // 280)
        verlauf = alt[::schritt] + neu
    return {"kennzahlen": kennzahlen, "verlauf": verlauf, "positionen": positionen, "orders": orders, "takt_minuten": TAKT_MINUTEN,
            "geschrieben": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


def main(argv=None) -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=Path); p.add_argument("--daten", type=Path, required=True)
    a = p.parse_args(argv)
    d = bauen(bot.konfig(a.config), a.daten)
    (a.daten / "dashboard.json").write_text(json.dumps(d, separators=(",", ":")))
    print("dashboard.json:", len(d["verlauf"]), "Läufe,", len(d["orders"]), "Orders")


if __name__ == "__main__":
    main()
