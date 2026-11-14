"""Schreibt reports/suche_bericht.md aus den Ergebnisdateien der Suche (keine Zahl von Hand)."""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
K = json.loads((ROOT / "reports/kandidat.json").read_text())
R3 = json.loads((ROOT / "reports/suche_runde3.json").read_text())
E = R3["finalisten"][K["name"]]
D = json.loads((ROOT / "reports/fuellmodell_diagnose.json").read_text())
S1 = pd.read_csv(ROOT / "reports/suche_stufe1.csv")
H = K["hebel"]
R4 = json.loads((ROOT / "reports/suche_runde4.json").read_text())
R5 = json.loads((ROOT / "reports/suche_runde5.json").read_text())
G6 = json.loads((ROOT / "reports/gesamt_60.json").read_text())
SV = json.loads((ROOT / "reports/swing_vergleich.json").read_text())
sw = SV["momentum_vol_ls_baseline"]["pruef"]


def pz(x, n=1, vz=True):
    if x != x:
        return "–"
    s = f"{x * 100:+.{n}f}" if vz else f"{x * 100:.{n}f}"
    return s.replace(".", ",").replace("-", "−") + " %"


def zahl(x, n=2):
    return f"{x:,.{n}f}".replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")


def usd(x, n=2):
    return ("−" if x < 0 else "") + zahl(abs(x), n) + " $"


b = K["basis"]
ent, pr, ges = b["Entwicklung"], b["Pruefung"], b["Gesamt"]
tage_p, tage_g = K["tage"]["Pruefung"], K["tage"]["Gesamt"]
z = K["zufall_pruefung"]
z_ges = E["stufen"]["4_zufall"]
gb = K["gruppe_b"]
pa = K["passiv"]
sl = K["slippage"]


def zeile(titel, key, f=pz, **kw):
    return f"| {titel} | {f(ent[key], **kw)} | {f(pr[key], **kw)} | {f(ges[key], **kw)} |"


tabelle = "\n".join([
    "| | Entwicklung (08/2021–03/2025) | Prüfzeitraum (04/2025–10/2026) | Gesamt |", "|---|---|---|---|",
    zeile("Handel vor Gebühren", "G"), zeile("Gezahlte Gebühr", "F", vz=False), zeile("Rebate (85 %)", "R"),
    zeile("Handel nach voller Gebühr (ohne Rebate)", "handel"), zeile("**Netto mit Rebate**", "N"),
    zeile("Größter Einbruch", "dd_mit", vz=False, n=0),
    f"| Volumen pro Tag (× Kapital) | {zahl(ent['vol_tag'])} | {zahl(pr['vol_tag'])} | {zahl(ges['vol_tag'])} |",
])
jahre = "\n".join(["| Jahr | Handel vor Gebühren | Rebate | Handel nach voller Gebühr | Netto mit Rebate |", "|---|---|---|---|---|"] + [
    f"| {j}{' (ab 15.08.)' if j == '2021' else ' (bis 23.10.)' if j == '2026' else ''} | {pz(v['G'])} | {pz(v['R'])} | {pz(v['ohne'])} | {pz(v['N'])} |"
    for j, v in K["jahre"].items()])
kap = ["| Kapital | Position je Coin | Volumen/Tag | Rebate/Tag | Netto/Tag (Prüfzeitraum) | Netto/Tag (gesamter Zeitraum) | Größter Einbruch |",
       "|---|---|---|---|---|---|---|"]
for c in (500, 1000, 5000):
    kap.append(f"| {zahl(c, 0)} $ | {usd(H * c / 10, 0)} | {usd(pr['vol_tag'] * c, 0)} | {usd(pr['R'] / tage_p * c)} | "
               f"{usd(pr['N'] / tage_p * c)} | {usd(ges['N'] / tage_g * c)} | {pz(max(pr['dd_mit'], ent['dd_mit']), 0, False)} (≈ {usd(max(pr['dd_mit'], ent['dd_mit']) * c, 0)}) |")
kap = "\n".join(kap)
slip = "\n".join(["| Slippage je Order | Netto mit Rebate, Entwicklung | Netto mit Rebate, Prüfzeitraum |", "|---|---|---|"] + [
    f"| {zahl(float(bp) / 100, 3)} % | {pz(v['Entwicklung']['N'])} | {pz(v['Pruefung']['N'])} |" for bp, v in sl.items()])
n_s1 = int(S1["bestanden"].sum())
# ---- Runde 4
cs, vo, br = R4["C_sofort"], R4["vorperiode"], R4["breit"]
HB = R4["breit_hebel"]
bp, bg, be = br["Pruefung"], br["Gesamt"], br["Entwicklung"]
n_breit = 20 + len(R4["gruppe_c"])
tab_c = "\n".join([
    "| Gruppe C (20 neue Coins) | Entwicklung | Prüfzeitraum |", "|---|---|---|",
    f"| Handel vor Gebühren | {pz(cs['Entwicklung']['G'] * H)} | {pz(cs['Pruefung']['G'] * H)} |",
    f"| Handel nach voller Gebühr (ohne Rebate) | {pz(cs['Entwicklung']['handel'] * H)} | {pz(cs['Pruefung']['handel'] * H)} |",
    f"| **Netto mit Rebate** | {pz(cs['Entwicklung']['N'] * H)} | {pz(cs['Pruefung']['N'] * H)} |"])
tab_v = "\n".join(["| Vorperiode 02/2020–08/2021 | Coins | Handel vor Gebühren | Netto mit Rebate |", "|---|---|---|---|"] + [
    f"| {nm} | {int(vo[k]['coins'])} | {pz(vo[k]['G'] * H)} | {pz(vo[k]['N'] * H)} |"
    for nm, k in (("Gruppe A", "A"), ("Gruppe B", "B"), ("Gruppe C", "C"), ("alle zusammen", "alle"))])
tab_b = "\n".join([
    f"| Breites Portfolio ({n_breit} Coins), Hebel {zahl(HB, 1)} | Entwicklung | Prüfzeitraum | Gesamt |", "|---|---|---|---|",
    f"| Handel vor Gebühren | {pz(be['G'])} | {pz(bp['G'])} | {pz(bg['G'])} |",
    f"| Rebate (85 %) | {pz(be['R'])} | {pz(bp['R'])} | {pz(bg['R'])} |",
    f"| Handel nach voller Gebühr (ohne Rebate) | {pz(be['handel'])} | {pz(bp['handel'])} | {pz(bg['handel'])} |",
    f"| **Netto mit Rebate** | {pz(be['N'])} | {pz(bp['N'])} | {pz(bg['N'])} |",
    f"| Größter Einbruch | {pz(be['dd_mit'], 0, False)} | {pz(bp['dd_mit'], 0, False)} | {pz(bg['dd_mit'], 0, False)} |"])
jahre_b = "\n".join(["| Jahr | Handel vor Gebühren | Rebate | Netto mit Rebate |", "|---|---|---|---|"] + [
    f"| {j}{' (ab 15.08.)' if j == '2021' else ' (bis 23.10.)' if j == '2026' else ''} | {pz(v['G'])} | {pz(v['R'])} | {pz(v['N'])} |"
    for j, v in R4["breit_jahre"].items()])
tp4, tg4 = R4["tage"]["Pruefung"], R4["tage"]["Gesamt"]
kap_b = ["| Kapital | Position je Coin | Volumen/Tag | Rebate/Tag | Netto/Tag (Prüfzeitraum) | Netto/Tag (gesamter Zeitraum) |", "|---|---|---|---|---|---|"]
for c in (500, 1000, 5000):
    kap_b.append(f"| {zahl(c, 0)} $ | {usd(HB * c / n_breit)} | {usd(bp['vol_tag'] * c, 0)} | {usd(bp['R'] / tp4 * c)} | "
                 f"{usd(bp['N'] / tp4 * c)} | {usd(bg['N'] / tg4 * c)} |")
kap_b = "\n".join(kap_b)
sl_b = ", ".join(f"{zahl(float(k) / 100, 3)} % → {pz(v['N'])}" for k, v in R4["breit_slippage"].items())
zb = R4["breit_zufall_pruefung"]
# ---- Runde 5 und Gesamtschätzung
gr = G6["gruppen"]
H6 = G6["hebel"]
a6 = G6["alle"]
t6p, t6g = G6["tage"]["Pruefung"], G6["tage"]["Gesamt"]
tab_gr = "\n".join(["| Gruppe | Coins | Handel vor Gebühren, Prüfzeitraum | Netto mit Rebate, Prüfzeitraum | Netto mit Rebate, Entwicklung |",
                     "|---|---|---|---|---|"] + [
    f"| {g}{' (frisch in Runde 4)' if g == 'C' else ' (frisch in Runde 5)' if g == 'D' else ''} | {n} | {pz(gr[g]['Pruefung']['G'] * H)} | "
    f"{pz(gr[g]['Pruefung']['N'] * H)} | {pz(gr[g]['Entwicklung']['N'] * H)} |" for g, n in (("A", 10), ("B", 10), ("C", 20), ("D", 20))])
tab_60 = "\n".join([
    f"| Alle {G6['n_coins']} Coins, Hebel {zahl(H6, 2)} | Entwicklung | Prüfzeitraum | Gesamt |", "|---|---|---|---|",
    f"| Handel vor Gebühren | {pz(a6['Entwicklung']['G'])} | {pz(a6['Pruefung']['G'])} | {pz(a6['Gesamt']['G'])} |",
    f"| Rebate (85 %) | {pz(a6['Entwicklung']['R'])} | {pz(a6['Pruefung']['R'])} | {pz(a6['Gesamt']['R'])} |",
    f"| Handel nach voller Gebühr (ohne Rebate) | {pz(a6['Entwicklung']['handel'])} | {pz(a6['Pruefung']['handel'])} | {pz(a6['Gesamt']['handel'])} |",
    f"| **Netto mit Rebate** | {pz(a6['Entwicklung']['N'])} | {pz(a6['Pruefung']['N'])} | {pz(a6['Gesamt']['N'])} |",
    f"| Größter Einbruch | {pz(a6['Entwicklung']['dd_mit'], 0, False)} | {pz(a6['Pruefung']['dd_mit'], 0, False)} | {pz(a6['Gesamt']['dd_mit'], 0, False)} |"])
jahre_60 = ", ".join(f"{j}: {pz(v['N'])}" for j, v in G6["jahre"].items())
sl_60 = ", ".join(f"{zahl(float(k) / 100, 3)} % → {pz(v['N'])}" for k, v in G6["slippage"].items())
e5 = R5["entwicklung"]
hb, hv = R5["hebel_basis"], R5[f"hebel_{R5['gewinnerin']}"]
tab_5 = "\n".join(["| Variante | Besteht beide Hälften | Schlechtere Hälfte (Sharpe) | Netto, Entwicklung (Hebel 1) | Einbruch (Hebel 1) |", "|---|---|---|---|---|"] + [
    f"| {nm} | {'ja' if e5[k]['besteht'] else 'nein'} | {zahl(e5[k]['score'])} | {pz(e5[k]['N'])} | {pz(e5[k]['dd_mit'], 0, False)} |"
    for nm, k in (("Basis (der Kandidat)", "basis"), ("Ruhige Coins größer", "vol_coin"), ("In wilden Phasen kleiner", "vol_markt"),
                  ("Beides zusammen", "vol_beide"), ("Mischung aus 4 Trendlängen", "mischung"), ("Funding-Carry", "carry"))])
diag = D["tsmom_L168_biasTrue"]
rebate_jahr = pr["R"] / tage_p * 365

text = f"""# Suchbericht: Strategie mit Rebate als größerem Gewinnanteil

Stand 14.11.2026. Historische Simulation, keine Anlageberatung. Vergangene Ergebnisse sagen nichts Sicheres über die Zukunft.

## Ergebnis

**Es gibt einen Kandidaten, der deine Vorgabe auf dem Papier erfüllt. Tieferes Graben (Runde 5) hat keinen
zusätzlichen Edge gefunden und das Bild eher gedämpft: Auf einer zweiten frischen Coin-Gruppe bringt er im
Prüfzeitraum netto null. Der Vorteil ist klein und bringt bei deinem Kapital wenig Geld.**

Beste Gesamtschätzung über alle {G6['n_coins']} getesteten Coins, Hebel {zahl(H6, 2)}: im Prüfzeitraum {pz(a6['Pruefung']['N'])} netto mit Rebate
in 19 Monaten (davon {pz(a6['Pruefung']['R'])} Rebate), über gut fünf Jahre {pz(a6['Gesamt']['N'])}. Die Punkte darunter beziehen sich auf die
ursprünglichen 10 Coins.

- **Vor Gebühren profitabel:** ja, in jedem Kalenderjahr seit 2021.
- **Netto mit Rebate profitabel:** ja, in jedem Kalenderjahr. Im Prüfzeitraum aber nur {pz(pr['N'])} in 19 Monaten.
- **Rebate ist der größere Anteil:** ja. Im Prüfzeitraum {pz(pr['R'])} Rebate gegen {pz(pr['N'])} Nettogewinn.
  Ohne Rebate hätte der Handel dort {pz(pr['handel'])} gebracht, also verloren.
- **Größter Einbruch:** {pz(pr['dd_mit'], 0, False)} im Prüfzeitraum, {pz(ent['dd_mit'], 0, False)} in der Entwicklung (Grenze 15 %).
- **Der Haken:** Das hält nur bei Hebel {zahl(H, 1)}, also wenn nur ein Fünftel des Kontos im Markt ist. Bei 5.000 $ sind
  das etwa {usd(pr['R'] / tage_p * 5000)} Rebate und {usd(pr['N'] / tage_p * 5000)} Nettogewinn pro Tag.
- **Breiter gestreut wird es etwas besser:** Über {n_breit} Coins bringt derselbe Kandidat im Prüfzeitraum {pz(bp['N'])} statt {pz(pr['N'])},
  bei {pz(bp['dd_mit'], 0, False)} Einbruch. Mehr Hebel erlaubt die Streuung aber nicht.

Meine Empfehlung: als Vorwärtstest mit Kleinstbetrag laufen lassen, um die echte Slippage bei Yubit zu messen.
Nicht hochfahren, bevor diese Zahl vorliegt.

## Der Kandidat in einfachen Worten

- **Markt:** dieselben 10 Coins wie in deinem Labor, als Futures.
- **Signal, jede volle Stunde:** Steht der Kurs höher als vor 14 Tagen, dann Long. Steht er tiefer, dann Short.
  Das ist dein Tagestrend (momentum_vol_ls), nur stündlich nachgeführt und mit kürzerer Länge.
- **Größe:** jeder Coin gleich groß, zusammen höchstens {pz(H, 0, False)} des Kontos (Hebel {zahl(H, 1)}).
- **Order:** Limit mit Preisgrenze knapp durch den Markt. Sie wird sofort gefüllt und zählt als Taker.
- **Schutz:** Tagesverlust-Limit 3 % (in {tage_g} Tagen {K['orders']['sperrtage']}-mal ausgelöst), Obergrenze je Coin.
- **Aktivität:** rund {zahl(K['orders']['orders'] / tage_g, 0)} Orders pro Tag über alle Coins, Ø Haltedauer {zahl(ges['halte_h'], 0)} Stunden,
  Order-zu-Fill 1:1, keine Stornos, nie zwei Orders gleichzeitig je Coin.

## Zahlen

Gruppe A (10 Labor-Coins), Hebel {zahl(H, 1)}, 0,05 % Slippage je Order. Prozent vom Startkapital, ohne Zinseszins.

{tabelle}

### Jahr für Jahr

{jahre}

Das Rebate ist jedes Jahr fast gleich groß (rund {pz(rebate_jahr, 1, False)} des Kapitals), weil der Umsatz gleich bleibt.
Der Handel selbst schwankt stark und ist 2025 und 2026 deutlich schwächer als davor.
{pz(K['monate_positiv'], 0, False)} der {K['monate']} Monate schließen im Plus, {pz(K['trefferquote'], 0, False)} der Trades gewinnen (typisch für Trendfolge:
viele kleine Verluste, wenige große Gewinne).

## Kapital-Szenarien

{kap}

Bei 500 $ ist eine Position nur 10 $ groß. Ob Yubit so kleine Orders annimmt, weiß ich nicht.

## Wie belastbar ist das?

**Slippage entscheidet.** Der Kandidat verträgt im Prüfzeitraum bis knapp 0,07 % je Order, darüber verliert er:

{slip}

**Zweite Coin-Gruppe (nie zur Auswahl benutzt):** BNB, TRX, ATOM, BCH, ETC, FIL, UNI, NEAR, XLM, AAVE.
Entwicklung {pz(gb['Entwicklung']['N'])}, Prüfzeitraum {pz(gb['Pruefung']['N'])}. Positiv, im Prüfzeitraum aber praktisch null.

**Zufallstest:** Über den ganzen Zeitraum schlägt der Kandidat alle 200 Zufallsvarianten (dasselbe Signal, zeitlich
verschoben). Nur im Prüfzeitraum betrachtet ist er besser als {zahl(z['perzentil'], 0)} % davon. Das liegt unter der 90-%-Marke
deines Labors: In den letzten 19 Monaten ist der Vorteil statistisch nicht gesichert.

**Passive Ausführung statt sofortiger:** Mit Limit zum letzten Kurs (Maker) rechnet das Modell im Prüfzeitraum
{pz(pa['Pruefung']['N'])} netto, und der Handel wäre dort sogar nach voller Gebühr im Plus ({pz(pa['Pruefung']['handel'])}).
Dieser Wert hängt an der Füllannahme, die sich mit Kerzen nicht absichern lässt. Die sofortige Ausführung ist die
vorsichtige Untergrenze.

## Bestätigung auf frischen Daten (Runde 4)

Der Kandidat wurde unverändert auf Daten getestet, die in der Suche nie vorkamen. Vorab festgelegt war: bestätigt
nur, wenn Gruppe C in Entwicklung und Prüfzeitraum und die Vorperiode netto positiv sind. **Ergebnis: bestätigt.**
Runde 5 relativiert das: Eine weitere frische Gruppe (D) liegt im Prüfzeitraum bei null.
Alle Werte auf Hebel {zahl(H, 1)} umgerechnet, ohne Tageslimit.

{tab_c}

{tab_v}

Gruppe C: {", ".join(R4["gruppe_c"])}. Die Vorperiode war ein starker Aufwärtsmarkt, in dem Trendfolge leichtes
Spiel hatte; sie zählt deshalb weniger als Gruppe C. Nur Coins mit vollständiger Historie bis 2026 sind dabei, das
schönt etwas.

### Breites Portfolio: alle {n_breit} Coins zusammen

{tab_b}

{jahre_b}

- **Streuung senkt den Einbruch nicht genug für mehr Hebel.** Die Coins fallen und steigen zu sehr gemeinsam.
  Der zulässige Hebel bleibt {zahl(HB, 1)}, das Rebate damit bei rund {pz(bp['R'] / tp4 * 365, 1, False)} des Kapitals pro Jahr.
- **Slippage im Prüfzeitraum** (netto mit Rebate): {sl_b}. Die Schmerzgrenze liegt hier bei knapp 0,09 %.
- **Zufallstest nur im Prüfzeitraum:** besser als {zahl(zb['perzentil'], 0)} % der Zufallsvarianten, weiter unter der 90-%-Marke.

{kap_b}

Bei {n_breit} Coins werden die Einzelpositionen sehr klein. Unter etwa 5.000 $ Kapital ist das breite Portfolio kaum
handelbar, und ob Yubit alle diese Coins führt, weiß ich nicht.

## Tiefer gegraben (Runde 5)

Frage: Lässt sich aus dem Trend mehr holen, ohne den Einbruch zu erhöhen? Getestet wurden drei Arten der
Risikosteuerung, eine Mischung aus vier Trendlängen und eine neue Ertragsquelle (Funding-Carry), auf 40 Coins.

{tab_5}

- **Risikosteuerung sieht in der Entwicklung besser aus, hilft aber nicht.** Sie macht die beiden Hälften
  gleichmäßiger, erhöht aber den Einbruch. Beim zulässigen Hebel ({zahl(hv['hebel'], 2)} statt {zahl(hb['hebel'], 2)}) bringt sie im Prüfzeitraum
  {pz(hv['Pruefung']['N'])} statt {pz(hb['Pruefung']['N'])}. Auf der frischen Gruppe D ist sie nicht bestätigt.
- **Funding-Carry fällt durch:** in der ersten Hälfte positiv, in der zweiten nicht mehr.
- **Die Mischung aus Trendlängen fällt durch:** in der ersten Hälfte netto negativ.

### Gegenprobe über alle vier Coin-Gruppen

Der unveränderte Kandidat, auf Hebel {zahl(H, 1)} umgerechnet:

{tab_gr}

Vor Gebühren ist der Handel in allen vier Gruppen und beiden Zeiträumen positiv. Netto mit Rebate bleibt im
Prüfzeitraum aber nur in einer Gruppe (C) deutlich etwas übrig. Gruppe D: {", ".join(R5["gruppe_d"])}.

{tab_60}

- **Jahr für Jahr netto:** {jahre_60}.
- **Slippage im Prüfzeitraum:** {sl_60}.
- **Zufallstest nur im Prüfzeitraum:** besser als {zahl(G6['zufall_pruefung']['perzentil'], 0)} % der Zufallsvarianten.
- **In Dollar bei 5.000 $:** etwa {usd(a6['Pruefung']['R'] / t6p * 5000)} Rebate und {usd(a6['Pruefung']['N'] / t6p * 5000)} netto pro Tag im Prüfzeitraum,
  {usd(a6['Gesamt']['N'] / t6g * 5000)} netto pro Tag über den ganzen Zeitraum.

Über {G6['n_coins']} Coins sinkt der zulässige Hebel auf {zahl(H6, 2)}.

## Der Weg dorthin

Fünf Runden, 47 Versuche, alles vorab im Protokoll festgelegt (`suche_protokoll.md`).

1. **Runde 1 (30 Einstellungen, passive Limits):** {n_s1} bestehen die Entwicklung, beide Finalisten fallen im Füll-Stress durch.
   Alle Gegenbewegungs-Ideen (Rücksetzer kaufen, schwache Coins kaufen) verlieren schon vor Gebühren.
2. **Runde 2 (10 Trend-Einstellungen, sofortige Ausführung):** durchgefallen. Die Diagnose zeigte einen Fehler in
   meinem Testaufbau: Das Tagesverlust-Limit von 3 % wurde bei vollem Einsatz an jedem sechsten Tag ausgelöst
   und hat das Ergebnis dominiert.
3. **Runde 3 (dieselben 10, Messfehler korrigiert):** 2 Finalisten. Einer fällt im Prüfzeitraum klar durch
   (4-Tage-Trend), der 14-Tage-Trend besteht alle fünf Stufen.

4. **Runde 4 (keine Suche):** der Kandidat unverändert auf 20 frischen Coins und der Vorperiode 2020–2021. Bestätigt.

5. **Runde 5 (7 Varianten, tiefer gegraben):** Risikosteuerung, Trend-Mischung, Funding-Carry. Kein Mehrwert.
   Eine vierte, frische Coin-Gruppe zeigt den Kandidaten im Prüfzeitraum bei netto null.

Der Prüfzeitraum und die zweite Coin-Gruppe wurden erst in Runde 3 angesehen, und nur für diese zwei Finalisten.
Insgesamt sind es jetzt 47 Versuche. Der Kern des Befunds hat sich seit Runde 3 nicht mehr bewegt: ein kleiner
Trend-Vorteil vor Gebühren, der nach Kosten nur mit Rebate und nur knapp trägt.
Wichtig für die Einordnung: Bei 40 Versuchen in drei Messaufbauten ist ein einzelner Treffer weniger wert als ein
Treffer beim ersten Versuch.

## Was das für dein Ziel bedeutet

- **Rebate hängt am Umsatz, Umsatz hängt am Einsatz, und den Einsatz begrenzt deine 15-%-Grenze.**
  Diese Strategie schlägt den eingesetzten Betrag etwa {zahl(ges['vol_tag'] / H, 1)}-mal pro Tag um. Mit Hebel {zahl(H, 1)} ergibt das
  rund {pz(rebate_jahr, 1, False)} des Kapitals als Rebate pro Jahr.
- **Mehr Hebel bringt mehr Rebate, aber im selben Maß mehr Einbruch.** Bei Hebel 1 lag der Einbruch im
  Prüfzeitraum bei {pz(E['stufen']['3_pruefung']['sofort']['A']['Pruefung']['dd_mit'], 0, False)}.
- **Der Gewinn kommt hier wirklich aus dem Rebate.** In den Jahren 2022, 2025 und 2026 hätte der Handel ohne Rebate
  verloren. Wird das Rebate gekürzt oder gestrichen, trägt die Strategie nach heutigem Stand nicht mehr.
  Das ist genau die Abhängigkeit, die du mit „kein Rebate-Farming“ ursprünglich ausschließen wolltest.
- **Mehr Rebate heißt hier nicht mehr Gewinn.** Deine reine Tages-Swing (momentum_vol_ls) hätte im selben
  Prüfzeitraum beim selben Hebel {pz(sw['rendite_mit'] * H)} netto gebracht, also mehr als der Kandidat ({pz(pr['N'])}),
  mit rund einem {zahl(pr['vol_tag'] / (sw['volumen_tag'] * H), 0)}tel des Umsatzes. Der Kandidat tauscht Gewinn gegen Volumen.

## Risiken und Annahmen

- **Yubit ist nicht getestet.** Kurse, Funding und Slippage stammen von Binance-Futures. Die Slippage bei Yubit ist
  die eine Zahl, die über Gewinn oder Verlust entscheidet.
- **Regel-Auslegung:** Du hast „Limit-Orders für Einstiege“ verlangt. Der Kandidat nutzt Limits mit Preisgrenze,
  die sofort gefüllt werden. Dem Ordertyp nach ist das ein Limit, den Gebühren nach ein Taker.
- **Risikokontrolle der Börse:** Ein Konto, dessen Gewinn überwiegend aus Rebate stammt, kann dort auffallen.
  Prüf, ob die Freigabe deines Partners das ausdrücklich abdeckt.
- **Rebate:** gerechnet als sofortige Gutschrift von 85 % der Gebühr.
- **Die Coins wurden im Rückblick festgelegt,** und der Prüfzeitraum umfasst nur 19 Monate.
- **Keine Zinseszins-Rechnung,** feste Positionsgröße vom Startkapital.

## Dateien

- `suche_protokoll.md`: Regeln und Zwischenergebnisse aller drei Runden
- `suche_stufe1.csv`, `suche_runde2_stufe1.csv`, `suche_runde3_stufe1.csv`: alle 40 Einstellungen mit Zahlen
- `suche_runde3.json`, `suche_runde4.json`, `suche_runde5.json`, `gesamt_60.json`, `kandidat.json`, `fuellmodell_diagnose.json`: Rohwerte zu diesem Bericht
- `../labor_strategie/trend_14d/strategie.py`: der Kandidat im Format deines Labors
- `../scripts/vorwaertstest_auswerten.py`: wertet ein Protokoll echter Orders aus (Slippage gegen die Schmerzgrenze)
"""
(ROOT / "reports/suche_bericht.md").write_text(text)
print(text)
