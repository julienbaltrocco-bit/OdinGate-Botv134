"""C07 Stufe 4 wird NICHT ausgeführt. Geprüft wird der Quelltext:
1) Benjamini-Hochberg: der Abschnitt aus stufe4 wird wörtlich aus dem Quelltext geschnitten und mit künstlichen p-Werten gegen zwei
   Referenzrechnungen gelaufen (scipy.stats.false_discovery_control und die Lehrbuchdefinition).
2) Sperre gegen Wiederholung: die Zeilen 'bekannt'/'neu' aus stufe4, wörtlich, mit künstlichen Dateiinhalten.
3) Wie viele 'validierte' Kandidaten entstehen rein zufällig? Unabhängige p-Werte und - wirklichkeitsnäher - die 1.327 Finalisten mit ihren
   echten Tagesreihen (T/V1 ab 2023, auf Mittel null gesetzt = kein Vorteil), aus denen 274 'V2-Tage' blockweise gezogen werden."""
import sys, math, inspect, textwrap, json
import numpy as np
from scipy import stats
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
import c02_rc_eichung as E
from fabrik import trichter as T

print("Code-Stand:", C.stand())
src = inspect.getsource(T.stufe4)
a, b = src.index("    m = len(erg)"), src.index('        con.execute("UPDATE kandidaten SET status = ?')
BH = textwrap.dedent(src[a:b])
print("1) geprüfter Abschnitt aus trichter.stufe4 (wörtlich):"); print(textwrap.indent(BH, "      | "))


def bh_trichter(p, n85=None, n2x=None):
    erg = [{"p_v2": float(x), "n85_v2": 1.0 if n85 is None else n85[i], "n85_2x_v2": 1.0 if n2x is None else n2x[i], "nr": i} for i, x in enumerate(p)]
    ns = {"erg": erg}
    exec(BH, ns)
    aus = np.zeros(len(p), bool); val = np.zeros(len(p), bool)
    for e in erg:
        aus[e["nr"]], val[e["nr"]] = e["bh_bestanden"], e["validiert"]
    return aus, val


def bh_lehrbuch(p, q=0.10):
    p = np.asarray(p); m = len(p)
    ordnung = np.argsort(p, kind="stable")
    k = 0
    for rang, i in enumerate(ordnung, 1):
        if p[i] <= q * rang / m:
            k = rang
    aus = np.zeros(m, bool); aus[ordnung[:k]] = True
    return aus


rng = np.random.default_rng(3)
abw_lehr = abw_scipy = faelle = 0
for fall in range(3000):
    m = int(rng.choice([1, 2, 3, 10, 50, 300, 1327]))
    art = fall % 5
    p = rng.random(m)
    if art == 1: p[: max(1, m // 10)] = rng.random(max(1, m // 10)) * 1e-4
    if art == 2: p = np.round(p, 2)                                # viele gleiche p-Werte
    if art == 3: p[: m // 2] = 0.0
    if art == 4: p = np.round(1 - stats.norm.cdf(rng.normal(1.0, 1.5, m)), 6)   # so gerundet wie in stufe4
    x, _ = bh_trichter(p)
    y = bh_lehrbuch(p)
    z = stats.false_discovery_control(p, method="bh") <= 0.10
    abw_lehr += not np.array_equal(x, y)
    grenznah = np.any(np.abs(stats.false_discovery_control(p, method="bh") - 0.10) < 1e-12)
    abw_scipy += (not np.array_equal(x, z)) and not grenznah
    faelle += 1
print(f"   {faelle} künstliche Fälle (m = 1 bis 1327, Gleichstände, Nullen, gerundete p-Werte): Abweichungen zur Lehrbuchrechnung {abw_lehr}, zu scipy {abw_scipy}")
p = np.array([0.00001, 0.00002, 0.00003, 0.9]); x, v = bh_trichter(p, n85=[1, -1, 1, 1], n2x=[1, 1, -1, 1])
print("   Zusatzbedingungen: BH bestanden", x.tolist(), "| validiert (zusätzlich n85_v2 > 0 und n85_2x_v2 > 0):", v.tolist())
print(f"   Rundung: p_v2 wird vor dem Vergleich auf 6 Stellen gerundet; kleinste Schwelle bei m = 1327: 0,10 / 1327 = {0.1 / 1327:.3e} (Rundungsfehler bis 5e-7 = {5e-7 / (0.1 / 1327):.1%} der Schwelle)")

print("\n2) Sperre gegen Wiederholung (Zeilen aus stufe4, wörtlich):")
a, b = src.index("    bekannt = "), src.index("    if not neu:")
SP = textwrap.dedent(src[a:b]); print(textwrap.indent(SP, "      | "))
alt = {"chargen": [{"charge": 1}], "ergebnisse": [{"id": "aaa", "gen": "gen1"}, {"id": "bbb", "gen": "gen2"}]}
for text, fin in (("dieselben Finalisten noch einmal", [{"id": "aaa", "gen": "gen1"}, {"id": "bbb", "gen": "gen2"}]),
                  ("dieselbe Regel (gleiche Kennung) in einer späteren Generation neu gerechnet", [{"id": "aaa", "gen": "gen3"}]),
                  ("Gruppenmitglied eines schon geprüften Finalisten, in einem späteren Stufe-3-Lauf zum Finalisten geworden", [{"id": "ccc", "gen": "gen3"}])):
    ns = {"alt": alt, "fin": {"finalisten": fin}}
    exec(SP, ns)
    print(f"   {text}: als 'neu' zur Prüfung auf V2 zugelassen: {[f['id'] + '/' + f['gen'] for f in ns['neu']]}")
print("   Ohne die Datei schlusspruefung.json (gelöscht, verschoben) gilt alles als neu: bekannt = set() -> alle Finalisten würden erneut auf V2 gerechnet.")

print("\n3) Zufällig 'validiert' bei Fehlentdeckungsrate 10 %")
m = 1327
R = []
for w in range(20000):
    p = np.sort(rng.random(m))
    k = np.nonzero(p <= 0.10 * np.arange(1, m + 1) / m)[0]
    R.append(k.max() + 1 if len(k) else 0)
R = np.array(R)
print(f"   a) {m} unabhängige Finalisten ohne Vorteil (p gleichverteilt), 20.000 Durchläufe: mindestens einer validiert in {np.mean(R > 0):.1%}, im Mittel {R.mean():.3f}, größter Wert {R.max()}")
X = np.load(C.HIER / "tmp" / "finalisten_reihen.npy")[:, 504:]          # 2023-01-01 bis 2024-06-30, für alle Finalisten vorhanden
Xc = X - X.mean(1, keepdims=True)
for name, blockl in (("Tage einzeln gezogen", 1), ("Blöcke von im Mittel 10 Tagen", 10)):
    R, klein = [], []
    for w in range(4000):
        ix = E.idx_schnell(X.shape[1], 1, blockl, rng)[0][:274]
        v = Xc[:, ix]
        s = v.std(1, ddof=1)
        t = np.where(s > 0, v.mean(1) / np.where(s > 0, s, 1) * math.sqrt(274), 0.0)
        p = np.sort(1 - stats.norm.cdf(t))
        k = np.nonzero(p <= 0.10 * np.arange(1, m + 1) / m)[0]
        R.append(k.max() + 1 if len(k) else 0); klein.append(np.mean(p < 0.05))
    R = np.array(R)
    print(f"   b) echte Finalisten-Reihen ohne Vorteil, {name}, 4.000 Durchläufe: mindestens einer validiert in {np.mean(R > 0):.1%}; Zahl der Validierten im Mittel {R.mean():.1f}, "
          f"Median {np.median(R):.0f}, 95 % {np.percentile(R, 95):.0f}, 99 % {np.percentile(R, 99):.0f}, größter Wert {R.max()} | Anteil p < 0,05 im Mittel {np.mean(klein):.3f} (Soll 0,05)")
    if blockl == 10:
        print(f"      Wenn mindestens einer validiert wird, dann im Mittel {R[R > 0].mean():.0f} zugleich (Median {np.median(R[R > 0]):.0f}).")
