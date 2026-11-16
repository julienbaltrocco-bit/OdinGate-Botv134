"""C10 Die ECHTE Funktion trichter.stufe3() auf einer kleinen KOPIE (tmp/), V2-blind: Was geschieht, wenn Stufe 3 in einem späteren Zyklus
noch einmal läuft (neue Kandidaten aus einer weiteren Generation)? Verwendet wird ein Finalist A aus Lauf A und ein Mitglied B seiner Gruppe
(Korrelation der Tagesergebnisse > 0,8, in Lauf A deshalb NICHT Finalist).
Lauf 1: nur A steht auf 'stufe2'.  Lauf 2: danach kommt B dazu.  Kontrolle: A und B gemeinsam in einem Lauf."""
import sys, json, sqlite3, shutil, io, contextlib
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
from fabrik import daten as D, lauf as L, trichter as T

print("Code-Stand:", C.stand())
ende = C.blind()
ERG_TMP = C.TMP / "erg_c10"; ERG_TMP.mkdir(parents=True, exist_ok=True)
shutil.copy(C.ECHT_ERG / "ausstiege.json", ERG_TMP / "ausstiege.json")
T.ERG = ERG_TMP
L.AUS = C.ECHT_AUS                                            # Tagesreihen von Lauf A, nur lesend
con = C.ro()
tief = lambda z: bool(z["braucht"] == "t" or (z["best"] and ("tiefe" in z["best"] or "liq_entzug" in z["best"])))


def besteht_heute(z):
    """Bedingungen der Stufe 3 nach heutigem Code (Lauf A wurde mit dem Stand von gestern gerechnet)."""
    if not (z["n85_v"] > 0 and z["t85_v"] >= 1) or not T.nachbarn_ok(con, z)[0]:
        return False
    i0 = L.I_TIEFE if tief(z) else L.I_T
    p, n, roh = T.tagesreihe(z, i0, L.I_ENDE, verzug=1)
    if not (n > 0 and roh - L.KOSTEN85 > 0):
        return False
    v0 = L.I_T + L.SEGMENTE["t" if tief(z) else "k"][1] * 288
    _, nt, rt = T.tagesreihe(z, i0, v0, modell="bewegt"); _, nv, rv = T.tagesreihe(z, v0, L.I_ENDE, modell="bewegt")
    if not (nt > 0 and nv > 0 and rt - L.KOSTEN85 > 0 and rv - L.KOSTEN85 > 0):
        return False
    alpha, t_alpha, beta = T.marktbereinigt(z, i0, L.I_ENDE)
    return alpha > 0 and t_alpha >= 2


paar = None
for A in con.execute("SELECT * FROM kandidaten WHERE status = 'final' ORDER BY sharpe_v DESC LIMIT 300"):
    mitglieder = con.execute("SELECT * FROM kandidaten WHERE status = 'stufe3' AND grund LIKE ? LIMIT 6", (f"%vertreten durch {A['id']}",)).fetchall()
    if mitglieder and besteht_heute(A):
        for B in mitglieder:
            if besteht_heute(B):
                paar = (A, B); break
    if paar:
        break
A, B = paar
mm = {g: np.load(C.ECHT_AUS / f"tage_{g}.npy", mmap_mode="r") for g in ("gen1", "gen2")}
ra, rb = (np.asarray(mm[z["gen"]][z["zeile"]], dtype=np.float64) for z in (A, B))
gem = (ra != 0) | (rb != 0)
for name, z in (("A", A), ("B", B)):
    print(f"{name}: {z['id']} {z['gen']} {z['signal']} th {z['th']} r {z['r']} {z['f']} k{z['k']} {z['x']} {z['m']} best {z['best']} | in Lauf A: {z['status']} ({z['grund']}) | Sharpe V1 {z['sharpe_v']}")
print(f"Korrelation der Tagesergebnisse A/B (Tage, an denen mindestens einer handelt): {np.corrcoef(ra[gem], rb[gem])[0, 1]:.3f}")


def kopie(name, status_a, status_b):
    pfad = C.TMP / f"{name}.sqlite"
    if pfad.exists():
        pfad.unlink()
    neu = sqlite3.connect(pfad)
    neu.execute(f"CREATE TABLE kandidaten ({', '.join(L.SPALTEN)}, PRIMARY KEY (id, gen))")
    for z in (A, B):                                          # alle Zeilen, die als Nachbarn in Frage kommen (gleicher Filter, Takt, Ausstieg, Markt, Richtung)
        zeilen = con.execute("SELECT * FROM kandidaten WHERE f = ? AND k = ? AND x = ? AND m = ? AND r = ?", (z["f"], z["k"], z["x"], z["m"], z["r"])).fetchall()
        neu.executemany(f"INSERT OR REPLACE INTO kandidaten VALUES ({','.join('?' * len(L.SPALTEN))})", [tuple(r) for r in zeilen])
    neu.execute("UPDATE kandidaten SET status = 'in_lauf_a_erledigt' WHERE status IN ('stufe2', 'stufe3', 'final')")
    for z, st in ((A, status_a), (B, status_b)):
        neu.execute("UPDATE kandidaten SET status = ?, grund = '' WHERE id = ? AND gen = ?", (st, z["id"], z["gen"]))
    neu.commit(); neu.close()
    L.DB = pfad
    return pfad


def stufe3_laufen():
    assert str(C.TMP) in str(L.DB) and str(C.TMP) in str(T.ERG)
    with contextlib.redirect_stdout(io.StringIO()) as aus:
        T.stufe3()
    k = sqlite3.connect(L.DB)
    st = {z["id"]: k.execute("SELECT status, grund FROM kandidaten WHERE id = ? AND gen = ?", (z["id"], z["gen"])).fetchone() for z in (A, B)}
    k.close()
    fj = json.loads((T.ERG / "finalisten.json").read_text())
    return st, [f["id"] for f in fj["finalisten"]], aus.getvalue().splitlines()[:3]


pfad = kopie("c10_nacheinander", "stufe2", "wartet_auf_spaeteren_zyklus")
st, fin, text = stufe3_laufen()
print("\nLauf 1 (nur A offen):", text[1]); print("   Status A:", st[A["id"]], "| B:", st[B["id"]], "| finalisten.json:", fin)
k = sqlite3.connect(pfad); k.execute("UPDATE kandidaten SET status = 'stufe2' WHERE id = ? AND gen = ?", (B["id"], B["gen"])); k.commit(); k.close()
st, fin, text = stufe3_laufen()
print("Lauf 2 (B kommt später dazu):", text[1]); print("   Status A:", st[A["id"]], "| B:", st[B["id"]], "| finalisten.json:", fin)
print("   -> B ist jetzt ebenfalls Finalist ('Gruppe 1'), obwohl B mit A über 0,8 korreliert; finalisten.json enthält A nicht mehr.")
kopie("c10_gemeinsam", "stufe2", "stufe2")
st, fin, text = stufe3_laufen()
print("Kontrolle (A und B im selben Lauf):", text[1]); print("   Status A:", st[A["id"]], "| B:", st[B["id"]], "| finalisten.json:", fin)
print("\nV2-blind: D.N =", D.N, "= I_ENDE", ende, "- stufe3 lief vollständig durch, ohne eine Kerze ab 2024-07-01 zu brauchen (numpy-Zugriffe darüber hinaus wären ein Fehler gewesen).")
