"""Kandidaten-Generator: SIGNAL x SCHWELLE x RICHTUNG x FILTER x TAKT x AUSSTIEG x MARKT, jede Einstellung genau einmal.

Der Hebel ist kein eigener Kandidat (er skaliert nur; die Risikoprüfung bestimmt ihn). Die Kennung ist der Hash der
Einstellung und damit reproduzierbar.
"""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fabrik import signale as S

SCHWELLEN = (1.5, 2.5, 3.5)
RICHTUNGEN = (1, -1)                          # 1 = mit dem Signal, -1 = gegen das Signal
TAKTE = (1, 3, 12)                            # geprüft alle 5, 15, 60 Minuten
# Name: (Haltedauer in Kerzen, Stop, Ziel, Nachzug-Abstand, Nachzug ab Gewinn, Signal-Ausstieg) – Stop/Ziel/Nachzug in Einheiten der Stundenschwankung
AUSSTIEGE = {"h15": (3, 0, 0, 0, 0, None), "h60": (12, 0, 0, 0, 0, None), "h240": (48, 0, 0, 0, 0, None), "h720": (144, 0, 0, 0, 0, None),
             "h240_stop2": (48, 2.0, 0, 0, 0, None), "h240_stop1.5_ziel3": (48, 1.5, 3.0, 0, 0, None), "h60_stop1.5_ziel1.5": (12, 1.5, 1.5, 0, 0, None),
             "h720_nachzug2": (144, 0, 0, 2.0, 0.0, None), "h720_zielnachzug": (144, 0, 0, 0.5, 1.0, None), "signal_h720": (144, 0, 0, 0, 0, 0.5)}
MAERKTE = {"top3": (0, 1, 2), "alle10": tuple(range(10)), "alt7": tuple(range(3, 10))}


def kennung(k: dict) -> str:
    return hashlib.sha1(json.dumps(k, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:12]


def aufgaben(signale=None, schwellen=SCHWELLEN, filter_=None, takte=TAKTE):
    """Eine Aufgabe = eine Einstiegsregel; sie liefert je Ausstieg und Markt einen Kandidaten."""
    for si, (name, familie, laenge, braucht) in enumerate(S.SIGNALE):
        if signale is not None and name not in signale:
            continue
        for th in schwellen:
            for r in RICHTUNGEN:
                for f in (filter_ or S.FILTER):
                    for k in takte:
                        yield {"si": si, "signal": name, "familie": familie, "braucht": braucht, "th": th, "r": r, "f": f, "k": k}


def kandidaten(aufgabe: dict, ausstiege=None, maerkte=None):
    for x in (ausstiege or AUSSTIEGE):
        for m in (maerkte or MAERKTE):
            k = {"s": aufgabe["signal"], "th": aufgabe["th"], "r": aufgabe["r"], "f": aufgabe["f"], "k": aufgabe["k"], "x": x, "m": m}
            yield kennung(k), k


if __name__ == "__main__":
    a = list(aufgaben())
    print(len(S.SIGNALE), "Signale ->", len(a), "Einstiegsregeln ->", len(a) * len(AUSSTIEGE) * len(MAERKTE), "Kandidaten")
