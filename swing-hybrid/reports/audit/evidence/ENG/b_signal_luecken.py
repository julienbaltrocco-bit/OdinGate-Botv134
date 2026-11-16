"""ENG-B: Zeilenbasierter shift(336) der Forschung gegen zeitbasierten Vergleich (wie im Bot). Nur lesend."""
import sys
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from hybrid import research as R, mutationen as M

m = R.markt(R.GRUPPE_A, vor=True)
c = R._close(m)
print("Stunden im gemeinsamen Index:", len(c), "von", c.index[0], "bis", c.index[-1])
voll = pd.date_range(c.index[0], c.index[-1], freq="1h")
fehl = voll.difference(c.index)
print("im gemeinsamen Stundenindex fehlende Stunden:", len(fehl), list(fehl[:10]))
b = M.basis(m)
for coin in m.coins:
    h = m.h1[coin]["close"]
    luecken = pd.date_range(h.index[0], h.index[-1], freq="1h").difference(h.index)
    nan_im_verbund = c[coin].loc[h.index[0]:].isna().sum()
    zeit = np.sign(h / h.reindex(h.index - pd.Timedelta(hours=336)).to_numpy() - 1)
    zeile = b[coin].reindex(h.index)
    ab = (zeit.fillna(0.0) != zeile)
    ab_handel = ab.loc[R.START:]
    print(f"{coin:5s} erste Stunde {h.index[0]}  fehlende Stunden {len(luecken)}  NaN im Verbund {nan_im_verbund}  "
          f"Signal-Abweichungen gesamt {int(ab.sum())}, ab {R.START}: {int(ab_handel.sum())}"
          + (f"  ({ab_handel[ab_handel].index[0]} bis {ab_handel[ab_handel].index[-1]})" if ab_handel.any() else ""))
    if len(luecken):
        print("       Luecken:", [str(x) for x in luecken[:6]], "..." if len(luecken) > 6 else "")
# Gleichstand: wie oft ist das Signal exakt 0 (Schluss == Schluss vor 336 h) im Handelszeitraum?
bb = b.loc[R.START:]
print("Stunden mit Signal 0 je Coin ab START:", {k: int((bb[k] == 0).sum()) for k in bb.columns})
