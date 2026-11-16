"""Stufe-3-Bedingung "eine Kerze Verzögerung": kern.sim verzögert den Signal-Ausstieg um ZWEI Kerzen (liest wert[j-1] und steigt erst zu j+2 aus).
Wirkung auf echten Daten (T und V1) für alle Kandidaten mit Signal-Ausstieg, die die Verzögerungsprüfung erreicht haben.
Eigener Simulator: a) Nachbau von kern.sim (doppelt), b) genau eine Kerze Verzögerung für Einstieg UND Signal-Ausstieg."""
import sqlite3, sys, json, time
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/B_buchung')
import pruef_lib as P
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
con.row_factory = sqlite3.Row
sx_namen = [k for k, v in P.AUSSTIEGE.items() if v[5] is not None]
print("Ausstiege mit Signal-Ausstieg:", sx_namen)
q = ",".join("?" * len(sx_namen))
zeilen = [dict(r) for r in con.execute(f"SELECT * FROM kandidaten WHERE x IN ({q}) AND (status IN ('final','stufe3') OR (status = 'verworfen_3' AND grund IN ('eine Kerze Verzögerung', 'nach Abzug des Marktes kein gesicherter Ertrag')))", sx_namen)]
print("Kandidaten mit Signal-Ausstieg in der Verzögerungsprüfung:", len(zeilen), {s: sum(1 for z in zeilen if (z['status'], z['grund'][:10]) == s) for s in {(z['status'], z['grund'][:10]) for z in zeilen}})
start, erg = time.time(), []
for z in zeilen:
    out = []
    for doppelt in (True, False):
        r = P.nachbau(z, verzug=1, sx_doppelt=doppelt)
        n = r["n_tag"].sum()
        out.append(r["roh_tag"].sum() / n - 2.4 if n else -9e9)
    r0 = P.nachbau(z)
    n0 = r0["n_tag"].sum()
    erg.append((z, r0["roh_tag"].sum() / n0 - 2.4, out[0], out[1]))
d = np.array([e[3] - e[2] for e in erg])
print(f"n85 über T+V1 mit Verzögerung: Mittel wie kern.sim {np.mean([e[2] for e in erg]):.2f} bp, mit genau einer Kerze {np.mean([e[3] for e in erg]):.2f} bp, ohne Verzögerung {np.mean([e[1] for e in erg]):.2f} bp")
print(f"Differenz (eine Kerze minus kern.sim): Mittel {d.mean():+.2f} bp, Median {np.median(d):+.2f}, min {d.min():+.2f}, max {d.max():+.2f}; |Differenz| > 1 bp bei {(np.abs(d) > 1).sum()} von {len(d)}")
kern_ok = np.array([e[2] > 0 for e in erg]); ein_ok = np.array([e[3] > 0 for e in erg])
db_ok = np.array([not (e[0]['status'] == 'verworfen_3' and e[0]['grund'] == 'eine Kerze Verzögerung') for e in erg])
print(f"Nachbau von kern.sim trifft das Urteil der Datenbank: {(kern_ok == db_ok).sum()} von {len(erg)}")
print(f"Urteil kippt bei genau einer Kerze: zu Unrecht verworfen (kern.sim <= 0, eine Kerze > 0): {(~kern_ok & ein_ok).sum()}; zu Unrecht bestanden (kern.sim > 0, eine Kerze <= 0): {(kern_ok & ~ein_ok).sum()}")
for e in [e for e in erg if (e[2] > 0) != (e[3] > 0)][:12]:
    z = e[0]
    print(f"   {z['gen']} {z['id']} {z['signal']} th {z['th']} r {z['r']:+d} {z['f']} k{z['k']} {z['x']} {z['m']} | Status {z['status']} ({z['grund']}) | n85 ohne Verzug {e[1]:.2f}, kern.sim {e[2]:.2f}, eine Kerze {e[3]:.2f}")
kipp = [e for e in erg if (e[2] > 0) != (e[3] > 0)]
print("gekippte Urteile nach heutigem Status:", {st: sum(1 for e in kipp if e[0]['status'] == st and e[2] > 0) for st in ('final', 'stufe3')}, "(bestanden mit kern.sim, durchgefallen mit einer Kerze);",
      sum(1 for e in kipp if e[2] <= 0), "umgekehrt")
print("gekippt je Ausstieg:", {x: sum(1 for e in kipp if e[0]['x'] == x) for x in sx_namen}, "| je Richtung r:", {r: sum(1 for e in kipp if e[0]['r'] == r) for r in (1, -1)})
json.dump([{"id": e[0]['id'], "gen": e[0]['gen'], "status": e[0]['status'], "grund": e[0]['grund'], "x": e[0]['x'], "n85_ohne": e[1], "n85_kern": e[2], "n85_eine_kerze": e[3]} for e in erg],
          open('forschung/fabrik/pruefung/B_buchung/10_verzug_signalausstieg.json', 'w'), indent=0)
print(f"{time.time()-start:.0f} s")
