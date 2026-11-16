"""C03 Stufe 3, Nachbar-Regel: BASIS und Auswahl der Nachbar-Signale für alle 63 Signale; trichter.nachbarn_ok (lesend, echte Datenbank)
gegen eine eigene Nachrechnung in pandas und gegen die gespeicherten Entscheidungen."""
import sys, json, collections
import numpy as np, pandas as pd
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
from fabrik import signale as S, trichter as T, lauf as L

con = C.ro()
print("1) BASIS und Nachbar-Signale (nach Länge sortiert), wie nachbarn_ok sie bildet:")
ohne = []
for name, fam, laenge, braucht in S.SIGNALE:
    basis = T.BASIS(name)
    verwandt = sorted((s[2], s[0]) for s in S.SIGNALE if T.BASIS(s[0]) == basis and s[0] != basis or s[0] == name)
    namen = [s for _, s in verwandt]
    i = namen.index(name)
    nb = [namen[k] for k in (i - 1, i + 1) if 0 <= k < len(namen)]
    if not nb:
        ohne.append(name)
    print(f"   {name:<20} Länge {laenge:>3}  BASIS {basis:<14} Nachbarn {nb}")
print("   Signale ohne Nachbar-Länge:", ohne)

print("\n2) Entscheidungen nachstellen: alle Kandidaten, die Stufe 2 bestanden und die V1-Hürde nehmen (dann erst greift die Nachbar-Regel)")
kand = con.execute("SELECT * FROM kandidaten WHERE status IN ('final','stufe3','verworfen_3') AND n85_v > 0 AND t85_v >= 1").fetchall()
alle = pd.read_sql("SELECT signal, th, r, f, k, x, m, n85_t FROM kandidaten WHERE n_t >= 200 AND best IS NULL", con)
tab = {key: g for key, g in alle.groupby(["signal", "f", "k", "x", "m", "r"])}
laengen = {s[0]: s[2] for s in S.SIGNALE}


def basis_eigen(s):
    kopf, _, ende = s.rpartition("_")
    return kopf if kopf and ende.replace(".", "").isdigit() else s


def eigen(z):
    """Eigene Nachrechnung nach dem Wortlaut: gleiches Signal mit Schwelle im Abstand bis 1,0 (ohne die eigene; bei Bestätigungssignal mit der
    Eltern-Schwelle), dazu die in der Länge unmittelbar benachbarten Signale derselben Art bei gleicher Schwelle. Sonst alles gleich, ohne Bestätigung."""
    key = lambda s: (s, z["f"], z["k"], z["x"], z["m"], z["r"])
    werte = []
    g = tab.get(key(z["signal"]))
    if g is not None:
        d = (g["th"] - z["th"]).abs()
        werte += list(g.loc[(d <= 1.01) & ((d > 0) | bool(z["best"])), "n85_t"])
    b = basis_eigen(z["signal"])
    fam = sorted((laengen[s], s) for s in laengen if (basis_eigen(s) == b and s != b) or s == z["signal"])
    namen = [s for _, s in fam]
    i = namen.index(z["signal"])
    for k in (i - 1, i + 1):
        if 0 <= k < len(namen):
            g = tab.get(key(namen[k]))
            if g is not None:
                werte += list(g.loc[g["th"] == z["th"], "n85_t"])
    pos = sum(1 for w in werte if w > 0)
    return (len(werte) > 0 and pos >= len(werte) / 2), len(werte), pos


abw, n_db_nachbar, n_fkt_nachbar, zahl = 0, 0, 0, collections.Counter()
art_zahl = collections.defaultdict(lambda: [0, 0, 0, 0])
for z in kand:
    a, b = T.nachbarn_ok(con, z), eigen(z)
    abw += a != b
    in_db = z["status"] == "verworfen_3" and z["grund"] == "Nachbar-Einstellungen überwiegend negativ"
    n_db_nachbar += in_db; n_fkt_nachbar += not a[0]
    if in_db != (not a[0]):
        print("   Entscheidung in der Datenbank weicht ab:", z["id"], z["gen"], z["status"], z["grund"], a)
    zahl[min(a[1], 6)] += 1
    art = "gen1" if z["gen"] == "gen1" else ("gen2 Bestätigung" if z["best"] else ("gen2 neue Schwelle" if z["th"] not in (1.5, 2.5, 3.5) else "gen2 neuer Ausstieg"))
    art_zahl[art][0] += 1; art_zahl[art][1] += not a[0]; art_zahl[art][2] += a[1] == 0; art_zahl[art][3] += a[1]
print(f"   geprüft {len(kand)} | trichter.nachbarn_ok gegen eigene Nachrechnung: {abw} Abweichungen | abgelehnt laut Funktion {n_fkt_nachbar}, laut Datenbank {n_db_nachbar}")
print("   Zahl der Nachbarn je Kandidat (6 = sechs oder mehr):", dict(sorted(zahl.items())))
for art, (n, abgel, null, summe) in art_zahl.items():
    print(f"   {art:<20} geprüft {n:>5}  abgelehnt {abgel:>4} ({abgel / n:.1%})  davon ohne jeden Nachbarn {null:>3}  Nachbarn im Mittel {summe / n:.1f}")

print("\n3) Wie streng ist die Regel? Vergleich mit dem Anteil positiver Nachbarn bei beliebigen gültigen Kandidaten")
print(f"   Anteil aller gültigen Regeln ohne Bestätigung mit n85_t > 0: {(alle['n85_t'] > 0).mean():.3f}")
z_best = [z for z in kand if z["best"]]
eltern_pos = 0
for z in z_best:
    g = tab.get((z["signal"], z["f"], z["k"], z["x"], z["m"], z["r"]))
    e = g.loc[g["th"] == z["th"], "n85_t"] if g is not None else []
    eltern_pos += len(e) > 0 and float(e.iloc[0]) > 0
print(f"   Varianten mit Bestätigung: {len(z_best)}; ihre Eltern-Regel (gleicher Ausstieg, gleicher Markt) ist in T positiv bei {eltern_pos} ({eltern_pos / max(len(z_best), 1):.1%})")
