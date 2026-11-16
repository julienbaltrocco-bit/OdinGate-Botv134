"""C06 Stufe 3, Gruppenbildung: eigene Nachrechnung (andere Formel, gleiche Regel) gegen die gespeicherten Entscheidungen;
danach: Wie unabhängig sind die 1.327 Finalisten wirklich? (nur lesend; Tagesreihen T und V1)"""
import sys, json, collections
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
from fabrik import lauf as L

con = C.ro()
tief = lambda z: bool(z["braucht"] == "t" or (z["best"] and ("tiefe" in z["best"] or "liq_entzug" in z["best"])))
weiter = con.execute("SELECT * FROM kandidaten WHERE status IN ('final', 'stufe3')").fetchall()
mm = {g: np.load(f'data/fabrik/tage_{g}.npy', mmap_mode='r') for g in ("gen1", "gen2")}
weiter.sort(key=lambda z: -z["sharpe_v"])                       # Python sortiert stabil; die ursprüngliche Reihenfolge bei Gleichstand ist nicht gespeichert
R = np.stack([np.asarray(mm[z["gen"]][z["zeile"]], dtype=np.float64) for z in weiter])
for i, z in enumerate(weiter):
    R[i, :L.SEGMENTE["t" if tief(z) else "k"][0]] = 0.0
NZ = R != 0
s1, s2 = R.sum(1), (R * R).sum(1)


def korr_vereinigung(i, fuehrer):
    """Korrelation von Reihe i mit den Reihen 'fuehrer' auf den Tagen, an denen mindestens eine der beiden ungleich null ist (Formel über Summen)."""
    n = (NZ[fuehrer] | NZ[i]).sum(1).astype(np.float64)
    sxy = R[fuehrer] @ R[i]
    kov = sxy - s1[fuehrer] * s1[i] / n
    va, vb = s2[fuehrer] - s1[fuehrer] ** 2 / n, s2[i] - s1[i] ** 2 / n
    return np.where((va > 0) & (vb > 0), kov / np.sqrt(np.where(va > 0, va, 1) * np.where(vb > 0, vb, 1)), np.nan), n


fuehrer, gruppe_von, groesse = [], {}, collections.Counter()
for i, z in enumerate(weiter):
    treffer = None
    if fuehrer:
        k, n = korr_vereinigung(i, np.array(fuehrer))
        t = np.where((n > 30) & (k > 0.8))[0]
        if len(t):
            treffer = fuehrer[int(t[0])]
    if treffer is None:
        fuehrer.append(i); gruppe_von[i] = i
    else:
        gruppe_von[i] = treffer
    groesse[gruppe_von[i]] += 1
eigen_final = {(weiter[i]["id"], weiter[i]["gen"]) for i in fuehrer}
db_final = {(z["id"], z["gen"]) for z in weiter if z["status"] == "final"}
print(f"robuste Kandidaten {len(weiter)} | Finalisten laut Datenbank {len(db_final)}, laut eigener Nachrechnung {len(eigen_final)} | nur in der Datenbank {len(db_final - eigen_final)}, nur eigen {len(eigen_final - db_final)}")
fj = json.load(open('forschung/fabrik/ergebnisse/finalisten.json'))
gr_json = {(f["id"], f["gen"]): f["gruppengroesse"] for f in fj["finalisten"]}
gr_eigen = {(weiter[i]["id"], weiter[i]["gen"]): groesse[i] for i in fuehrer}
print("Gruppengrößen gleich wie in finalisten.json:", sum(gr_json.get(k) == v for k, v in gr_eigen.items()), "von", len(gr_eigen), "| finalisten.json: robust", fj["robust"], "Gruppen", fj["gruppen"], "eingefroren", fj["eingefroren"])
vertreter_falsch = 0
for i, z in enumerate(weiter):
    if z["status"] == "stufe3":
        vertreter_falsch += not z["grund"].endswith(weiter[gruppe_von[i]]["id"])
print("Mitglieder, deren gespeicherter Vertreter von der eigenen Nachrechnung abweicht:", vertreter_falsch)
bester = sum(weiter[i]["sharpe_v"] >= max(weiter[j]["sharpe_v"] for j in range(len(weiter)) if gruppe_von[j] == i) - 1e-12 for i in fuehrer[:200])
print("Vertreter hat den höchsten Sharpe in V1 seiner Gruppe (erste 200 Gruppen):", bester, "von 200")

print("\nWie verschieden sind die Finalisten?")
F = np.array(fuehrer)
ist_tief = np.array([tief(weiter[i]) for i in F])
print(f"   Finalisten {len(F)}: Orderbuch-Gruppe {ist_tief.sum()}, übrige {(~ist_tief).sum()} | verschiedene Einstiegsregeln (Signal, Richtung, Filter): "
      f"{len({(weiter[i]['signal'], weiter[i]['r'], weiter[i]['f']) for i in F})} | verschiedene (Signal, Richtung): {len({(weiter[i]['signal'], weiter[i]['r']) for i in F})} | verschiedene Signale: {len({weiter[i]['signal'] for i in F})}")
# volle Korrelationsmatrix der Finalisten über den gemeinsamen Zeitraum (ab Tag 504 = 2023-01-01 für alle), alle Kalendertage
X = R[F][:, 504:]
Xs = (X - X.mean(1, keepdims=True)); Xs /= np.sqrt((Xs ** 2).sum(1, keepdims=True))
K = Xs @ Xs.T
np.fill_diagonal(K, np.nan)
ob = np.triu_indices(len(F), 1)
print(f"   Korrelation der Tagesergebnisse zwischen Finalisten (2023-01-01 bis 2024-06-30, alle Tage): Median {np.nanmedian(K[ob]):+.3f}, 95 % {np.nanpercentile(K[ob], 95):+.3f}, Paare über 0,8: {(K[ob] > 0.8).sum()}, über 0,7: {(K[ob] > 0.7).sum()}, über 0,5: {(K[ob] > 0.5).sum()} von {len(ob[0])}")
gemischt = np.where(ist_tief[:, None] != ist_tief[None, :], K, np.nan)
print(f"   davon Paare Orderbuch-Gruppe mit übriger Gruppe über 0,8 (in stufe3 über die Vereinigung aller Tage ab 2021 gerechnet, dort verdünnt): {(np.nan_to_num(gemischt[ob], nan=0) > 0.8).sum()}")
print(f"   Finalisten, die mit mindestens einem anderen Finalisten über 0,7 korrelieren: {(np.nanmax(K, 1) > 0.7).sum()}; über 0,5: {(np.nanmax(K, 1) > 0.5).sum()}")
ew = np.linalg.eigvalsh(np.nan_to_num(K, nan=1.0))[::-1]
print(f"   Eigenwerte der Korrelationsmatrix: die größten fünf {np.round(ew[:5], 1)} | Zahl gleichwertiger unabhängiger Reihen (Summe)^2 / Summe der Quadrate = {ew.sum() ** 2 / (ew ** 2).sum():.0f}"
      f" | 90 % der Streuung stecken in {int(np.searchsorted(np.cumsum(ew) / ew.sum(), 0.9)) + 1} Hauptrichtungen")
(C.HIER / "tmp").mkdir(exist_ok=True)
np.save(C.HIER / "tmp" / "finalisten_reihen.npy", R[F]); json.dump([[weiter[i]["id"], weiter[i]["gen"], bool(ist_tief[k])] for k, i in enumerate(F)], open(C.HIER / "tmp" / "finalisten_ids.json", "w"))
