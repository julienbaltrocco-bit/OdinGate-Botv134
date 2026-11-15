"""Strategie „Orderbuch-Stütze“ für den Papier-Runner (nur Standardbibliothek, läuft überall).

Rechnet dieselbe Regel wie die Forschung (forschung/experimente/e10_ausstiege.py, Variante X3):
  U  = (K - V) / (K + V), K/V = Auftragswert bis `tiefe_pct` unter/über dem Kurs, Mittel je 5-Minuten-Kerze
  z  = (U - Mittel der letzten `fenster` Kerzen) / Standardabweichung (mindestens `min_perioden` Werte)
  Einstieg bei |z| >= einstieg_z zur Eröffnung der nächsten Kerze, Richtung = Vorzeichen von z
  Ausstieg, sobald z * Richtung < ausstieg_z (Schluss einer Kerze -> Eröffnung der nächsten), spätestens nach `zeitlimit` Kerzen
Die Parität zur Forschung prüft forschung/tests/test_papier_paritaet.py.
"""
import math

DATEN = ("tiefe", "kerzen")       # was der Runner je Coin und Tag laden muss


def z_werte(u, fenster, min_perioden):
    z = [math.nan] * len(u)
    for i in range(len(u)):
        w = [x for x in u[max(0, i - fenster + 1): i + 1] if x == x]
        if len(w) < min_perioden or u[i] != u[i]:
            continue
        m = sum(w) / len(w)
        s = math.sqrt(sum((x - m) ** 2 for x in w) / (len(w) - 1))
        if s > 0:
            z[i] = (u[i] - m) / s
    return z


def trades(kerzen, u, p, start_ms):
    """kerzen: Liste (zeit_ms, open, high, low, close), lückenlos sortiert; u: Übergewicht je Kerze (nan = fehlt).
    Gibt Trades zurück; ein Trade ohne Ausstieg (Daten enden vorher) hat aus=None und gilt als offen."""
    z = z_werte(u, p["fenster"], p["min_perioden"])
    n, frei, out = len(kerzen), 0, []
    for i in range(n):
        if not (abs(z[i]) >= p["einstieg_z"]):
            continue
        a = i + 1
        if a < frei or a >= n or kerzen[a][0] < start_ms:
            continue
        r = 1.0 if z[i] > 0 else -1.0
        b = a + p["zeitlimit"]
        for j in range(a, a + p["zeitlimit"]):
            if j >= n:
                b = None
                break
            if z[j] * r < p["ausstieg_z"]:
                b = j + 1
                break
        if b is not None and b >= n:
            b = None
        ende = n - 1 if b is None else b
        schlimmst = min(k[3] for k in kerzen[a: ende + 1]) if r > 0 else max(k[2] for k in kerzen[a: ende + 1])
        out.append({"ein": kerzen[a][0], "aus": None if b is None else kerzen[b][0], "richtung": r, "ein_kurs": kerzen[a][1],
                    "aus_kurs": kerzen[-1][4] if b is None else kerzen[b][1], "z": round(z[i], 3),
                    "schlimmst_bp": round((schlimmst / kerzen[a][1] - 1) * r * 1e4, 1), "ein_idx": a, "aus_idx": b})
        if b is None:
            break
        frei = b
    return out
