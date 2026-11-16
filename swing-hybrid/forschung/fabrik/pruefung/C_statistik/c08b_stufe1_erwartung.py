"""C08b Was ist die Zufallserwartung für Stufe 1 (t_roh >= 2, Ergebnis nach Slippage und Funding, vor Gebühr)?
statistik() setzt 2,28 % an (Erwartungswert null). Ohne Wissen verliert ein Trade aber im Mittel die Slippage. Bootstrap auf 20.000 echten
Tagesreihen aus gen1 (Kurs/Volumen/Derivate, nur T). Näherung: die Reihe 'netto mit Rebate' wird je Tag gleichmäßig um die Gebühr angehoben."""
import sys, math
import numpy as np, pandas as pd
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
import c02_rc_eichung as E
from fabrik import lauf as L, generator as G

con = C.ro()
g = pd.read_sql("SELECT zeile, signal, m, n_t, n_v, t_roh_t, roh_t, status FROM kandidaten WHERE gen = 'gen1' AND n_t >= 200 AND braucht != 't'", con)
rng = np.random.default_rng(12)
s = g.iloc[np.sort(rng.choice(len(g), 20000, replace=False))].reset_index(drop=True)
X = np.asarray(np.load(C.ECHT_AUS / 'tage_gen1.npy', mmap_mode='r')[s["zeile"].to_numpy()], dtype=np.float64)[:, :685]
slip = np.load('data/fabrik/slip_bp.npy')
ohne = s["signal"].str.startswith(("btcfuehrt", "relstaerke", "korrbruch")).to_numpy()
abzug = np.array([2 * slip[[c for c in G.MAERKTE[m] if not (o and c == 0)]].mean() * nt / (len([c for c in G.MAERKTE[m] if not (o and c == 0)]) * 685)
                  for m, o, nt in zip(s["m"], ohne, s["n_t"])])
idx = E.idx_schnell(685, 200, 10, rng)
W = np.stack([np.bincount(ix, minlength=685) for ix in idx]).astype(np.float64) / 685
for name, mittel in (("Erwartungswert null (Annahme in statistik)", np.zeros(len(s))), ("ohne Wissen: Slippage geht verloren", -abzug)):
    Xn = X - X.mean(1, keepdims=True) + mittel[:, None]
    mb, qb = Xn @ W.T, (Xn * Xn) @ W.T
    var = np.maximum(qb - mb ** 2, 0) * 685 / 684
    t = np.where(var > 0, mb / np.sqrt(np.where(var > 0, var, 1)) * math.sqrt(685), 0)
    print(f"{name}: Anteil t >= 2 = {np.mean(t >= 2):.4f} (Streuung über 200 Welten {np.mean(t >= 2, axis=0).std():.4f})")
beob = ((g["t_roh_t"] >= 2) & (g["roh_t"] > 0)).mean()
print(f"beobachtet in gen1 (Kurs/Volumen/Derivate, {len(g)} gültige): {beob:.4f} | in statistik.json ausgewiesen (gen1 und gen2 vermischt): 0.0428 gegen 0.0228")
