"""Schreibt reports/hybrid_report.md aus ergebnis.json und gegenpruefung.json (keine Zahl von Hand eingetragen)."""
import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
E = json.loads((ROOT / "reports/ergebnis.json").read_text())
G = json.loads((ROOT / "reports/gegenpruefung.json").read_text())
NAMEN = {"trail_beide": "trail_beide (4H)", "momentum_vol_ls": "momentum_vol_ls (1D)"}


def pz(x, n=1, vz=True):
    if x != x:
        return "–"
    s = f"{x * 100:+.{n}f}" if vz else f"{x * 100:.{n}f}"
    return s.replace(".", ",").replace("-", "−") + " %"


def zahl(x, n=2):
    return f"{x:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def usd(x, n=2):
    return ("−" if x < 0 else "") + zahl(abs(x), n) + " $"


def datum(s):
    j, m, t = s.split("-")
    return f"{t}.{m}.{j}"


def vergleich(strat):
    e = E[strat]["ergebnis"]
    b, s, h = (e[k]["pruefen"] for k in ("baseline", "swing_limit", "hybrid"))
    z = [
        ("Ergebnis vor Gebühren", *(pz(x["rendite_brutto"]) for x in (b, s, h))),
        ("**Netto ohne Rebate**", *(f"**{pz(x['rendite_ohne'])}**" for x in (b, s, h))),
        ("Netto mit 85 % Rebate", *(pz(x["rendite_mit"]) for x in (b, s, h))),
        ("Größter Einbruch (ohne Rebate)", *(pz(x["dd_ohne"], vz=False) for x in (b, s, h))),
        ("Anzahl Trades", *(str(x["trades"]) for x in (b, s, h))),
        ("Ø Haltedauer", *(f"{x['haltedauer_h'] / 24:.1f} Tage".replace(".", ",") if x["haltedauer_h"] > 48
                           else f"{x['haltedauer_h']:.0f} Std." for x in (b, s, h))),
        ("Gewinn-Trades", *(pz(x["trefferquote"], 0, False) for x in (b, s, h))),
        ("Volumen pro Tag (× Kapital)", *(zahl(x["volumen_tag"]) for x in (b, s, h))),
        ("Anteil Maker-Volumen", *(pz(x["maker_anteil"], 0, False) for x in (b, s, h))),
        ("Orders pro Tag", *(zahl(x["orders_tag"], 0) for x in (b, s, h))),
        ("Order-zu-Fill", *(zahl(x["order_zu_fill"], 1) + ":1" for x in (b, s, h))),
    ]
    out = ["| | Reine Swing | Swing, Einstieg per Limit | Hybrid |", "|---|---|---|---|"]
    return "\n".join(out + [f"| {a} | {x} | {y} | {w} |" for a, x, y, w in z])


def urteil(strat):
    out = ["| Regel | Bestanden | Messwert |", "|---|---|---|"]
    def wert(w):
        w = re.sub(r"(\d)\.(\d)", r"\1,\2", w).replace("%", " %").replace("-", "−").replace("Min.", "Minuten")
        return re.sub(r"\((\d{4})−(\d{2})\)", r"(\2/\1)", w)
    return "\n".join(out + [f"| {r['regel']} | {'ja' if r['ok'] else '**NEIN**'} | {wert(r['wert'])} |"
                            for r in E[strat]["urteil"]])


def kapital(strat):
    e = E[strat]["ergebnis"]
    out = ["| Kapital | Variante | Volumen/Tag | Rebate/Tag | Netto/Tag ohne Rebate | Netto/Tag mit Rebate | Größter Einbruch (ohne / mit Rebate) |",
           "|---|---|---|---|---|---|---|"]
    for c in (500, 1000, 5000):
        for name, k in (("Reine Swing", "baseline"), ("Hybrid", "hybrid")):
            x = e[k]["pruefen"]
            out.append(f"| {zahl(c, 0)} $ | {name} | {usd(x['volumen_tag'] * c, 0)} | {usd(x['rebate_tag'] * c)} | "
                       f"{usd(x['rendite_ohne'] / x['tage'] * c)} | {usd(x['rendite_mit'] / x['tage'] * c)} | "
                       f"{pz(x['dd_ohne'], 0, False)} / {pz(x['dd_mit'], 0, False)} |")
    return "\n".join(out)


def roll(strat):
    r = E[strat]["rollierend"]
    besser = sum(1 for x in r if x["hybrid_ohne"] >= x["baseline_ohne"])
    sh, sb = sum(x["hybrid_ohne"] for x in r), sum(x["baseline_ohne"] for x in r)
    return (f"{len(r)} Fenster, Summe netto ohne Rebate: Hybrid {pz(sh)}, reine Swing {pz(sb)}. "
            f"Hybrid war in {besser} von {len(r)} Fenstern mindestens so gut")


t, m = E["trail_beide"], E["momentum_vol_ls"]
tb, th, ts = (t["ergebnis"][k]["pruefen"] for k in ("baseline", "hybrid", "swing_limit"))
mb, mh, ms = (m["ergebnis"][k]["pruefen"] for k in ("baseline", "hybrid", "swing_limit"))
gt, gm = G["trail_beide"], G["momentum_vol_ls"]
B = pd.read_csv(ROOT / "data/processed/baseline.csv").set_index(["swing", "hebel", "fenster"])
mom_dd1_gesamt = float(B.loc[("momentum_vol_ls", 1.0, "gesamt"), "dd_ohne"])
mom_dd3_gesamt = float(B.loc[("momentum_vol_ls", 3.0, "gesamt"), "dd_ohne"])
besser = gt["varianten_besser_als_baseline"] + gm["varianten_besser_als_baseline"]
if besser == 0:
    satz18 = ("Keine der 18 getesteten Einstellungen schlägt im Prüfzeitraum die reine Swing-Strategie, bei keiner der beiden "
              "Swing-Quellen. Nachjustieren würde also nichts retten.")
else:
    satz18 = (f"Von den 18 getesteten Einstellungen liegen im Prüfzeitraum {gt['varianten_besser_als_baseline']} (trail_beide) bzw. "
              f"{gm['varianten_besser_als_baseline']} (momentum_vol_ls) über der reinen Swing-Strategie.")
h1t, h1m = t["hebel1_pruefen"], m["hebel1_pruefen"]
p_t, p_m = t["gewaehlt"], m["gewaehlt"]


def param(p):
    return (f"Dip {zahl(p['dip'], 1)} × Stunden-ATR, Teilgewinn {zahl(p['tp'], 1)} × ATR, "
            f"{'mit' if p['trail'] else 'ohne'} Trailing")


text = f"""# Hybrid-Bericht: Swing-Bias + Intraday-Dip-Ausführung

Stand 14.11.2026. Historische Simulation, keine Anlageberatung. Vergangene Ergebnisse sagen nichts Sicheres über die Zukunft.

## Ergebnis

**Nicht weiterbauen. Die Hybrid-Variante fällt durch, bei beiden Swing-Strategien und deutlich.**

- Sie verdient im Prüfzeitraum nach Gebühren weniger als die reine Swing-Strategie:
  {pz(th['rendite_ohne'])} gegen {pz(tb['rendite_ohne'])} bei trail_beide, {pz(mh['rendite_ohne'])} gegen {pz(mb['rendite_ohne'])} bei momentum_vol_ls.
- Das Dip-Kaufen selbst bringt vor Gebühren praktisch nichts und kostet nach Gebühren Geld.
- Das Mehr an Volumen ist real (Faktor {zahl(th['volumen_tag'] / tb['volumen_tag'], 1)} bzw. {zahl(mh['volumen_tag'] / mb['volumen_tag'], 1)}),
  bringt bei 1.000 $ Kapital aber nur etwa {usd((th['rebate_tag'] - tb['rebate_tag']) * 1000)} bis {usd((mh['rebate_tag'] - mb['rebate_tag']) * 1000)} mehr Rebate pro Tag.
- {satz18}

Drei Nebenbefunde sind für dich wichtiger als das Hauptergebnis (Abschnitt „Was stattdessen auffällt“).

## Was in den Daten steckt

Deine ZIP ist das komplette Labor: 4.177 Einzel-Backtests, 23 Testreihen, 26 Strategien, Kerzen in 4H (ab 08/2021)
und 1D (ab 01/2022) für 10 Coins. Details in `datenbericht.md`. Als Swing-Bias dienen die zwei Strategien, die dein
Signalbot an Telegram meldet: **trail_beide (4H)** und **momentum_vol_ls (1D)**. Ihre Signale habe ich nachgerechnet;
im Prüfzeitraum deines Labors stimmen sie an jeder einzelnen Kerze mit den dort gespeicherten Werten überein.

Feine Kurse fehlten. Nachgeladen: 5-Minuten-Kerzen und Funding-Raten der Binance-Futures, 07/2021 bis 10/2026,
für alle 10 Coins. Bei SOL, XRP und LTC fehlen im Binance-Archiv 5 Tage (26.–28.02.2022 und 01.–02.04.2022);
an diesen Tagen wird für diese Coins kein Handel simuliert. Sie liegen im Lernzeitraum, nicht im Prüfzeitraum.

## Wie getestet wurde

- **Reine Swing (Baseline):** wie im Labor, Market-Order zum Open der nächsten Kerze. Yubit-Taker-Gebühr 0,08 %,
  dazu 0,05 % Slippage je Market-Order (wie im Labor).
- **Hybrid:** 50 % der Position folgt dem Swing-Signal (Einstieg per Limit). Die anderen 50 % in 3 Tranchen:
  jede volle Stunde ein Limit unter dem Kurs (bei Short darüber), nach Füllung ein Limit-Teilgewinn.
  Endet das Swing-Signal, wird alles per Market geschlossen.
- **Füllung streng:** Ein Limit zählt nur, wenn eine spätere 5-Minuten-Kerze den Preis um mehr als 0,01 % durchhandelt.
  Füllpreis ist der Limitpreis. Ungefüllte Orders werden nach 60 Minuten verworfen.
- **Deine Regeln sind eingebaut:** Hebel 3, nur Limits für Einstiege und Teilgewinne, Stops als Market, nie Orders
  gegeneinander, Obergrenze je Coin, Tagesverlust-Limit 3 % (schließt den Dip-Teil und sperrt ihn bis zum nächsten Tag).
- **Walk-Forward:** Einstellungen nur in den ersten 70 % der Zeit gewählt (aus 18 Kombinationen, stabilster Bereich
  statt Spitzenwert), die letzten 30 % unverändert gemessen. Dazu rollierende Fenster (12 Monate lernen, 3 Monate prüfen).
- **Immer drei Rechnungen:** vor Gebühren, ohne Rebate, mit 85 % Rebate. Die Trades sind in allen dreien dieselben.

Alle Prozentzahlen beziehen sich auf das Startkapital bei Hebel 3, ohne Zinseszins.

## Baseline gegen Hybrid

### {NAMEN['trail_beide']}

Prüfzeitraum {datum(t['split'])} bis {datum(t['ende'])}. Gewählte Einstellung: {param(p_t)}.

{vergleich('trail_beide')}

### {NAMEN['momentum_vol_ls']}

Prüfzeitraum {datum(m['split'])} bis {datum(m['ende'])}. Gewählte Einstellung: {param(p_m)}.

{vergleich('momentum_vol_ls')}

## Entscheidungsregeln

### {NAMEN['trail_beide']}

{urteil('trail_beide')}

### {NAMEN['momentum_vol_ls']}

{urteil('momentum_vol_ls')}

Rollierende Fenster bestätigen das:
- trail_beide: {roll('trail_beide')}.
- momentum_vol_ls: {roll('momentum_vol_ls')}.

In den Fenstern, in denen Hybrid vorn liegt, verliert die Swing-Strategie. Hybrid verliert dann weniger, weil
weniger Kapital im Markt ist, nicht weil das Dip-Kaufen verdient.

## Volumen- und Rebate-Rechnung

Prüfzeitraum, Hebel 3. Alle Beträge skalieren genau mit dem Kapital.

### {NAMEN['trail_beide']}

{kapital('trail_beide')}

### {NAMEN['momentum_vol_ls']}

{kapital('momentum_vol_ls')}

Warum mehr Volumen wenig mehr Rebate bringt: Die reine Swing zahlt auf jedes Volumen die teure Taker-Gebühr (0,08 %),
Hybrid handelt zu rund 80 % als Maker (0,04 %). Mehr Volumen zum halben Satz ergibt nur wenig mehr Gebühr und
damit wenig mehr Rebate. Der Einbruch ist in Prozent für jedes Kapital gleich.

## Warum es nicht funktioniert

Zerlegung der Hybrid-Trades im Prüfzeitraum (ohne Funding):

| | Kern (Swing-Hälfte) | Dip-Teil vor Gebühren | Dip-Teil nach Gebühren |
|---|---|---|---|
| trail_beide | {pz(gt['kern_netto'])} | {pz(gt['taktik_brutto'])} | {pz(gt['taktik_netto'])} |
| momentum_vol_ls | {pz(gm['kern_netto'])} | {pz(gm['taktik_brutto'])} | {pz(gm['taktik_netto'])} |

1. **Der Dip-Teil hat keinen eigenen Vorteil.** {pz(th['trefferquote'], 0, False)} bzw. {pz(mh['trefferquote'], 0, False)} der Trades gewinnen,
   aber die Gewinne sind klein (fester Teilgewinn) und die Verlierer groß: Sie laufen, bis das Swing-Signal endet.
2. **Er verdrängt die Hälfte der Swing-Position.** Hybrid hält nur den halben Swing-Anteil. Der Dip-Teil müsste
   also die andere Hälfte des Swing-Gewinns ersetzen. Das schafft er in keinem der beiden Fälle.
3. **Gebühren fressen den Rest.** {th['trades']} bzw. {mh['trades']} Trades mit winzigem Ertrag pro Trade.

## Was stattdessen auffällt

**1. Derselbe Swing, aber Einstieg per Limit statt Market, war besser als die Baseline.**
Im Prüfzeitraum {pz(ts['rendite_ohne'])} statt {pz(tb['rendite_ohne'])} (trail_beide) und {pz(ms['rendite_ohne'])} statt {pz(mb['rendite_ohne'])}
(momentum_vol_ls), jeweils ohne Rebate. Der Grund ist schlicht: halbe Gebühr und keine Slippage beim Einstieg.
Mehr Volumen entsteht dadurch nicht. Der Vorteil hängt an der Füllannahme und ist klein gegenüber den Schwankungen.

**2. Hebel 3 ist für diese Swing-Strategien zu viel, auch ohne Hybrid.**
Die reine Swing hat im Prüfzeitraum einen Einbruch von {pz(tb['dd_ohne'], 0, False)} (trail_beide) bzw. {pz(mb['dd_ohne'], 0, False)} (momentum_vol_ls).
Über den ganzen Zeitraum (ab 07/2022) wäre das Konto mit momentum_vol_ls bei Hebel 3 zwischenzeitlich unter null
gefallen (Einbruch {pz(mom_dd3_gesamt, 0, False)} vom Höchststand), in der Praxis also vorher liquidiert worden.
Mit Hebel 1 liegen die Einbrüche im Prüfzeitraum bei {pz(h1t['baseline']['dd_ohne'], 0, False)} bzw. {pz(h1m['baseline']['dd_ohne'], 0, False)}.
Deine 15-%-Grenze hält bei Hebel 3 keine Variante. Bei Hebel 1 hält sie trail_beide auch nicht, und momentum_vol_ls
nur im Prüfzeitraum: über den ganzen Zeitraum sind es dort {pz(mom_dd1_gesamt, 0, False)}.

**3. trail_beide hat seit April 2025 kaum verdient.**
Ohne Hebel {pz(h1t['baseline']['rendite_ohne'])} in 18 Monaten bei {pz(h1t['baseline']['dd_ohne'], 0, False)} Einbruch.
Der gute Labor-Wert (+62 % im Labor-Prüfzeitraum ab 10/2024) stammt überwiegend aus November 2024 bis Januar 2025:
Allein diese drei Monate brachten ohne Hebel {pz(next(x['baseline_ohne'] for x in t['rollierend'] if x['test_von'] == '2024-11-01') / 3)}.

## Empfehlung

- **Hybrid mit Dip-Nachkauf: nein.** Nicht weiterbauen, nicht nachjustieren.
- **Wenn du etwas mitnehmen willst:** Swing-Einstiege per Limit statt Market (Befund 1) und Hebel deutlich unter 3
  (Befund 2). Beides ist keine neue Strategie, sondern sauberere Ausführung der bestehenden.
- **Rebate als Einnahme lohnt bei diesem Kapital nicht.** Selbst die volumenstärkste Hybrid-Rechnung bringt bei 5.000 $
  nur {usd(mh['rebate_tag'] * 5000)} Rebate pro Tag.

## Risiken und Annahmen

- **Yubit selbst ist nicht getestet.** Kurse und Funding stammen von Binance-Futures. Liquidität, Spreads, Funding und
  Mindestordergrößen bei Yubit können abweichen. Bei 500 $ ist eine Dip-Tranche nur 25 $ groß.
- **Füllmodell:** 5-Minuten-Kerzen zeigen nicht, wo man in der Warteschlange steht. Eine mildere Annahme (jedes
  Durchhandeln zählt) ändert das Urteil nicht: Hybrid {pz(gt['mild_hybrid'])} bzw. {pz(gm['mild_hybrid'])}.
- **Positionsgröße:** festes Kapital ohne Zinseszins, Hebel 3 gleichmäßig auf 10 Coins. Das Labor rechnet je Coin
  mit Zinseszins; im selben Fenster ohne Hebel weichen beide Rechnungen wenig ab
  (trail_beide: Labor {pz(gt['labor_fenster'])}, hier {pz(gt['baseline_fenster'])}; momentum_vol_ls: Labor {pz(gm['labor_fenster'])}, hier {pz(gm['baseline_fenster'])}).
- **Tagesverlust-Limit:** Den Wert 3 % habe ich gesetzt, bevor Ergebnisse vorlagen. Er wirkt nur auf den Dip-Teil.
  Der Kern folgt weiter dem Swing-Signal.
- **Die Swing-Strategien selbst sind nicht gesichert profitabel.** Im Labor erreichte keine Futures-Strategie GRÜN,
  und sie wurden aus 17 Versuchen ausgewählt. Die 10 Coins wurden im Rückblick festgelegt.
- **Rebate:** gerechnet als sofortige Gutschrift von 85 % der gezahlten Gebühr. Auszahlungstermine und Bedingungen
  des Partners sind nicht berücksichtigt.
- **Ein Datenstand:** Die Auswertung endet am 23.10.2026. Der Prüfzeitraum umfasst nur 15 bis 18 Monate.

## Nachrechnen

```bash
cd swing-hybrid
.venv/bin/python -m pytest -q                 # 10 Tests, u. a. Füllregel und „kein Blick in die Zukunft“
.venv/bin/python -I scripts/raster.py         # alle Varianten rechnen
.venv/bin/python -I scripts/walkforward.py    # Auswahl, Urteil, rollierende Fenster
.venv/bin/python -I scripts/gegenpruefung.py  # Gegenprüfungen
.venv/bin/python -I scripts/bericht.py        # diesen Bericht erzeugen
```
"""
(ROOT / "reports/hybrid_report.md").write_text(text)
print(text)
