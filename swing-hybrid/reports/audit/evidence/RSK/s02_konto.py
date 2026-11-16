"""RSK 02: Kontoverlauf des Kandidaten bei Hebel 1 und 3 je Zeitraum, Ausfallschwellen, Start-Tag-Analyse.

Bauart wie der Papier-Test: Größe beim Einstieg fest (Startkapital x Hebel / 10 je Coin), kein Zinseszins, kein
Tageslimit, Yubit-Kosten (Taker 0,08 %, 85 % Rebate, Slippage je Coin aus der Yubit-Stichprobe). Kein Parameter verändert.
Jedes Fenster beginnt mit einem FRISCHEN Start (alle zehn Positionen neu in Standardgröße), wie ein neu gestarteter Papier-Test.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from rsk_common import A, M, R, SCRATCH, dd_stat, frisch, runner, starts_sim

OUT = {}
FEE = runner.TAKER * (1 - runner.MIT.rebate)
SLIP = R.yubit_kosten(A)[0]
t0 = time.time()


def fenster_stat(ix, eq1, ex1, hebel):
    konto = 1.0 + hebel * eq1                                   # Kontostand, Start des Fensters = 1
    s = pd.Series(konto, index=ix)
    out = {"von": str(ix[0]), "bis": str(ix[-1]), "tage": len(ix) / 288.0, "hebel": hebel,
           "ergebnis": float(konto[-1] - 1.0), "pro_jahr": float((konto[-1] - 1.0) / (len(ix) / 288.0) * 365),
           "konto_min": float(konto.min()), "konto_min_zeit": str(ix[int(konto.argmin())]), **dd_stat(konto, ix)}
    schluss = s.resample("1D").last()
    tag = schluss.diff(); tag.iloc[0] = schluss.iloc[0] - 1.0
    out["tage_n"] = int(len(tag))
    out["tag_std"] = float(tag.std()); out["sharpe"] = float(tag.mean() / tag.std() * np.sqrt(365))
    out["schlechtester_tag"] = float(tag.min()); out["schlechtester_tag_datum"] = str(tag.idxmin().date())
    out["q01_tag"] = float(tag.quantile(0.01)); out["q001_tag"] = float(tag.quantile(0.001)); out["q05_tag"] = float(tag.quantile(0.05))
    out["es01_tag"] = float(tag[tag <= tag.quantile(0.01)].mean())
    # dieselben Tagesergebnisse relativ zum Kontostand des Vortags (so erlebt es der Kontoinhaber)
    vortag = schluss.shift(1); vortag.iloc[0] = 1.0
    rel = tag / vortag
    out["schlechtester_tag_rel"] = float(rel.min()); out["schlechtester_tag_rel_datum"] = str(rel.idxmin().date())
    out["q01_tag_rel"] = float(rel.quantile(0.01)); out["q001_tag_rel"] = float(rel.quantile(0.001))
    w = s.resample("W-SUN").last(); wd = w.diff(); wd.iloc[0] = w.iloc[0] - 1.0
    wv = w.shift(1); wv.iloc[0] = 1.0
    out["schlechteste_woche"] = float(wd.min()); out["schlechteste_woche_ende"] = str(wd.idxmin().date())
    out["schlechteste_woche_rel"] = float((wd / wv).min()); out["schlechteste_woche_rel_ende"] = str((wd / wv).idxmin().date())
    mo = s.resample("ME").last(); md = mo.diff(); md.iloc[0] = mo.iloc[0] - 1.0
    mv = mo.shift(1); mv.iloc[0] = 1.0
    out["schlechtester_monat"] = float(md.min()); out["schlechtester_monat_ende"] = str(md.idxmin().date())
    out["schlechtester_monat_rel"] = float((md / mv).min()); out["schlechtester_monat_rel_ende"] = str((md / mv).idxmin().date())
    out["monate_negativ"] = int((md < 0).sum()); out["monate"] = int(len(md))
    for name, n in (("1h", 12), ("24h", 288), ("7d", 2016), ("30d", 8640)):     # rollierend auf dem 5-Minuten-Raster
        d = konto[n:] - konto[:-n]
        i = int(d.argmin())
        out[f"roll_{name}"] = float(d[i]); out[f"roll_{name}_ende"] = str(ix[i + n])
        r = d / konto[:-n]
        i = int(r.argmin())
        out[f"roll_{name}_rel"] = float(r[i]); out[f"roll_{name}_rel_ende"] = str(ix[i + n])
    tief = s.resample("1D").min()
    intraday = tief - vortag
    out["schlechtester_tag_intraday"] = float(intraday.min()); out["schlechtester_tag_intraday_datum"] = str(intraday.idxmin().date())
    stunden = s.resample("1h").min()
    for sw in (0.5, 0.25, 0.0):
        unter = konto < sw
        out[f"unter_{int(sw * 100)}_tage"] = int((tief < sw).sum())
        out[f"unter_{int(sw * 100)}_stunden"] = int((stunden < sw).sum())
        out[f"unter_{int(sw * 100)}_erstmals"] = str(ix[int(np.argmax(unter))]) if unter.any() else None
    # Positionswert gegen Startkapital und gegen den laufenden Kontostand (effektiver Hebel)
    brutto = hebel * ex1
    out["positionswert_start"] = float(brutto[12]); out["positionswert_max"] = float(brutto.max()); out["positionswert_max_zeit"] = str(ix[int(brutto.argmax())])
    out["positionswert_median"] = float(np.median(brutto))
    eff = np.where(konto > 0, brutto / np.where(konto > 0, konto, 1.0), np.inf)
    out["eff_hebel_median"] = float(np.median(eff)); out["eff_hebel_p95"] = float(np.quantile(eff, 0.95)); out["eff_hebel_max"] = float(eff.max())
    out["eff_hebel_max_zeit"] = str(ix[int(eff.argmax())])
    out["anteil_zeit_eff_hebel_ueber_nominal"] = float((eff > hebel).mean())
    return out


def zeile(k):
    return (f"  Hebel {k['hebel']:.0f}: Ergebnis {k['ergebnis']:+8.1%} ({k['pro_jahr']:+7.1%}/Jahr, Sharpe {k['sharpe']:.2f}) | größter Einbruch {k['dd_rel']:6.1%} vom Höchststand "
            f"(Spitze {k['dd_rel_spitze'][:10]}, Tief {k['dd_rel_tief'][:16]}), größter Rückgang in Punkten des Startkapitals {k['dd_abs']:.1%} | tiefster Kontostand {k['konto_min']:.1%} am {k['konto_min_zeit'][:16]}\n"
            f"           in Punkten des Startkapitals: schlechtester Tag {k['schlechtester_tag']:+.1%} ({k['schlechtester_tag_datum']}), Tagestief gegen Vortagesschluss {k['schlechtester_tag_intraday']:+.1%} ({k['schlechtester_tag_intraday_datum']}); "
            f"Woche {k['schlechteste_woche']:+.1%} (bis {k['schlechteste_woche_ende']}); Monat {k['schlechtester_monat']:+.1%} (bis {k['schlechtester_monat_ende']}); negative Monate {k['monate_negativ']}/{k['monate']}\n"
            f"           relativ zum Kontostand davor: schlechtester Tag {k['schlechtester_tag_rel']:+.1%} ({k['schlechtester_tag_rel_datum']}); Woche {k['schlechteste_woche_rel']:+.1%} (bis {k['schlechteste_woche_rel_ende']}); "
            f"Monat {k['schlechtester_monat_rel']:+.1%} (bis {k['schlechtester_monat_rel_ende']}); 1-%-Quantil Tag {k['q01_tag_rel']:+.2%}, 0,1-%-Quantil {k['q001_tag_rel']:+.2%}\n"
            f"           rollierend (Punkte des Startkapitals): 1 h {k['roll_1h']:+.1%} ({k['roll_1h_ende'][:16]}), 24 h {k['roll_24h']:+.1%} ({k['roll_24h_ende'][:16]}), 7 Tage {k['roll_7d']:+.1%} ({k['roll_7d_ende'][:10]}), 30 Tage {k['roll_30d']:+.1%} ({k['roll_30d_ende'][:10]})\n"
            f"           rollierend (relativ zum Kontostand am Fensteranfang): 1 h {k['roll_1h_rel']:+.1%} ({k['roll_1h_rel_ende'][:16]}), 24 h {k['roll_24h_rel']:+.1%} ({k['roll_24h_rel_ende'][:16]}), 7 Tage {k['roll_7d_rel']:+.1%} ({k['roll_7d_rel_ende'][:10]}), 30 Tage {k['roll_30d_rel']:+.1%} ({k['roll_30d_rel_ende'][:10]})\n"
            f"           Tagesergebnis (Punkte des Startkapitals): Std {k['tag_std']:.2%}, 5-%-Quantil {k['q05_tag']:+.2%}, 1-%-Quantil {k['q01_tag']:+.2%}, 0,1-%-Quantil {k['q001_tag']:+.2%}, Mittel der schlechtesten 1 % {k['es01_tag']:+.2%} ({k['tage_n']} Tage)\n"
            f"           längste Zeit unter dem Höchststand {k['unter_wasser_tage']:.0f} Tage ({str(k['unter_wasser_von'])[:10]} bis {str(k['unter_wasser_bis'])[:10]}{', am Fensterende noch offen' if k['unter_wasser_offen_am_ende'] else ''})\n"
            f"           Positionswert / Startkapital: Start {k['positionswert_start']:.2f}, Median {k['positionswert_median']:.2f}, Maximum {k['positionswert_max']:.2f} ({k['positionswert_max_zeit'][:10]}); "
            f"Positionswert / laufendes Konto: Median {k['eff_hebel_median']:.2f}, 95-%-Quantil {k['eff_hebel_p95']:.2f}, Maximum {k['eff_hebel_max']:.2f} ({k['eff_hebel_max_zeit'][:10]}); Zeitanteil über Nennhebel {k['anteil_zeit_eff_hebel_ueber_nominal']:.0%}\n"
            f"           Konto < 50 % des Startkapitals: {k['unter_50_tage']} Tage / {k['unter_50_stunden']} Stunden (erstmals {k['unter_50_erstmals']}); "
            f"< 25 %: {k['unter_25_tage']} Tage / {k['unter_25_stunden']} Stunden (erstmals {k['unter_25_erstmals']}); "
            f"< 0 %: {k['unter_0_tage']} Tage / {k['unter_0_stunden']} Stunden (erstmals {k['unter_0_erstmals']})")


mv = R.markt(A, start=R.VOR_START, ende=R.VOR_ENDE, vor=True)
mh = R.markt(A, vor=True)
wv, wh = R.auf_raster(mv, M.basis(mv)), R.auf_raster(mh, M.basis(mh))
pos = lambda m, z: int(m.index.searchsorted(pd.Timestamp(z)))
FEN = {"Vorperiode 02/2020-08/2021": (mv, wv, 0, len(mv.index)),
       "Entwicklung 08/2021-03/2025": (mh, wh, 0, pos(mh, R.SPLIT)),
       "davon D1 08/2021-06/2023": (mh, wh, 0, pos(mh, R.D1_ENDE)),
       "davon D2 07/2023-03/2025": (mh, wh, pos(mh, R.D1_ENDE), pos(mh, R.SPLIT)),
       "Pruefzeitraum 04/2025-10/2026": (mh, wh, pos(mh, R.SPLIT), len(mh.index)),
       "Hauptzeitraum durchgehend 08/2021-10/2026": (mh, wh, 0, len(mh.index))}
print("KONTOVERLAUF DES KANDIDATEN (Gruppe A, 5-Minuten-Raster, frischer Start am Fensterbeginn, Konto = 1, feste Größe = Startkapital x Hebel / 10)")
print(f"Kosten: Taker {runner.TAKER:.4%} x (1 - Rebate {runner.MIT.rebate:.0%}) = {FEE:.4%} je Seite, Slippage je Coin aus der Yubit-Stichprobe.")
print("Ohne Zinseszins: Gewinne und Verluste in Punkten des Startkapitals. Vorperiode: bis 10/2020 handeln erst 5 bis 9 der zehn Coins (kleinerer Einsatz).")
print("Kein Liquidationsmodell: das Konto darf rechnerisch unter null fallen (wie im Rechenkern der Forschung und im Papier-Bot).")
for name, (m, w, a, b) in FEN.items():
    eq, ex = frisch(m, w, a, b, SLIP, FEE)
    print(f"\n{name}")
    OUT[name] = {}
    for h in (1.0, 3.0):
        k = fenster_stat(m.index[a:b], eq, ex, h)
        OUT[name][f"hebel_{h:.0f}"] = k
        print(zeile(k))
    if name.startswith("Pruefzeitraum"):      # zum Vergleich: so rechnet die Forschung (Positionen laufen aus der Entwicklung weiter)
        d = np.load(SCRATCH / "lauf_haupt.npz")
        e = d["eq1"][a:b] - d["eq1"][a - 1]
        print(f"  [Vergleich Forschung, durchlaufende Positionen] Ergebnis Hebel 1 {e[-1]:+.1%} ({e[-1] / ((b - a) / 288) * 365:+.1%}/Jahr); frischer Start {eq[-1]:+.1%}")
print(f"\nFenster fertig nach {time.time() - t0:.0f} s")

# ---------------------------------------------------------------- Start-Tag-Analyse ----
mg = R.markt(A, start=R.VOR_START, ende=R.ENDE, vor=True)
wg = R.auf_raster(mg, M.basis(mg))
tagstart = np.arange(0, len(mg.index), 288, dtype=np.int64)
HOR = {"30 Tage": 30, "90 Tage": 90, "180 Tage": 180, "365 Tage": 365}
cp = np.array([t * 288 for t in HOR.values()], dtype=np.int64)
mn, en = starts_sim(mg.o, mg.c, mg.fund, np.ascontiguousarray(wg, dtype=np.float64), np.ascontiguousarray(SLIP), FEE, tagstart, int(cp[-1]), cp)
print(f"\nStart-Tag-Simulation fertig nach {time.time() - t0:.0f} s ({len(tagstart)} Starttage, exakt neu gerechnet)")
np.savez_compressed(SCRATCH / "starttage.npz", start=mg.index[tagstart].as_unit("ns").asi8, mn=mn, en=en)
tage_idx = mg.index[tagstart]
gruppen = {"Vorperiode": (pd.Timestamp(R.VOR_START), pd.Timestamp(R.VOR_ENDE)), "Entwicklung": (pd.Timestamp(R.START), pd.Timestamp(R.SPLIT)),
           "Pruefzeitraum": (pd.Timestamp(R.SPLIT), pd.Timestamp(R.ENDE)), "alle": (pd.Timestamp(R.VOR_START), pd.Timestamp(R.ENDE))}
print("\nSTART-TAG-ANALYSE: Jeder Kalendertag (00:00 UTC) als möglicher Starttag eines neuen Kontos, alle Positionen frisch eröffnet.")
print("Tabelle: Anteil der Starttage, nach denen das Konto innerhalb des Horizonts mindestens einmal unter die Schwelle fällt (5-Minuten-Schlusskurse).")
print("Hinweis: Starttage überlappen sich stark (keine unabhängigen Stichproben); bis 10/2020 sind weniger als zehn Coins handelbar.")
OUT["starttage"] = {}
for h in (0.2, 1.0, 3.0, 5.0):
    print(f"\n  Hebel {h} ({'regelkonformer Hebel der Forschung, Runde 3' if h == 0.2 else 'Messbasis der Forschung' if h == 1.0 else 'Papier-Tests' if h == 3.0 else 'Obergrenze laut config.yaml / bot.konfig'})")
    for ci, hname in enumerate(HOR):
        for gname, (ga, gb) in gruppen.items():
            sel = (tage_idx >= ga) & (tage_idx < gb) & ~np.isnan(mn[:, ci])
            if not sel.any():
                continue
            tiefst = 1.0 + h * mn[sel, ci]
            endst = 1.0 + h * en[sel, ci]
            e = {"starttage": int(sel.sum()), "unter_50": float((tiefst < 0.5).mean()), "unter_25": float((tiefst < 0.25).mean()),
                 "unter_0": float((tiefst < 0.0).mean()), "median_tiefst": float(np.median(tiefst)), "p05_tiefst": float(np.quantile(tiefst, 0.05)),
                 "schlechtester": float(tiefst.min()), "schlechtester_start": str(tage_idx[sel][int(tiefst.argmin())].date()),
                 "median_ende": float(np.median(endst)), "anteil_ende_im_minus": float((endst < 1.0).mean())}
            OUT["starttage"][f"H{h}|{hname}|{gname}"] = e
            print(f"    {hname:8s} Starts {gname:13s} ({e['starttage']:4d}): < 50 % bei {e['unter_50']:5.1%}, < 25 % bei {e['unter_25']:5.1%}, < 0 % bei {e['unter_0']:5.1%}; "
                  f"tiefster Stand Median {e['median_tiefst']:4.0%}, schlechtestes Zwanzigstel {e['p05_tiefst']:5.0%}, schlechtester Start {e['schlechtester_start']} -> {e['schlechtester']:5.0%}; "
                  f"Endstand Median {e['median_ende']:4.0%}, Anteil Endstand im Minus {e['anteil_ende_im_minus']:4.0%}")
(SCRATCH / "s02.json").write_text(json.dumps(OUT, indent=1))
print(f"\nfertig nach {time.time() - t0:.0f} s")
