"""ENG-A: Unabhaengige Nachrechnung des Kandidaten (14-Tage-Trend, taker) ohne engine2, Vergleich mit engine2.
Nur lesend. Aufruf: cd swing-hybrid && NUMBA_CACHE_DIR=<scratch> .venv/bin/python -I -B <dieses skript>"""
import json, sys, time
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M

t0 = time.time()
G = json.loads(open("reports/suche_runde6.json").read())["gruppen"]
assert G["A"] == R.GRUPPE_A, G["A"]
m = R.markt(G["A"], vor=True)
slip = R.yubit_kosten(m.coins)[0]
print("Slippage-Annahme je Coin (bp):", dict(zip(m.coins, np.round(slip * 1e4, 3))))
w = R.auf_raster(m, M.basis(m))
l = R.lauf(m, w, taker=True, slip=slip, day_limit=9.0)
eng = l.daily_pnl(runner.MIT)
print(f"engine2 fertig nach {time.time()-t0:.0f} s; Bars {len(m.index)}, Tage {len(m.days)}")

# ---------- unabhaengige Rechnung ----------
N, T = m.c.shape
S = 1.0 / N
TAKER, REB = 0.0008, 0.85
idx = m.index
tag_ende = np.r_[np.nonzero(np.diff(m.day))[0], T - 1]            # letzter Bar je Tag
mein = np.zeros((len(tag_ende), N))
abw_signal = {}
summe = {"tv": 0.0, "fu": 0.0}
for j, coin in enumerate(m.coins):
    # Signal unabhaengig: Stundenschluss aus 5m-Rohdaten, Vergleich ZEITBASIERT mit dem Schluss 336 h frueher
    roh = R._lesen("5m", coin, True)
    h = roh["close"].resample("1h").last().dropna()
    alt = h.reindex(h.index - pd.Timedelta(hours=336)).to_numpy()
    sig = pd.Series(np.sign(h.to_numpy() / alt - 1), index=h.index + pd.Timedelta(hours=1))   # gilt ab Stundenschluss
    sig = sig.fillna(0.0)
    ziel = sig.reindex(idx.union(sig.index)).ffill().reindex(idx).fillna(0.0).to_numpy()
    abw_signal[coin] = int((ziel != w[j]).sum())
    o, c, f = m.o[j], m.c[j], m.fund[j]
    dpos = np.zeros(T); dcash = np.zeros(T); dtv = np.zeros(T)
    pos, held = 0.0, 0.0
    wechsel = np.nonzero(np.diff(ziel, prepend=ziel[0]) != 0)[0]
    kandidaten = sorted(set(wechsel.tolist()) | {1, T - 1})
    for t in kandidaten:
        tgt = 0.0 if t == T - 1 else ziel[t]
        if t == 0 or tgt == held:
            continue
        neu = tgt * S / o[t]
        dq = neu - pos
        px = o[t] * (1 + np.sign(dq) * slip[j])
        dpos[t] = dq; dcash[t] = -dq * px; dtv[t] = abs(dq) * px
        pos, held = neu, tgt
    posb = np.cumsum(dpos); cash = np.cumsum(dcash); tv = np.cumsum(dtv)
    vor = np.r_[0.0, posb[:-1]]                                   # Position VOR dem Fill dieses Bars zahlt Funding
    fu = np.cumsum(-vor * o * f)
    netto = cash + posb * c - TAKER * (1 - REB) * tv + fu
    kum = netto[tag_ende]
    mein[:, j] = np.diff(np.r_[0.0, kum])
    summe["tv"] += tv[-1]; summe["fu"] += fu[-1]
mein = pd.DataFrame(mein, index=m.days, columns=m.coins)
# Zweiter Durchgang: dieselbe unabhaengige Kontorechnung, aber mit den Zielgewichten der Forschung (isoliert die Arithmetik)
def konto(j, ziel):
    o, c, f = m.o[j], m.c[j], m.fund[j]
    dpos = np.zeros(T); dcash = np.zeros(T); dtv = np.zeros(T); pos, held = 0.0, 0.0
    for t in sorted(set(np.nonzero(np.diff(ziel, prepend=ziel[0]) != 0)[0].tolist()) | {1, T - 1}):
        tgt = 0.0 if t == T - 1 else ziel[t]
        if t == 0 or tgt == held:
            continue
        neu = tgt * S / o[t]; dq = neu - pos; px = o[t] * (1 + np.sign(dq) * slip[j])
        dpos[t] = dq; dcash[t] = -dq * px; dtv[t] = abs(dq) * px; pos, held = neu, tgt
    posb = np.cumsum(dpos); tv = np.cumsum(dtv); fu = np.cumsum(-np.r_[0.0, posb[:-1]] * o * f)
    return np.diff(np.r_[0.0, (np.cumsum(dcash) + posb * c - TAKER * (1 - REB) * tv + fu)[tag_ende]])
gleich = pd.DataFrame({coin: konto(j, w[j]) for j, coin in enumerate(m.coins)}, index=m.days)
print(f"Arithmetik isoliert (gleiche Zielgewichte): groesste Abweichung Tagesergebnis je Coin engine2 vs. Nachrechnung = {(gleich - eng).abs().to_numpy().max():.3e}")

d = (mein - eng).abs().to_numpy()
print("Signal: abweichende 5m-Bars je Coin (zeitbasiert vs. research.shift(336)):", abw_signal)
print(f"Tagesergebnis je Coin: groesste Abweichung engine2 vs. Nachrechnung = {d.max():.3e}")
print(f"Summe Taker-Volumen: engine {l.TV[-1]:.6f} / nach {summe['tv']:.6f};  Funding: engine {l.FU[-1]:.6f} / nach {summe['fu']:.6f}")
# Identitaet: Summe der Tagesergebnisse = Endstand
print(f"Identitaet Summe Tage = equity[-1]: {eng.to_numpy().sum():.10f} vs {l.equity(runner.MIT)[-1]:.10f}")

def kenn(x, von, bis):
    if von is not None: x = x[x.index >= pd.Timestamp(von)]
    if bis is not None: x = x[x.index < pd.Timestamp(bis)]
    k = 1.0 + x.cumsum()
    return {"tage": len(x), "N": round(float(x.sum()), 4), "jahr": round(float(x.mean() * 365), 4),
            "sharpe": round(float(x.mean() / x.std() * np.sqrt(365)), 3),
            "dd_rel_spitze": round(float(((k.cummax() - k) / k.cummax()).max()), 4),
            "dd_abs_startkapital": round(float((x.cumsum().cummax().clip(lower=0) - x.cumsum()).max()), 4)}
FEN = {"D1": (None, R.D1_ENDE), "D2": (R.D1_ENDE, R.SPLIT), "Entwicklung": (None, R.SPLIT), "Pruefung": (R.SPLIT, None), "Gesamt": (None, None)}
out = {}
for name, (a, b) in FEN.items():
    out[name] = {"engine2": kenn(eng.sum(axis=1), a, b), "nachrechnung": kenn(mein.sum(axis=1), a, b)}
    print(name, json.dumps(out[name]))
# Sicht-Funktion der Forschung (Fensterlogik) zum Vergleich
for name, (a, b) in FEN.items():
    s = R.sicht(l, a, b)
    print(f"  research.sicht {name}: N {s['N']:.4f} jahr_N {s['jahr_N']:.4f} sharpe {s['sharpe']:.3f} dd_mit {s['dd_mit']:.4f} G {s['G']:.4f} F {s['F']:.4f} R {s['R']:.4f} vol_tag {s['vol_tag']:.4f} trades {s['trades']} halte_h {s['halte_h']:.1f}")
# Kostenzerlegung gesamt
print("Gesamt: brutto", round(float(l.eq_gross[-1]), 4), "TV", round(float(l.TV[-1]), 2), "Gebuehr voll", round(float(0.0008 * l.TV[-1]), 4),
      "Rebate", round(float(0.0008 * 0.85 * l.TV[-1]), 4), "Funding", round(float(l.FU[-1]), 4))
json.dump(out, open(sys.argv[1], "w"), indent=1) if len(sys.argv) > 1 else None
print(f"fertig nach {time.time()-t0:.0f} s")
