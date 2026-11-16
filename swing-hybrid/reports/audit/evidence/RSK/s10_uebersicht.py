"""RSK 10: Übersichtstabellen aus den JSON-Zwischenergebnissen von s02 bis s07 (keine neue Rechnung)."""
import json
import os
import sys
import tempfile
from pathlib import Path

SCR = Path(os.environ.get("RSK_SCRATCH", str(Path(tempfile.gettempdir()) / "rsk_audit")))
J = {n: json.loads((SCR / f"{n}.json").read_text()) for n in ("s02", "s03", "s04", "s05", "s06", "s07")}
p = lambda x, n=1: f"{x * 100:+.{n}f} %".replace(".", ",")
u = lambda x, n=1: f"{x * 100:.{n}f} %".replace(".", ",")

print("TABELLE 1: Kandidat (14-Tage-Trend, Gruppe A), frischer Start am Fensterbeginn, feste Größe, kein Tageslimit, Yubit-Kosten mit Rebate")
print("Alle Verluste in Punkten des Startkapitals (ohne Zinseszins), außer 'Einbruch vom Höchststand'.")
print("| Zeitraum | Hebel | Ergebnis/Jahr | Sharpe | Einbruch vom Höchststand | größter Rückgang (Punkte) | schlechtester Tag | schlechteste Woche | schlechtester Monat | 1-%-Quantil Tag | 0,1-%-Quantil Tag | längste Zeit unter Höchststand | tiefster Kontostand |")
print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
for f in ("Vorperiode 02/2020-08/2021", "Entwicklung 08/2021-03/2025", "Pruefzeitraum 04/2025-10/2026"):
    for h in ("hebel_1", "hebel_3"):
        k = J["s02"][f][h]
        print(f"| {f} | {h[-1]} | {p(k['pro_jahr'])} | {k['sharpe']:.2f} | {u(k['dd_rel'])} | {u(k['dd_abs'])} | {p(k['schlechtester_tag'])} ({k['schlechtester_tag_datum']}) | {p(k['schlechteste_woche'])} | "
              f"{p(k['schlechtester_monat'])} | {p(k['q01_tag'])} | {p(k['q001_tag'])} | {k['unter_wasser_tage']:.0f} Tage | {u(k['konto_min'])} |")

print("\nTABELLE 2: Start-Tag-Analyse. Anteil der Starttage (jeder Kalendertag 02/2020 bis 10/2026, frischer Start), nach denen das Konto im Horizont unter die Schwelle fällt")
print("| Hebel | Horizont | Starttage | Konto < 50 % | Konto < 25 % | Konto < 0 % | tiefster Stand (Median) | tiefster Stand (schlechtestes Zwanzigstel) |")
print("|---|---|---|---|---|---|---|---|")
for h in ("0.2", "1.0", "3.0", "5.0"):
    for hor in ("30 Tage", "90 Tage", "180 Tage", "365 Tage"):
        k = J["s02"]["starttage"][f"H{h}|{hor}|alle"]
        print(f"| {h.replace('.', ',')} | {hor} | {k['starttage']} | {u(k['unter_50'])} | {u(k['unter_25'])} | {u(k['unter_0'])} | {u(k['median_tiefst'], 0)} | {u(k['p05_tiefst'], 0)} |")
print("\nDasselbe für Hebel 3 getrennt nach Lage des Starttags:")
print("| Starttag in | Horizont | Starttage | Konto < 50 % | Konto < 25 % | Konto < 0 % |")
print("|---|---|---|---|---|---|")
for g in ("Vorperiode", "Entwicklung", "Pruefzeitraum"):
    for hor in ("30 Tage", "90 Tage", "180 Tage", "365 Tage"):
        k = J["s02"]["starttage"][f"H3.0|{hor}|{g}"]
        print(f"| {g} | {hor} | {k['starttage']} | {u(k['unter_50'])} | {u(k['unter_25'])} | {u(k['unter_0'])} |")

print("\nTABELLE 3: ANNAHME gemeinsame Margin (Cross), Hebel 3: Anteil der Starttage mit Liquidation des ganzen Kontos (Kontostand <= MMR x Positionswert)")
print("| Horizont | Starttage | MMR 0,5 % | MMR 1 % | MMR 2,5 % |")
print("|---|---|---|---|---|")
for hor in ("30 Tage", "90 Tage", "180 Tage", "365 Tage"):
    k = J["s07"]["cross_starttage"][f"H3.0|{hor}|alle"]
    print(f"| {hor} | {k['starttage']} | {u(k['mmr_0.005'])} | {u(k['mmr_0.01'])} | {u(k['mmr_0.025'])} |")

print("\nTABELLE 4: ANNAHME isolierte Margin: Haltephasen des Kandidaten (13.571 in 6,7 Jahren), die liquidiert worden wären")
print("| Börsenhebel | MMR | Distanz | Trades (5-Minuten-Hochs/-Tiefs) | pro Jahr | nur Schlusskurse | Vorperiode / Entwicklung / Prüfzeitraum |")
print("|---|---|---|---|---|---|---|")
for L in (3, 5, 10, 20):
    for m in ("0.005", "0.025"):
        k = J["s07"]["isoliert_trades"][f"L{L}|mmr{m}"]
        jf = k["je_fenster"]
        print(f"| {L}x | {u(float(m))} | {u(k['distanz'])} | {k['trades']} | {k['pro_jahr']:.1f} | {k['trades_schluss']} | {jf.get('Vorperiode', 0)} / {jf.get('Entwicklung', 0)} / {jf.get('Pruefzeitraum', 0)} |")

print("\nTABELLE 5: Korrelation und Konzentration")
print("| Zeitraum | mittlere Korrelation Coins (Tag) | effektive Wetten Coins | mittlere Korrelation Positions-Ergebnisse | effektive Wetten Positionen | alle zehn gleichgerichtet | mind. acht gleich | Beta zum Korb bei >= 9 Long | bei >= 9 Short | Anteil Streuung aus Richtungswette |")
print("|---|---|---|---|---|---|---|---|---|---|")
for f in ("Vorperiode", "Entwicklung", "Pruefzeitraum"):
    k = J["s04"][f]
    print(f"| {f} | {k['coins_Tagesrenditen']['mittlere_korrelation']:.2f} | {k['coins_Tagesrenditen']['neff_formel']:.2f} | {k['positionen_tagesergebnis']['mittlere_korrelation']:.2f} | "
          f"{k['positionen_tagesergebnis']['neff_formel']:.2f} | {u(k['richtungen']['anteil_alle_zehn_gleich'])} | {u(k['richtungen']['anteil_mind_acht_gleich'])} | "
          f"{k['beta']['beta_korb_netto_long_ab_0.8']:+.2f} | {k['beta']['beta_korb_netto_short_ab_0.8']:+.2f} | {u(k['beta']['r2_richtungswette'], 0)} |")

print("\nTABELLE 6: Gleichzeitige Verluste (durchlaufender Lauf, Hebel 1; Hebel 3 = dreifach)")
print("| Zeitraum | Fenster | alle zehn im Verlust | mind. acht im Verlust | Verlustanteil aus Fenstern mit mind. acht Verlierern | größter Verlust Hebel 1 | Hebel 3 | Beginn |")
print("|---|---|---|---|---|---|---|---|")
for f in ("Vorperiode", "Entwicklung", "Pruefzeitraum"):
    for w in ("1 Stunde (volle Stunden)", "24 Stunden (rollierend, Stundenschritt)", "Kalendertag"):
        k = J["s03"][f][w]
        print(f"| {f} | {w} | {u(k['anteil_alle_zehn_verlieren'])} | {u(k['anteil_mind_acht_verlieren'])} | {u(k['verlustanteil_aus_fenstern_mit_mind_acht_verlierern'], 0)} | {p(k['groesster_verlust_h1'])} | {p(3 * k['groesster_verlust_h1'])} | {k['groesster_verlust_zeit'][:16]} |")

print("\nTABELLE 7: Test 2 (Bot-Logik mit Stop 5 % / Ziel 15 %), Hebel 3, je Prüfabstand")
print("| Zeitraum | Lauf | Ergebnis | Sharpe | Einbruch vom Höchststand | tiefster Stand | Stops | Verlust am Stop (Mittel) | schlechtester Stop | Stops schlechter als −10 % |")
print("|---|---|---|---|---|---|---|---|---|---|")
for f in ("Vorperiode", "Entwicklung", "Pruefzeitraum"):
    for l, k in J["s05"][f].items():
        st = f"{k['stops']} | {p(k['stop_mittel'], 2)} | {p(k['stop_schlechtester'])} | {k['stops_schlechter_10']}" if "stops" in k else "– | – | – | –"
        print(f"| {f} | {l} | {p(k['ergebnis'])} | {k['sharpe']:.2f} | {u(k['dd_rel'])} | {u(k['konto_min'], 0)} | {st} |")

print("\nTABELLE 8: Funding (Binance-Sätze), Hebel 1; Hebel 3 = dreifach")
print("| Zeitraum | Funding pro Jahr | schlechteste 30 Tage | schlechteste 90 Tage | Position zahlt (Anteil der Abrechnungen) | zahlt mind. 0,03 % | mittlerer Satz wenn Long | wenn Short |")
print("|---|---|---|---|---|---|---|---|")
for f in ("Vorperiode", "Entwicklung", "Pruefzeitraum"):
    k, a = J["s06"][f], J["s06"]["abrechnungen"][f]
    print(f"| {f} | {p(k['funding_pro_jahr_h1'], 2)} | {p(k['schlechteste_30_tage_h1'], 2)} | {p(k['schlechteste_90_tage_h1'], 2)} | {u(a['anteil_position_zahlt'], 0)} | {u(a['anteil_hoch_gegen_position'])} | "
          f"{p(a['mittlere_rate_long'], 4)} | {p(a['mittlere_rate_short'], 4)} |")
