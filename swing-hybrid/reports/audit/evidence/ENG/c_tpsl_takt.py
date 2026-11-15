"""ENG-C: Test 2 (Stop 5 % / Ziel 15 %): Pruefung am Stundenschluss (hybrid.tpsl, Rueckrechnung) gegen Pruefung
bei jedem Bot-Lauf (alle 5 Minuten, gegen den Fuellkurs des Einstiegs). NUR Entwicklungszeitraum (bis 2025-04-01).
Keine Parameterwahl: tp=0.15, sl=0.05 fest wie in config_lauf_tpsl.json. Nur lesend."""
import json, sys, time
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from numba import njit
from hybrid import research as R, runner, mutationen as M, tpsl

@njit
def botlogik(o, sig, slip, tp, sl, takt, minute_idx):
    """Zustand wie in vorwaertstest/bot.py: Pruefung zu Beginn jedes `takt`-ten 5m-Bars mit dem Kurs dieses Moments (Open),
    Einstiegskurs = Fuellkurs (Open +/- Slippage). Gibt Zielgewicht je Bar und Zaehler (stop, ziel, einstiege) zurueck."""
    n = len(o); out = np.zeros(n); z = np.zeros(3)
    pos, ein, gesperrt = 0.0, 0.0, 0.0
    for t in range(n):
        if minute_idx[t] % takt != 0:
            out[t] = pos; continue
        s = sig[t]
        if gesperrt != 0.0 and s != gesperrt:
            gesperrt = 0.0
        if pos != 0.0 and s != pos:
            pos = 0.0
        if pos == 0.0 and s != 0.0 and gesperrt == 0.0:
            pos = s; ein = o[t] * (1.0 + s * slip); z[2] += 1
        elif pos != 0.0:
            r = (o[t] / ein - 1.0) * pos
            if tp > 0 and r >= tp:
                gesperrt = pos; pos = 0.0; z[1] += 1
            elif sl > 0 and r <= -sl:
                gesperrt = pos; pos = 0.0; z[0] += 1
        out[t] = pos
    return out, z

t0 = time.time()
m = R.markt(R.GRUPPE_A, vor=True)
slip = R.yubit_kosten(m.coins)[0]
sig5 = R.auf_raster(m, M.basis(m))
minute_idx = np.asarray(((m.index - m.index.normalize()) // pd.Timedelta(minutes=5)), dtype=np.int64)   # 0..287
ende = int(m.index.searchsorted(pd.Timestamp(R.SPLIT)))
TP, SL = 0.15, 0.05

def kenn(l, w, name, z=None):
    x = l.daily_pnl(runner.MIT).sum(axis=1)
    x = x[x.index < pd.Timestamp(R.SPLIT)]
    k = 1.0 + x.cumsum()
    e = {"variante": name, "jahr": round(float(x.mean() * 365), 4), "sharpe": round(float(x.mean() / x.std() * np.sqrt(365)), 3),
         "einbruch": round(float(((k.cummax() - k) / k.cummax()).max()), 4), "im_markt": round(float(np.abs(w[:, :ende]).mean()), 4),
         "umsatz_tag": round(float(l.TV[ende - 1] / (ende / 288)), 4)}
    if z is not None:
        e.update(stops=int(z[0]), ziele=int(z[1]), einstiege=int(z[2]))
    return e

erg = []
wb = sig5
erg.append(kenn(R.lauf(m, wb, taker=True, slip=slip, day_limit=9.0), wb, "Kandidat (Test 1), Rueckrechnung"))
wh = R.auf_raster(m, tpsl.gewichte(m, tp=TP, sl=SL))
erg.append(kenn(R.lauf(m, wh, taker=True, slip=slip, day_limit=9.0), wh, "sl5_tp15 Rueckrechnung hybrid.tpsl (Stundenschluss)"))
for takt, name in ((12, "Bot-Logik, Lauf 1x je Stunde"), (1, "Bot-Logik, Lauf alle 5 Minuten (Ist-Betrieb)")):
    w = np.zeros_like(sig5); z = np.zeros(3)
    for j in range(len(m.coins)):
        # Zaehler nur im Entwicklungszeitraum
        wj, zj = botlogik(m.o[j, :ende], sig5[j, :ende], slip[j], TP, SL, takt, minute_idx[:ende])
        w[j, :ende] = wj; z += zj
    erg.append(kenn(R.lauf(m, np.ascontiguousarray(w), taker=True, slip=slip, day_limit=9.0), w, name, z))
# Latenz Test 1: Signal 5 Minuten spaeter ausgefuehrt (ein 5m-Bar)
wl = np.ascontiguousarray(np.roll(sig5, 1, axis=1)); wl[:, 0] = 0.0
erg.append(kenn(R.lauf(m, wl, taker=True, slip=slip, day_limit=9.0), wl, "Kandidat, Ausfuehrung 5 Minuten spaeter"))
t = pd.DataFrame(erg).set_index("variante")
pd.set_option("display.width", 250)
print("Entwicklungszeitraum", m.index[0], "bis", R.SPLIT, "| Gruppe A, Einsatz 100 %, Yubit-Kosten mit Rebate, ohne Tageslimit")
print(t.to_string())
if len(sys.argv) > 1:
    open(sys.argv[1], "w").write(json.dumps(erg, indent=1))
print(f"fertig nach {time.time()-t0:.0f} s")
