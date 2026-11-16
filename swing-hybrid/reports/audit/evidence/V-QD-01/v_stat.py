"""V-QD-01: unabhaengige Gegenpruefung von QD-01, Teil 1 (Punktschaetzung, Unsicherheit, Zufallstest, Vorperiode).
Nur lesend: importiert src/hybrid, schreibt ausschliesslich nach stdout."""
import sys, time, math, json
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, mutationen as M

t0 = time.time()
A = R.GRUPPE_A
SPLIT = pd.Timestamp(R.SPLIT)
K, fehlt = R.yubit_kosten(A)
print("Yubit-Slippage je Coin (2 x halbe Spanne):", dict(zip(A, np.round(K * 1e4, 3))), "bp | fehlend:", fehlt)
print("Gebuehren aus config.yaml: maker", runner.MAKER, "taker", runner.TAKER, "rebate", runner.MIT.rebate)


def sharpe(x):
    x = np.asarray(x, float)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(365))


def t_wert(x):
    x = np.asarray(x, float)
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x))))


def t_hac(x, lag=10):
    """t-Wert mit Newey-West-Standardfehler (Bartlett-Gewichte)."""
    x = np.asarray(x, float); n = len(x); e = x - x.mean()
    v = (e @ e) / n
    for k in range(1, lag + 1):
        v += 2 * (1 - k / (lag + 1)) * (e[k:] @ e[:-k]) / n
    return float(x.mean() / math.sqrt(v / n))


# ------------------------------------------------------------------ eigene Nachrechnung der Tagesreihe ----
def eigene_tagesreihe(m, w, slip, rebate=0.85, hebel=1.0):
    """Unabhaengig von engine2: sofortige Ausfuehrung zum Open +/- Slippage, feste Stueckzahl je Position,
    Funding auf die Position vor dem Tausch, Taker-Gebuehr abzueglich Rebate. Gibt Tagesergebnis (Summe ueber Coins)."""
    N, T = m.c.shape; S = hebel / N
    letzte = np.r_[np.nonzero(np.diff(m.day))[0], T - 1]            # letzte Kerze je Tag
    summe = np.zeros(len(letzte))
    for j in range(N):
        ziel = w[j].copy(); ziel[0] = 0.0; ziel[-1] = 0.0            # erste Kerze: keine Order; letzte: Schlussabrechnung
        wechsel = np.nonzero(np.diff(np.r_[0.0, ziel]) != 0)[0]
        dq_a = np.zeros(T); dcash = np.zeros(T); dtv = np.zeros(T)
        pos = 0.0
        for t in wechsel:
            p = m.o[j, t]
            neu = ziel[t] * S / p
            dq = neu - pos
            px = p * (1 + np.sign(dq) * slip[j])
            dq_a[t] = dq; dcash[t] = -dq * px; dtv[t] = abs(dq) * px; pos = neu
        q = np.cumsum(dq_a)
        q_vor = np.r_[0.0, q[:-1]]
        fu = np.cumsum(-q_vor * m.o[j] * m.fund[j])
        netto = np.cumsum(dcash) + q * m.c[j] - runner.TAKER * (1 - rebate) * np.cumsum(dtv) + fu
        summe += np.diff(np.r_[0.0, netto[letzte]])
    return pd.Series(summe, index=m.days)


# --------------------------------------------------------------------------------------- Bootstrap ----
def stationaer(n, ziehungen, block, rng):
    """Stationaerer Bootstrap (Politis/Romano) ueber geometrische Blocklaengen; eigene Umsetzung."""
    nb = int(n / block * 3) + 30
    idx = np.empty((ziehungen, n), dtype=np.int64)
    for b in range(ziehungen):
        while True:
            lens = rng.geometric(1.0 / block, nb)
            if lens.sum() >= n:
                break
        starts = rng.integers(0, n, nb)
        ende = np.cumsum(lens)
        versatz = np.repeat(ende - lens, lens)[:n]
        idx[b] = (np.repeat(starts, lens)[:n] + np.arange(n) - versatz) % n
    return idx


def kreisblock(n, ziehungen, block, rng):
    nb = -(-n // block)
    starts = rng.integers(0, n, (ziehungen, nb))
    return ((starts[:, :, None] + np.arange(block)[None, None, :]) % n).reshape(ziehungen, -1)[:, :n]


def band(x, idx):
    b = x[idx]
    bm = b.mean(axis=1) * 365
    bs = b.mean(axis=1) / b.std(axis=1, ddof=1) * math.sqrt(365)
    return (np.percentile(bm, [5, 95]), np.percentile(bs, [5, 95]), float((bm <= 0).mean()), np.percentile(bs, [2.5, 97.5]))


print("\n=== A. Kandidat: Tagesreihe (Hebel 1, sofortige Ausfuehrung, ohne Tageslimit, Gruppe A)")
reihen = {}
for vor in (True, False):
    m = R.markt(A, vor=vor)
    sig_m, sig_r = M.basis(m), R.tsmom(m, 336)
    gleich = bool((sig_m.fillna(0) == sig_r.fillna(0)).all().all())
    w = R.auf_raster(m, sig_m)
    for bez, slip in (("yubit", K), ("5bp", np.full(len(A), 0.0005))):
        l = R.lauf(m, w, taker=True, slip=slip, day_limit=9.0)
        mit = l.daily_pnl(runner.MIT).sum(axis=1); ohne = l.daily_pnl(runner.OHNE).sum(axis=1)
        eig = eigene_tagesreihe(m, w, slip); eig0 = eigene_tagesreihe(m, w, slip, rebate=0.0)
        reihen[(vor, bez)] = (mit, ohne)
        print(f"vor={vor!s:5s} Kosten={bez:5s} | M.basis == R.tsmom(336): {gleich} | Sperrtage {int(l.st[4])} | "
              f"groesste Abweichung eigene Nachrechnung gegen engine2: mit Rebate {np.abs(eig.to_numpy() - mit.to_numpy()).max():.2e}, "
              f"ohne Rebate {np.abs(eig0.to_numpy() - ohne.to_numpy()).max():.2e}")
    if vor:
        m_haupt, w_haupt = m, w
    else:
        m_ohne_vor, w_ohne_vor = m, w

print("\n=== B. Punktschaetzung und Unsicherheit")
rng = np.random.default_rng(20261115)
ERG = {}
for (vor, bez), (mit, ohne) in reihen.items():
    for reb, tg in (("mit Rebate", mit), ("ohne Rebate", ohne)):
        for nm, x in (("Entwicklung", tg[tg.index < SPLIT]), ("Pruefzeitraum", tg[tg.index >= SPLIT])):
            xv = x.to_numpy(); n = len(xv)
            zeile = (f"vor={vor!s:5s} {bez:5s} {reb:11s} {nm:13s} Tage {n:4d}  Ertrag/Jahr {xv.mean()*365:+.3f}  Vola/Jahr {xv.std(ddof=1)*math.sqrt(365):.3f}  "
                     f"Sharpe {sharpe(xv):+.3f}  t {t_wert(xv):+.2f}  t(HAC,10) {t_hac(xv):+.2f}  AK1 {pd.Series(xv).autocorr(1):+.3f}")
            if vor and bez == "yubit":
                i_s = stationaer(n, 10000, 20, rng)
                (m5, m95), (s5, s95), ant, (s2, s97) = band(xv, i_s)
                zeile += (f"\n      stationaerer Bootstrap (Block 20, 10.000): Ertrag/Jahr 90-% [{m5:+.3f}, {m95:+.3f}]  Sharpe 90-% [{s5:+.2f}, {s95:+.2f}]  "
                          f"Sharpe 95-% [{s2:+.2f}, {s97:+.2f}]  Anteil Mittel <= 0: {ant:.3f}")
                ERG[(reb, nm)] = dict(tage=n, ertrag=xv.mean() * 365, sharpe=sharpe(xv), t=t_wert(xv), m5=m5, m95=m95, s5=s5, s95=s95, anteil=ant)
                if reb == "mit Rebate":
                    for bl in (5, 40):
                        (a5, a95), (b5, b95), an, _ = band(xv, stationaer(n, 4000, bl, rng))
                        zeile += f"\n      stationaer Block {bl:2d} (4.000): Ertrag/Jahr [{a5:+.3f}, {a95:+.3f}]  Sharpe [{b5:+.2f}, {b95:+.2f}]  Anteil <= 0: {an:.3f}"
                    (a5, a95), (b5, b95), an, _ = band(xv, kreisblock(n, 10000, 20, rng))
                    zeile += f"\n      Kreisblock 20 (10.000):     Ertrag/Jahr [{a5:+.3f}, {a95:+.3f}]  Sharpe [{b5:+.2f}, {b95:+.2f}]  Anteil <= 0: {an:.3f}"
                    (a5, a95), (b5, b95), an, _ = band(xv, rng.integers(0, n, (10000, n)))
                    zeile += f"\n      ohne Bloecke (10.000):      Ertrag/Jahr [{a5:+.3f}, {a95:+.3f}]  Sharpe [{b5:+.2f}, {b95:+.2f}]  Anteil <= 0: {an:.3f}"
                    se_lo = math.sqrt((1 + 0.5 * (xv.mean() / xv.std(ddof=1)) ** 2) / n) * math.sqrt(365)
                    zeile += f"\n      Naeherungsformel (Lo 2002, unabhaengige Tage): Sharpe 90-% [{sharpe(xv)-1.645*se_lo:+.2f}, {sharpe(xv)+1.645*se_lo:+.2f}]"
            print(zeile)

mit, ohne = reihen[(True, "yubit")]
dev, pru = mit[mit.index < SPLIT], mit[mit.index >= SPLIT]
d = dev.mean() - pru.mean(); se = math.sqrt(dev.var(ddof=1) / len(dev) + pru.var(ddof=1) / len(pru))
print(f"\nUnterschied Entwicklung minus Pruefzeitraum (Yubit, mit Rebate): t = {d/se:.2f}")
print(f"Hebel 3 skaliert Ertrag und Band linear: Pruefzeitraum 90-%-Band Ertrag/Jahr bei Hebel 3 = [{3*ERG[('mit Rebate','Pruefzeitraum')]['m5']:+.2f}, {3*ERG[('mit Rebate','Pruefzeitraum')]['m95']:+.2f}]")
n_noetig = (1.645 / (ERG[("mit Rebate", "Pruefzeitraum")]["sharpe"])) ** 2
print(f"Jahre, die ein wahrer Sharpe von {ERG[('mit Rebate','Pruefzeitraum')]['sharpe']:.3f} fuer t = 1,645 (einseitig 5 %) braucht: {n_noetig:.1f}")

print("\n=== C. Zufallstest des Projekts (zeitlich verschobenes Signal)")
def verschoben(m, w, slip, seed, anzahl, nur_stunden=False):
    rng = np.random.default_rng(seed); T = w.shape[1]
    echt = R.lauf(m, w, taker=True, slip=slip, day_limit=9.0).daily_pnl(runner.MIT).sum(axis=1)
    ep, ed = float(echt[echt.index >= SPLIT].sum()), float(echt[echt.index < SPLIT].sum())
    zp, zd = [], []
    for _ in range(anzahl):
        k = int(rng.integers(288 * 30, T - 288 * 30))
        if nur_stunden:
            k -= k % 12
        x = R.lauf(m, np.ascontiguousarray(np.roll(w, k, axis=1)), taker=True, slip=slip, day_limit=9.0).daily_pnl(runner.MIT).sum(axis=1)
        zp.append(float(x[x.index >= SPLIT].sum())); zd.append(float(x[x.index < SPLIT].sum()))
    zp, zd = np.array(zp), np.array(zd)
    return dict(pruef_perzentil=float((zp < ep).mean() * 100), pruef_echt=ep, pruef_median=float(np.median(zp)), pruef_p90=float(np.percentile(zp, 90)),
                pruef_max=float(zp.max()), entw_perzentil=float((zd < ed).mean() * 100), entw_echt=ed, entw_median=float(np.median(zd)),
                entw_p90=float(np.percentile(zd, 90)), entw_max=float(zd.max()))

gesp = json.load(open("/home/user/OdinGate-Botv134/swing-hybrid/reports/kandidat.json"))["zufall_pruefung"]
print("gespeichert reports/kandidat.json zufall_pruefung:", json.dumps(gesp))
r = verschoben(m_ohne_vor, w_ohne_vor, np.full(len(A), 0.0005), 11, 200)
print("nachgerechnet wie scripts/kandidat_pruefen.py:60-67 (5 bp, ohne Vorlauf, seed 11, 200):", json.dumps({k: round(v, 6) for k, v in r.items()}))
print(f"   Abweichung gegen gespeichert: Perzentil {r['pruef_perzentil'] - gesp['perzentil']:+.2f}, echt {r['pruef_echt'] - gesp['echt']:+.2e}, Median {r['pruef_median'] - gesp['median']:+.2e}")
r = verschoben(m_haupt, w_haupt, K, 11, 200)
print("Yubit-Kosten, mit Vorlauf, seed 11, 200 (wie Pruefer):", json.dumps({k: round(v, 4) for k, v in r.items()}))
r = verschoben(m_haupt, w_haupt, K, 987654, 600, nur_stunden=True)
print("Yubit-Kosten, mit Vorlauf, anderer seed, 600 Verschiebungen um ganze Stunden:", json.dumps({k: round(v, 4) for k, v in r.items()}))

print("\n=== D. Zusaetzliche Evidenz ausserhalb der Auswahl: Vorperiode 02/2020-08/2021, Gruppe A, Yubit-Kosten mit Rebate")
mv = R.markt(A, R.VOR_START, R.VOR_ENDE, vor=True)
wv = R.auf_raster(mv, R.tsmom(mv, 336))
erst = {c: str(R._lesen("5m", c, True).index[0].date()) for c in A}
print("erste Kerze je Coin:", erst)
lv = R.lauf(mv, wv, taker=True, slip=K, day_limit=9.0)
vt = lv.daily_pnl(runner.MIT).sum(axis=1); vo = lv.daily_pnl(runner.OHNE).sum(axis=1)
for nm, x in (("Vorperiode mit Rebate", vt), ("Vorperiode ohne Rebate", vo)):
    xv = x.to_numpy()
    print(f"{nm:24s} Tage {len(xv)}  Ertrag/Jahr {xv.mean()*365:+.3f}  Sharpe {sharpe(xv):+.3f}  t {t_wert(xv):+.2f}  t(HAC,10) {t_hac(xv):+.2f}")
for nm, teile in (("Vorperiode + Pruefzeitraum (nicht zur Auswahl benutzt)", [vt, pru]), ("Vorperiode + Entwicklung + Pruefzeitraum", [vt, dev, pru]),
                  ("Entwicklung + Pruefzeitraum", [dev, pru])):
    xv = np.concatenate([t.to_numpy() for t in teile])
    (m5, m95), (s5, s95), ant, _ = band(xv, stationaer(len(xv), 5000, 20, rng))
    print(f"{nm:55s} Tage {len(xv)}  Ertrag/Jahr {xv.mean()*365:+.3f}  Sharpe {sharpe(xv):+.3f}  t {t_wert(xv):+.2f}  t(HAC,10) {t_hac(xv):+.2f}  "
          f"Bootstrap 90-% Sharpe [{s5:+.2f}, {s95:+.2f}]  Anteil Mittel <= 0: {ant:.4f}")
# juengste Zeit: rollierend
for tage in (365, 730):
    x = mit.iloc[-tage:].to_numpy()
    print(f"letzte {tage} Tage (bis {mit.index[-1].date()}): Ertrag/Jahr {x.mean()*365:+.3f}  Sharpe {sharpe(x):+.3f}  t {t_wert(x):+.2f}")
je = mit.groupby(mit.index.year).agg(["sum", "count"])
print("Kalenderjahre (Summe Tagesergebnis, Hebel 1, Yubit mit Rebate):", {int(k): round(float(v), 3) for k, v in je["sum"].items()})
print(f"\nfertig nach {time.time() - t0:.0f} s")
