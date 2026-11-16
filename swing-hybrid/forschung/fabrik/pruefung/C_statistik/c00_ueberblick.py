"""C00 Überblick (nur lesend): Bestand der Datenbank, Anteile je Generation, Abgleich mit statistik.json."""
import json, sqlite3, sys
sys.path.insert(0, 'forschung')
from fabrik import lauf as L, daten as D, trichter as T
con = sqlite3.connect('file:data/fabrik/forschung.sqlite?mode=ro', uri=True)
print("I_T, I_TIEFE, I_V1, I_ENDE:", L.I_T, L.I_TIEFE, L.I_V1, L.I_ENDE, "| N_TAGE", L.N_TAGE, "| SEGMENTE", L.SEGMENTE)
print("I_V2, I_V2ENDE, D.N:", T.I_V2, T.I_V2ENDE, D.N, "| V2-Tage (I_V2ENDE - I_V2) / 288 =", (T.I_V2ENDE - T.I_V2) / 288, "| I_V2 % 288 =", T.I_V2 % 288, "| I_T % 288 =", L.I_T % 288)
print("Raster:", D.RASTER[0], "bis", D.RASTER[-1], "| RASTER[I_ENDE] =", D.RASTER[L.I_ENDE])
print("\nStatus je Generation:")
for r in con.execute("SELECT gen, status, COUNT(*) FROM kandidaten GROUP BY gen, status ORDER BY gen, status"):
    print("  ", r)
print("\nLäufe:", con.execute("SELECT * FROM laeufe").fetchall())
K = "braucht != 't' AND (best IS NULL OR best NOT LIKE '%tiefe%' AND best NOT LIKE '%liq_entzug%')"
Tf = "(braucht = 't' OR best LIKE '%tiefe%' OR best LIKE '%liq_entzug%')"
print("\nAnteil Stufe 1 bestanden (unter gültigen, n_t >= 200), getrennt nach Generation und Gruppe; Zufallserwartung laut statistik(): 0.0228")
for name, wo in (("Kurs/Volumen/Derivate", K), ("Orderbuch-Tiefe", Tf)):
    for gen in ("gen1", "gen2", None):
        g = "1=1" if gen is None else f"gen = '{gen}'"
        n, s1, s2, tmax = con.execute(f"SELECT COUNT(*), SUM(status != 'verworfen_1'), SUM(status IN ('stufe2','stufe3','final','validiert','verworfen_3','verworfen_4')), MAX(t85_t) "
                                      f"FROM kandidaten WHERE n_t >= 200 AND {wo} AND {g}").fetchone()
        print(f"  {name:<22} {str(gen or 'beide'):<6} gültig {n:>7}  Stufe 1 {s1:>6} = {s1 / n:.4f}  Stufe 2 {s2:>6} = {s2 / n:.5f}  max t85_t {tmax}")
print("\nstatistik.json:", json.dumps(json.load(open('forschung/fabrik/ergebnisse/statistik.json'))["gruppen"], ensure_ascii=False))
print("\nDoppelte Kennungen über Generationen:", con.execute("SELECT COUNT(*) FROM (SELECT id FROM kandidaten GROUP BY id HAVING COUNT(*) > 1)").fetchone())
print("Schwellen je Generation:", con.execute("SELECT gen, GROUP_CONCAT(DISTINCT th) FROM kandidaten GROUP BY gen").fetchall())
print("Finalisten nach Generation/Tiefe:", con.execute(f"SELECT gen, {Tf} AS tiefe, COUNT(*) FROM kandidaten WHERE status = 'final' GROUP BY 1, 2").fetchall())
print("Gründe Stufe 3:", con.execute("SELECT grund, COUNT(*) FROM kandidaten WHERE status = 'verworfen_3' GROUP BY 1").fetchall())
import os
print("schlusspruefung.json vorhanden:", os.path.exists('forschung/fabrik/ergebnisse/schlusspruefung.json'))
