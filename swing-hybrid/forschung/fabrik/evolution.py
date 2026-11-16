"""Evolution: aus den Kandidaten, die Stufe 2 bestanden haben (also allein aus dem Training T), neue Varianten erzeugen.

  .venv/bin/python -I forschung/fabrik/evolution.py gen2 [gen1]     schreibt data/fabrik/aufgaben_gen2.json
  .venv/bin/python -I forschung/fabrik/lauf.py gen2 data/fabrik/aufgaben_gen2.json

Mutationen je Eltern-Einstiegsregel: benachbarte Schwellen, zehn weitere Ausstiege, ein zweites Signal als
Bestätigung. V1 und V2 steuern die Evolution nicht. Jede Variante trägt die Kennung ihrer Eltern-Regel.
"""
import json
import sqlite3
import sys
from pathlib import Path

F = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F))
from fabrik import daten as D, generator as G, lauf as L, signale as S

MAX_ELTERN = 300
NEUE_AUSSTIEGE = {"h30": (6, 0, 0, 0, 0, None), "h120": (24, 0, 0, 0, 0, None), "h480": (96, 0, 0, 0, 0, None), "h120_stop2": (24, 2.0, 0, 0, 0, None),
                  "h240_stop3": (48, 3.0, 0, 0, 0, None), "h480_stop2_ziel4": (96, 2.0, 4.0, 0, 0, None), "signal0_h720": (144, 0, 0, 0, 0, 0.0),
                  "signal1_h720": (144, 0, 0, 0, 0, 1.0), "signal0.5_h240": (48, 0, 0, 0, 0, 0.5), "h240_nachzug1.5": (48, 0, 0, 1.5, 0.0, None)}
BESTAETIGUNG = ("tiefe_5", "kaufdruck_12", "mom_12", "boll_48", "oi_kurs_1h", "aufschlag", "volspitze_1", "btcfuehrt_3")


def erzeugen(ziel: str, quelle: str):
    con = sqlite3.connect(L.DB)
    eltern = con.execute("SELECT signal, familie, braucht, th, r, f, k, MAX(t85_t) AS t, COUNT(*) FROM kandidaten WHERE gen = ? AND status != 'ungültig' AND "
                         "status NOT LIKE 'verworfen_1' AND status NOT LIKE 'verworfen_2' AND best IS NULL GROUP BY signal, th, r, f, k ORDER BY t DESC LIMIT ?",
                         (quelle, MAX_ELTERN)).fetchall()
    alle_ausstiege = {**G.AUSSTIEGE, **NEUE_AUSSTIEGE}
    aufgaben, gesehen = [], set()

    def dazu(a):
        key = json.dumps([a["signal"], a["th"], a["r"], a["f"], a["k"], a.get("best"), sorted(a["ausstiege"])], sort_keys=True)
        if key not in gesehen:
            gesehen.add(key); aufgaben.append(a)

    for signal, familie, braucht, th, r, f, k, t, _ in eltern:
        basis = {"si": S.NAMEN.index(signal), "signal": signal, "familie": familie, "braucht": braucht, "r": r, "f": f, "k": k, "maerkte": G.MAERKTE,
                 "eltern": f"{signal}|{th}|{r}|{f}|{k}"}
        dazu({**basis, "th": th, "ausstiege": NEUE_AUSSTIEGE})                                    # neue Ausstiege für die Eltern-Regel
        for th2 in (th - 0.5, th + 0.5):
            if 1.0 <= th2 <= 4.5 and th2 not in G.SCHWELLEN:
                dazu({**basis, "th": th2, "ausstiege": alle_ausstiege})                           # benachbarte Schwelle
        for b in BESTAETIGUNG:
            if b == signal:
                continue
            for r2 in (1, -1):
                bi = S.NAMEN.index(b)
                dazu({**basis, "th": th, "ausstiege": G.AUSSTIEGE, "best": {"si": bi, "signal": b, "th": 1.0, "r": r2, "braucht": S.SIGNALE[bi][3]}})
    (L.AUS / f"aufgaben_{ziel}.json").write_text(json.dumps(aufgaben))
    (F / "fabrik/ergebnisse").mkdir(parents=True, exist_ok=True)
    (F / "fabrik/ergebnisse/ausstiege.json").write_text(json.dumps(alle_ausstiege, indent=1))
    n = sum(len(a["ausstiege"]) * len(a["maerkte"]) for a in aufgaben)
    print(f"{ziel}: {len(eltern)} Eltern-Regeln -> {len(aufgaben)} Aufgaben -> {n} Kandidaten")


if __name__ == "__main__":
    erzeugen(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "gen1")
