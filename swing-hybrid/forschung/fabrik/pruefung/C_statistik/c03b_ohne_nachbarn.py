"""C03b: die Kandidaten, die allein deshalb abgelehnt wurden, weil sie gar keinen Nachbarn haben. Warum fehlen die Nachbarn?"""
import sys
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
from fabrik import trichter as T
con = C.ro()
kand = con.execute("SELECT * FROM kandidaten WHERE status = 'verworfen_3' AND grund = 'Nachbar-Einstellungen überwiegend negativ'").fetchall()
for z in kand:
    ok, n, pos = T.nachbarn_ok(con, z)
    if n == 0:
        roh = con.execute("SELECT gen, th, n_t, n85_t, status, best IS NOT NULL FROM kandidaten WHERE signal = ? AND f = ? AND k = ? AND x = ? AND m = ? AND r = ? ORDER BY th",
                          (z["signal"], z["f"], z["k"], z["x"], z["m"], z["r"])).fetchall()
        print(z["id"], z["gen"], z["signal"], "th", z["th"], "r", z["r"], z["f"], "k", z["k"], z["x"], z["m"], "| n_t", z["n_t"], "n85_t", z["n85_t"], "t85_t", z["t85_t"], "V1", z["n85_v"], z["t85_v"])
        print("     alle Zeilen derselben Regel (gen, th, n_t, n85_t, status, mit Bestätigung):", [tuple(r) for r in roh])
