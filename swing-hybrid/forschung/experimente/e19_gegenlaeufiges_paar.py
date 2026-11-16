"""E19: Kern der Idee "gleichzeitig Long und Short, Verlierer früh schließen" an echten Minutenkursen (Protokoll Abschnitt 31)."""
import json
import sys
from pathlib import Path

import numpy as np
from numba import njit

F = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F))
from alpha import kern as K

VON, BIS = "2021-08-15", "2024-06-30 23:59"


@njit(cache=True)
def paare(o, h, l, c, starts, s, max_min):
    """Je Start: Ergebnis vor Kosten in bp (beide Seiten zusammen), 1 wenn die Gewinnerseite ihr Ziel erreicht, Dauer in Minuten."""
    out = np.zeros((len(starts), 3))
    for k in range(len(starts)):
        a = starts[k]
        e = o[a]
        oben, unten = e * (1 + s), e * (1 - s)
        d, j = 0, a
        ende = min(a + max_min, len(o) - 1)
        while j < ende:                                           # erste Grenze: welche Seite verliert?
            if h[j] >= oben and l[j] <= unten:
                d = 2; break                                      # beide in einer Minute: ungünstig, beide Seiten gestoppt
            if h[j] >= oben:
                d = 1; break
            if l[j] <= unten:
                d = -1; break
            j += 1
        if d == 0:                                                # keine Grenze erreicht: beide zum Schluss glatt, Ergebnis null
            out[k, 2] = j - a
            continue
        if d == 2:
            out[k, 0], out[k, 2] = -2 * s * 1e4, j - a
            continue
        ziel, stop = e * (1 + d * 2 * s), e * (1 - d * s)        # Gewinnerseite: Ziel bei 2 s, Stop bei -s vom Einstieg
        erg = np.nan
        j += 1
        while j < ende:
            hoch = h[j] >= ziel if d > 0 else l[j] <= ziel
            tief = l[j] <= stop if d > 0 else h[j] >= stop
            if tief:                                              # ungünstige Grenze zuerst gewertet
                erg = -s * 1e4; break
            if hoch:
                erg = 2 * s * 1e4; out[k, 1] = 1; break
            j += 1
        if erg != erg:
            erg = d * (c[min(j, len(c) - 1)] / e - 1) * 1e4       # Zeit abgelaufen: zum Schlusskurs
        out[k, 0], out[k, 2] = erg - s * 1e4, j - a              # Gewinnerseite minus Verlust der gestoppten Seite
    return out


def haupt():
    slip = K.slippage_bp(["BTC", "ETH", "SOL"])
    aus = {"hinweis": "bp des Werts einer Seite je Paar; vier Orders je Paar", "zeitraum": [VON, BIS], "ergebnisse": []}
    for coin in ("BTC", "ETH", "SOL"):
        m = K.lesen("1m", coin).loc[VON:BIS]
        o, h, l, c = (m[x].to_numpy(np.float64) for x in ("open", "high", "low", "close"))
        starts = np.flatnonzero((m.index.hour % 4 == 0) & (m.index.minute == 0))
        starts = starts[starts < len(o) - 1500]
        for s in (0.002, 0.005, 0.010):
            r = paare(o, h, l, c, starts, s, 1440)
            kosten85 = 4 * (8 * 0.15 + slip[coin]); kosten0 = 4 * (8 + slip[coin])
            n = len(r)
            se = r[:, 0].std() / np.sqrt(n)
            e = {"coin": coin, "stop_pct": s * 100, "paare": int(n), "vor_kosten_bp": round(float(r[:, 0].mean()), 2), "t_vor_kosten": round(float(r[:, 0].mean() / se), 2),
                 "kosten_mit_rebate_bp": round(kosten85, 2), "netto_mit_rebate_bp": round(float(r[:, 0].mean() - kosten85), 2),
                 "netto_ohne_rebate_bp": round(float(r[:, 0].mean() - kosten0), 2), "gewinner_erreicht_ziel": round(float(r[:, 1].mean()), 3),
                 "dauer_min_median": float(np.median(r[:, 2])), "netto_in_prozent_des_stops": round(float((r[:, 0].mean() - kosten85) / (s * 1e4) * 100), 1)}
            aus["ergebnisse"].append(e)
            print(e)
    (F / "ergebnisse/e19_gegenlaeufiges_paar.json").write_text(json.dumps(aus, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    haupt()
