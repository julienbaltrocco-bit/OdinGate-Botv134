"""ENG-E: Kontoidentitaeten und Kennzahlen an einer KOPIE der laufenden Papier-Daten (Schnappschuss, nur lesend).
Aufruf: .venv/bin/python -I -B e_snapshot_identitaeten.py <schnappschuss-verzeichnis>"""
import csv, json, statistics, sys, datetime as dt
from pathlib import Path
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid")
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/src")
from vorwaertstest import kern
SNAP = Path(sys.argv[1])
VT = Path("/home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest")
lesen = lambda p: list(csv.DictReader(open(p, newline="")))
for name, cfgdatei in (("lauf", "config_lauf.json"), ("lauf_tpsl", "config_lauf_tpsl.json")):
    cfg = json.loads((VT / cfgdatei).read_text()); d = SNAP / name
    z = json.loads((d / "zustand.json").read_text()); st = lesen(d / "stand.csv"); pr = lesen(d / "protokoll.csv"); sp = lesen(d / "spannen.csv")
    dash = json.loads((d / "dashboard.json").read_text()); k = dash["kennzahlen"][0]
    print(f"===== {name} (Hebel {cfg['hebel']}, Tageslimit {cfg['tagesverlust_limit']}, tp {cfg.get('tp')}, sl {cfg.get('sl')}) =====")
    v = kern.vermoegen(z, z["kurs"]); l = st[-1]
    print("1) kern.vermoegen(zustand) vs. letzte Zeile stand.csv:")
    for f in ("brutto", "gebuehr", "rebate", "funding", "netto_ohne_rebate", "netto_mit_rebate"):
        print(f"   {f:18s} {v[f]:12.4f} {float(l[f]):12.4f}  diff {v[f] - float(l[f]):+.5f}")
    # 2) aus dem Orderprotokoll unabhaengig
    kasse = {}; menge = {}
    for x in pr:
        s = 1 if x["seite"] == "kauf" else -1
        kasse[x["coin"]] = kasse.get(x["coin"], 0.0) - s * float(x["menge"]) * float(x["fuellkurs"])
        menge[x["coin"]] = menge.get(x["coin"], 0.0) + s * float(x["menge"])
    brutto_p = sum(kasse[c] + menge[c] * z["kurs"][c] for c in kasse)
    geb = sum(float(x["gebuehr"]) for x in pr); reb = sum(float(x["rebate"]) for x in pr); vol = sum(float(x["volumen"]) for x in pr)
    print(f"2) aus protokoll.csv: brutto {brutto_p:.4f} (Zustand {v['brutto']:.4f}); Positionen gleich: {all(abs(menge[c] - z['pos'][c]) < 1e-9 for c in menge)}; "
          f"Gebuehr {geb:.6f} (Zustand {z['gebuehr']:.6f}), Gebuehr/Volumen {geb / vol:.6f}, Rebate/Gebuehr {reb / geb:.4f}")
    print("   je Order |gebuehr - 0.0008*volumen| max:", max(abs(float(x["gebuehr"]) - 0.0008 * float(x["volumen"])) for x in pr),
          "| |rebate - 0.85*gebuehr| max:", max(abs(float(x["rebate"]) - 0.85 * float(x["gebuehr"])) for x in pr))
    # 3) Dashboard / Browser
    b_brutto = sum(p["kasse"] + p["menge"] * p["kurs"] for p in dash["positionen"])
    b_ohne = b_brutto - k["gebuehr_usd"] + k["funding_usd"]; b_mit = b_ohne + k["rebate_usd"]
    zeile = next(r for r in st if r["zeit"] == k["letzter_lauf"])
    print(f"3) dashboard.json (letzter_lauf {k['letzter_lauf']}): mit_rebate_usd {k['mit_rebate_usd']} | stand.csv {zeile['netto_mit_rebate']} | Browser-Formel konto() mit Bot-Kursen {b_mit:.4f}")
    sp_, dd = 0.0, 0.0
    for r in st:
        if r["zeit"] > k["letzter_lauf"]: break
        x = float(r["netto_mit_rebate"]) / cfg["kapital_usd"] * 100; sp_ = max(sp_, x); dd = max(dd, (sp_ - x) / (100 + sp_) * 100)
    print(f"   einbruch_pct Dashboard {k['einbruch_pct']} | nachgerechnet {dd:.3f} | margin_usd {k['margin_usd']} = einsatz {zeile['einsatz']} / Hebel {cfg['hebel']} -> {float(zeile['einsatz']) / cfg['hebel']:.0f}; margin_pct {k['margin_pct']}")
    # 4) Positionsgroessen
    nominal = cfg["kapital_usd"] * cfg["hebel"] / len(cfg["coins"])
    print(f"4) Sollbetrag je Coin {nominal:.0f} USD; Ist beim Einstieg (Volumen / Soll):")
    print("   " + ", ".join(f"{x['coin']} {float(x['volumen']) / nominal * 100:.1f} %" for x in pr if x["grund"] == "einstieg"))
    print(f"   Summe Einstiegsvolumen {vol:.2f} = {vol / (nominal * len(cfg['coins'])) * 100:.2f} % vom Soll; Hebel effektiv {vol / cfg['kapital_usd']:.3f}")
    # 5) Funding
    fz = [r for r in st if float(r["funding"]) != 0.0]
    if fz:
        e = float(fz[0]["einsatz"]); print(f"5) Funding erstmals {fz[0]['zeit']}: {fz[0]['funding']} USD auf Einsatz {e:.0f} USD = {float(fz[0]['funding']) / e * 100:.5f} % (alle Short)")
        print("   Zeitpunkte mit Aenderung des Funding-Standes:", sorted({r["zeit"] for i, r in enumerate(st) if i and r["funding"] != st[i - 1]["funding"]}))
    else:
        print("5) noch kein Funding gebucht")
    # 6) Takt der Laeufe
    t = [dt.datetime.fromisoformat(r["zeit"]) for r in st]
    ab = [(b - a).total_seconds() / 60 for a, b in zip(t, t[1:])]
    print(f"6) {len(st)} Laeufe von {st[0]['zeit']} bis {st[-1]['zeit']}; Abstand Minuten: median {statistics.median(ab):.0f}, min {min(ab):.0f}, max {max(ab):.0f}; "
          f"dashboard takt_minuten = {dash['takt_minuten']}")
    erste = {}
    for x in t:
        erste.setdefault(x.replace(minute=0), x.minute)
    print("   erster Lauf nach voller Stunde (Minute):", [erste[h] for h in sorted(erste)][1:])
    # 7) gemessene Slippage je Coin gegen Backtest-Annahme
    leer = sum(1 for r in sp if r["kauf_bp"] == "" or r["verkauf_bp"] == "")
    print(f"7) spannen.csv: {len(sp)} Messungen, davon ohne volle Fuellung (Tiefe < Standardgroesse): {leer}")
    if name == "lauf":
        import numpy as np
        from hybrid import research as R
        ann = dict(zip(R.GRUPPE_A, R.yubit_kosten(R.GRUPPE_A)[0] * 1e4))
        print("   Coin  Messungen  Slippage-Mittel bp (Kauf/Verkauf)  max bp  halbe Spanne Mittel bp | Backtest-Annahme bp")
        ges_m, ges_a = [], []
        for c in cfg["coins"]:
            w = [(float(r["kauf_bp"]) + float(r["verkauf_bp"])) / 2 for r in sp if r["coin"] == c and r["kauf_bp"] != "" and r["verkauf_bp"] != ""]
            mx = max(max(float(r["kauf_bp"]), float(r["verkauf_bp"])) for r in sp if r["coin"] == c and r["kauf_bp"] != "" and r["verkauf_bp"] != "")
            hs = statistics.fmean(float(r["spanne_bp"]) / 2 for r in sp if r["coin"] == c)
            print(f"   {c:5s} {len(w):5d} {statistics.fmean(w):10.3f} {mx:28.3f} {hs:10.3f} {ann[c]:24.3f}")
            ges_m.append(statistics.fmean(w)); ges_a.append(ann[c])
        print(f"   Mittel ueber Coins: gemessen {statistics.fmean(ges_m):.3f} bp | Annahme {statistics.fmean(ges_a):.3f} bp | bot.bericht vergleicht mit festen 5 bp")
