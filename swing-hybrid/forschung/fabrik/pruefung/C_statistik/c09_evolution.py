"""C09 evolution.py im Trockenlauf: die echte Funktion erzeugen() liest die Datenbank von Lauf A nur lesend, alle Ausgaben gehen nach tmp/.
1) Ergibt sie NACH Stufe 3 (Status final / stufe3 / verworfen_3 schon gesetzt) dieselbe Aufgabenliste wie die gespeicherte von 23:25 UTC (vor Stufe 3)?
   Dann steuert das Ergebnis aus V1 die Elternwahl nicht.
2) Welche Spalten bestimmen die Elternwahl? Gegenprobe: V1-Spalten in einer Kopie der Elternzeilen verwürfelt.
3) Was passiert bei einer dritten Generation aus gen2 (evolution.py gen3 gen2)? Entstehen Einstellungen, die es schon gibt?"""
import sys, json, sqlite3, hashlib, inspect
from pathlib import Path
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
from fabrik import evolution as EV, lauf as L, generator as G

print("Code-Stand:", C.stand())
ECHT_DB = 'data/fabrik/forschung.sqlite'


class NurLesen:                                               # ersetzt in diesem Prozess das Modul sqlite3 innerhalb von evolution.py
    @staticmethod
    def connect(*a, **k):
        return sqlite3.connect(f'file:{ECHT_DB}?mode=ro', uri=True)


EV.sqlite3 = NurLesen
EV.F = C.TMP / "ev"
L.AUS = C.TMP / "ev"
(C.TMP / "ev").mkdir(parents=True, exist_ok=True)
if hasattr(EV.D, "SPEICHER") and "D.SPEICHER /" in inspect.getsource(EV.erzeugen):
    raise SystemExit("evolution schreibt wieder nach D.SPEICHER - Trockenlauf abgebrochen")

print("1) Trockenlauf gen2 aus gen1 auf dem heutigen Stand der Datenbank (nach Stufe 3):")
EV.erzeugen("gen2x", "gen1")
neu = json.loads((C.TMP / "ev" / "aufgaben_gen2x.json").read_text())
alt = json.loads(Path("data/fabrik/aufgaben_gen2.json").read_text())
norm = lambda a: json.dumps({k: v for k, v in a.items() if k != "key"}, sort_keys=True)
print(f"   gespeicherte Liste (vor Stufe 3 erzeugt): {len(alt)} Aufgaben | Trockenlauf: {len(neu)} Aufgaben | gleich Stück für Stück: {[norm(a) for a in alt] == [norm(a) for a in neu]}")
eltern = sorted({a["eltern"] for a in neu})
print(f"   Eltern-Regeln: {len(eltern)}")

con = sqlite3.connect(f'file:{ECHT_DB}?mode=ro', uri=True)
abfrage = ("SELECT signal, th, r, f, k, MAX(t85_t) AS t FROM kandidaten WHERE gen = 'gen1' AND status != 'ungültig' AND status NOT LIKE 'verworfen_1' AND "
           "status NOT LIKE 'verworfen_2' AND best IS NULL GROUP BY signal, th, r, f, k ORDER BY t DESC")
alle = con.execute(abfrage).fetchall()
print(f"   Regeln mit mindestens einem Kandidaten nach Stufe 2: {len(alle)}; gewählt werden die {EV.MAX_ELTERN} mit dem höchsten t85_t; Grenze t = {alle[EV.MAX_ELTERN - 1][5]}, nächster {alle[EV.MAX_ELTERN][5]}")

print("2) Gegenprobe: Elternwahl allein aus T-Größen nachgebaut (Bedingungen von lauf.bewerte auf den Spalten n_t, roh_t, t_roh_t, n85_t, t85_t, n85_h1, n85_h2, n85_2x_t)")
eigen = con.execute("SELECT signal, th, r, f, k, MAX(t85_t) AS t FROM kandidaten WHERE gen = 'gen1' AND best IS NULL AND n_t >= 200 AND roh_t > 0 AND t_roh_t >= 2 AND n85_t > 0 AND t85_t >= 2 "
                    "AND n85_h1 > 0 AND n85_h2 > 0 AND n85_2x_t > 0 GROUP BY signal, th, r, f, k ORDER BY t DESC LIMIT ?", (EV.MAX_ELTERN,)).fetchall()
e1 = {f"{s}|{th}|{r}|{f}|{k}" for s, th, r, f, k, t in eigen}
print(f"   Eltern laut evolution {len(eltern)}, allein aus T-Spalten nachgebaut {len(e1)}, gemeinsam {len(e1 & set(eltern))}")
v = con.execute("SELECT AVG(n85_v > 0 AND t85_v >= 1) FROM kandidaten WHERE gen = 'gen1' AND status IN ('stufe3','final','verworfen_3')").fetchone()[0]
print(f"   Anteil der gen1-Kandidaten nach Stufe 2, die V1 bestehen: {v:.3f} - Eltern werden trotzdem alle nach T gewählt (auch die in V1 gescheiterten bleiben Eltern).")

print("3) Trockenlauf einer dritten Generation aus gen2:")
EV.erzeugen("gen3x", "gen2")
g3 = json.loads((C.TMP / "ev" / "aufgaben_gen3x.json").read_text())
def kennungen(aufgaben):
    for a in aufgaben:
        for xname, x in a["ausstiege"].items():
            for mname in a["maerkte"]:
                k = {"s": a["signal"], "th": a["th"], "r": a["r"], "f": a["f"], "k": a["k"], "x": list(x), "m": mname}
                if a.get("best"):
                    k["b"] = [a["best"]["signal"], a["best"]["th"], a["best"]["r"]]
                yield G.kennung(k)
vorhanden = {r[0] for r in con.execute("SELECT id FROM kandidaten")}
probe = set(kennungen(alt[:200]))
print(f"   Probe der Kennungsrechnung: {len(probe & vorhanden)} von {len(probe)} Kennungen der ersten 200 gen2-Aufgaben stehen in der Datenbank")
ids3 = list(kennungen(g3))
doppelt = sum(1 for i in ids3 if i in vorhanden)
print(f"   gen3 hätte {len(ids3)} Kandidaten; davon mit einer Kennung, die schon gerechnet ist: {doppelt} ({doppelt / max(len(ids3), 1):.1%}) - sie würden unter (id, 'gen3') ein zweites Mal gespeichert und gezählt")
