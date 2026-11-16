"""Schreibt reports/statarb_bericht.md aus suche_runde12.json (keine Zahl von Hand)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "reports/suche_runde12.json").read_text())
s, F = R["statarb"], R["fusion"]


def pz(x, n=1, vz=True):
    t = f"{x * 100:+.{n}f}" if vz else f"{x * 100:.{n}f}"
    return t.replace(".", ",").replace("-", "−") + " %"


def z(x, n=2):
    return f"{x:.{n}f}".replace(".", ",").replace("-", "−")


a, tr = s["A"], s["trades"]
einsatz_paar = 0.1                                          # 10 Paare gleichzeitig, je ein Zehntel des Topfes
gew = tr["mittel_gewinn_je_trade"] / einsatz_paar
kost = tr["kosten_je_trade"] / einsatz_paar
allein = "\n".join([
    "| Gruppe | Zeitraum | Vor Kosten | Kosten | Netto | Größter Einbruch |", "|---|---|---|---|---|---|"] + [
    f"| {g} | {nm} | {pz(s[g][k]['G'])} | {pz(-s[g][k]['kosten'])} | **{pz(s[g][k]['N'])}** | {pz(s[g][k]['dd'], 0, False)} |"
    for g in ("A", "B", "C") for nm, k in (("Entwicklung", "Entwicklung"), ("Prüfzeitraum", "Pruefung"))])
raster = "\n".join(["| Fenster | Z-Schwelle | Vor Kosten | Netto | Trades |", "|---|---|---|---|---|"] + [
    f"| {x['W_tage']} Tage | {z(x['z_ein'], 1)} | {pz(x['Entw_G'])} | {pz(x['Entw_N'])} | {x['trades']} |" for x in s["stufe1"]])


def fus(strat):
    f = F[strat]
    zeilen = ["| | Netto pro Jahr, Entwicklung | Einbruch | Sharpe | Netto pro Jahr, Prüfzeitraum | Einbruch | Sharpe |", "|---|---|---|---|---|---|---|"]
    for nm, k in (("Swing allein", "swing_allein"), ("Stat-Arb allein", "statarb_allein"), ("Fusion 1: zwei Töpfe", "F1_zwei_toepfe"),
                  ("Fusion 2: Swing als Filter", "F2_swing_als_filter")):
        e, p = f[k]["Entwicklung"], f[k]["Pruefung"]
        zeilen.append(f"| {nm} | {pz(e['jahr_N'])} | {pz(e['dd'], 0, False)} | {z(e['sharpe'])} | {pz(p['jahr_N'])} | {pz(p['dd'], 0, False)} | {z(p['sharpe'])} |")
    return "\n".join(zeilen)


ft, fm = F["trail_beide"], F["momentum_vol_ls"]
text = f"""# Stat-Arb mit Z-Score, fusioniert mit dem Swing

Stand 14.11.2026. Historische Simulation auf Binance-Futures, keine Anlageberatung. Yubit spielt hier keine Rolle;
gerechnet wird mit den Kosten deines Labors (0,05 % Gebühr + 0,05 % Slippage je Order).

## Ergebnis

**Das Stat-Arb-System ist gebaut und funktioniert technisch. Es verdient vor Kosten, nach Kosten aber nicht.
Die Fusion mit dem Swing senkt den Einbruch deutlich, ist aber im Prüfzeitraum nicht besser als der Swing allein.**

- Stat-Arb allein, Gruppe A: vor Kosten {pz(a['Entwicklung']['G'])} in der Entwicklung, netto {pz(a['Entwicklung']['N'])}; im Prüfzeitraum netto {pz(a['Pruefung']['N'])}.
- Keine der 9 Einstellungen ist in beiden Entwicklungshälften netto positiv.
- Ein Paar-Trade verdient im Mittel {pz(gew, 2, False)} seines Einsatzes und kostet {pz(kost, 2, False)} (vier Orders).

## Was gebaut wurde

- **Paare finden:** Für jedes Coin-Paar wird laufend über ein Fenster gemessen, wie stark die Kurse zusammenlaufen
  (Korrelation mindestens 0,7) und in welchem Verhältnis (Hedge-Verhältnis aus einer Regression).
- **Z-Score:** Der Abstand der beiden Kurse voneinander wird mit seinem eigenen Mittel und seiner Schwankung
  verglichen. Z = 2 heißt: zwei Standardabweichungen auseinander.
- **Handeln:** Ab der Z-Schwelle den teuren Coin short, den billigen long. Raus, wenn der Abstand zurück am Mittel
  ist, bei Z = 4 (Stop) oder nach der halben Fensterlänge.
- **Grenzen:** höchstens 10 Paare gleichzeitig, jeder Coin in höchstens 3 Paaren, Long und Short zusammen höchstens
  100 % des Topfes. Signale am Kerzenschluss, Ausführung zum Open der nächsten Stundenkerze, echtes Funding.

Getestet sind: verdient an künstlichen Paaren, die zum Mittel zurückkehren; ignoriert unkorrelierte Coins; hält die
Obergrenzen ein; kein Blick in die Zukunft.

## Stat-Arb allein

Alle 9 Einstellungen, Gruppe A (10 Coins), Entwicklungszeitraum:

{raster}

Je kürzer das Fenster, desto mehr Trades und desto mehr fressen die Kosten. Weitergerechnet wurde mit der
Einstellung, die dem Bestehen am nächsten kam ({s['W'] // 24} Tage, Z-Schwelle {z(s['z_ein'], 1)}):

{allein}

- **Trefferquote vor Kosten:** {pz(tr['gewinner_vor_kosten'], 0, False)}, mittlere Haltedauer {z(tr['stunden_mittel'] / 24, 1)} Tage, {tr['anzahl']} Trades über den ganzen Zeitraum.
- **Woran es hängt:** {tr['gruende']['ziel']} Trades enden am Ziel und bringen zusammen {pz(tr['gewinn_je_grund']['ziel'], 0)} des Topfes. {tr['gruende']['stop']} enden im Stop
  ({pz(tr['gewinn_je_grund']['stop'], 0)}) und {tr['gruende']['zeit']} im Zeitlimit ({pz(tr['gewinn_je_grund']['zeit'], 0)}). Paare, die auseinanderlaufen und nicht
  zurückkommen, nehmen fast alles wieder weg.
- **Mit sehr niedrigen Kosten** (Yubit nach Rebate): Entwicklung {pz(s['A_yubit_kosten']['Entwicklung']['N'])}, Prüfzeitraum {pz(s['A_yubit_kosten']['Pruefung']['N'])}.
  Selbst ganz ohne Kosten bleiben im Prüfzeitraum nur {pz(s['A_ohne_kosten']['Pruefung']['N'])}.

## Fusion mit dem Swing

Zwei Arten, jeweils mit beiden Swing-Strategien aus deinem Labor (Hebel 1, gleiche Kosten):

- **Fusion 1, zwei Töpfe:** die Hälfte des Kapitals im Swing, die Hälfte im Stat-Arb.
- **Fusion 2, Swing als Filter:** Das Stat-Arb nimmt ein Paar nur, wenn keine Seite gegen die Swing-Richtung des
  jeweiligen Coins läuft. Dazu wieder die Hälfte im Swing.

### trail_beide (4H)

{fus('trail_beide')}

### momentum_vol_ls (1D)

{fus('momentum_vol_ls')}

- **Der Einbruch sinkt deutlich.** Das liegt vor allem daran, dass nur noch die Hälfte im Swing steckt.
- **Swing und Stat-Arb laufen leicht gegeneinander** (Korrelation der Tagesgewinne {z(ft['korrelation_tagesgewinne'])}). Das ist echte
  Streuung und der Grund, warum die Fusion in der Entwicklung in drei von vier Fällen einen besseren Sharpe hat.
- **Im Prüfzeitraum ist der Sharpe in allen vier Fällen niedriger als beim Swing allein.** Der Stat-Arb-Topf
  verdient netto nichts und verdünnt den Swing nur.
- **Der Filter hilft dem Stat-Arb** (bei trail_beide im Prüfzeitraum {pz(ft['statarb_gefiltert']['Pruefung']['N'])} statt {pz(ft['statarb_allein']['Pruefung']['N'])}), macht es aber nicht profitabel.

Vorab festgelegt war: Die Fusion gilt als besser, wenn sie in Entwicklung **und** Prüfzeitraum einen höheren Sharpe
und einen kleineren Einbruch hat. Das erfüllt keine der vier Kombinationen.

## Einordnung

- Der Effekt ist da, aber klein: Paare kehren vor Kosten tatsächlich öfter zurück als nicht. Er reicht nicht für
  vier Orders je Trade.
- Er ist nicht stabil über Coin-Gruppen: Gruppe B ist schon vor Kosten negativ ({pz(s['B']['Entwicklung']['G'])} / {pz(s['B']['Pruefung']['G'])}),
  Gruppe C vor Kosten klar positiv ({pz(s['C']['Entwicklung']['G'])} / {pz(s['C']['Pruefung']['G'])}).
- Das passt zu den früheren Runden: Gegenbewegungs-Regeln und die marktneutrale Rangfolge sind ebenfalls an Kosten
  und fehlender Stabilität gescheitert.

## Dateien

- `src/hybrid/statarb.py`: das Stat-Arb-System
- `scripts/suche_runde12.py`: Raster, Gegenproben und Fusion; `tests/test_statarb.py`: Tests
- `reports/suche_runde12.json`, `reports/suche_runde12_stufe1.csv`: alle Zahlen
- `reports/suche_protokoll.md`: die vorab festgelegten Regeln (Runde 12)
"""
(ROOT / "reports/statarb_bericht.md").write_text(text)
print(text)
