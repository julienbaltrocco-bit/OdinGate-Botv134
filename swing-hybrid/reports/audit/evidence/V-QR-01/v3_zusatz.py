"""V-QR-01 (3): Zusatzrechnungen. Nur lesend; Kern wie v2 (gegen engine2 abgeglichen)."""
import sys
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from numba import njit
from hybrid import mutationen as M, research as R, tpsl

FEE = 0.0008 * (1 - 0.85)

@njit(cache=True)
def pfad(o, c, w, fund, slip, S, t0, t1, modus, bars_tag):
    """Konto je Kerze. modus 0: Groesse fest am Startkapital. modus 1: Groesse beim Einstieg = Konto x S.
    modus 2: wie 1, zusaetzlich jeden Tag um 00:00 jede Position auf Konto x S zurueckstellen (konstanter Hebel)."""
    N = o.shape[0]; n = t1 - t0
    pos = np.zeros(N); held = np.zeros(N); cash = np.zeros(N); tv = 0.0; fu = 0.0
    konto = np.empty(n); eins = np.empty(n); k_prev = 1.0
    for i in range(n):
        t = t0 + i
        for j in range(N):
            tgt = w[j, t]; ot = o[j, t]; r = fund[j, t]
            if r != 0.0 and pos[j] != 0.0:
                fu -= pos[j] * ot * r
            neu_tag = modus == 2 and (t % bars_tag) == 0 and tgt != 0.0
            if tgt != held[j] or neu_tag:
                basis = S * (max(k_prev, 0.0) if modus > 0 else 1.0)
                neu = tgt * basis / ot
                dq = neu - pos[j]
                if dq != 0.0:
                    px = ot * (1.0 + (1.0 if dq > 0 else -1.0) * slip[j])
                    cash[j] -= dq * px; tv += abs(dq) * px
                pos[j] = neu; held[j] = tgt
        g = 0.0; e = 0.0
        for j in range(N):
            g += cash[j] + pos[j] * c[j, t]; e += abs(pos[j]) * c[j, t]
        k = 1.0 + g - FEE * tv + fu
        konto[i] = k; eins[i] = e; k_prev = k
    return konto, eins

mA = R.markt(R.GRUPPE_A, vor=True)
wA = R.auf_raster(mA, M.basis(mA))
kA = R.yubit_kosten(R.GRUPPE_A)[0]
idx = mA.index; T = len(idx); SPLIT = int(idx.searchsorted(pd.Timestamp(R.SPLIT)))
assert idx[0].hour == 0 and idx[0].minute == 0

# ---- 1) Absoluter Rueckgang in Startkapital-Einheiten, 5-Minuten-Basis, Hebel 1 (Dauerlauf) ----
k1, e1 = pfad(mA.o, mA.c, wA, mA.fund, kA, 0.1, 0, T, 0, 288)
for name, a, b in (("Entwicklung", 0, SPLIT), ("Pruefzeitraum", SPLIT, T)):
    x = k1[a:b] - (k1[a - 1] if a > 0 else 1.0)
    hoch = np.maximum.accumulate(np.maximum(x, 0.0)); dd = hoch - x; i = int(np.argmax(dd))
    ih = int(np.argmax(x[:i + 1]))
    print(f"1) {name}: groesster absoluter Rueckgang (5-min-Schluss, Hebel 1) {dd.max():.4f} Startkapital, Hoch {idx[a + ih]} -> Tief {idx[a + i]} | x3 = {3 * dd.max():.3f}")

# ---- 2) 09.12.2024: Verlust des Tages in % des Kontos vom Vorabend, je nach Starttag (Hebel 3, feste Groesse) ----
print("2) 09.12.2024, Hebel 3, feste Groesse am Startkapital, frischer Start am ...:")
t_vor = int(idx.searchsorted(pd.Timestamp("2024-12-08 23:55"))); t_ab = int(idx.searchsorted(pd.Timestamp("2024-12-09 23:55")))
zeilen = []
for s in ["2021-08-15", "2023-07-01", "2024-01-01", "2024-06-01", "2024-09-01", "2024-10-01", "2024-11-01", "2024-11-15", "2024-12-01", "2024-12-05", "2024-12-08"]:
    t0 = int(idx.searchsorted(pd.Timestamp(s)))
    k, e = pfad(mA.o, mA.c, wA, mA.fund, kA, 0.3, t0, t_ab + 1, 0, 288)
    kv, ka = k[t_vor - t0], k[t_ab - t0]; tief = k[t_vor - t0:].min()
    zeilen.append((s, kv, e[t_vor - t0], e[t_vor - t0] / kv, ka - kv, (ka - kv) / kv * 100, (tief - kv) / kv * 100))
print(pd.DataFrame(zeilen, columns=["start", "konto_vorabend", "einsatz_vorabend", "einsatz/konto", "tagesergebnis_startkap", "tagesergebnis_%konto", "tagestief_%konto"]).round(3).to_string(index=False))
# alle Starttage der 400 Tage davor
alle = []
for d in pd.date_range("2023-11-01", "2024-12-08", freq="1D"):
    t0 = int(idx.searchsorted(d))
    k, e = pfad(mA.o, mA.c, wA, mA.fund, kA, 0.3, t0, t_ab + 1, 0, 288)
    kv, ka = k[t_vor - t0], k[t_ab - t0]
    if k[:t_vor - t0 + 1].min() > 0:
        alle.append((ka - kv) / kv)
alle = np.array(alle)
print(f"   Starttage 01.11.2023 bis 08.12.2024 mit Konto > 0 bis zum Vorabend: {len(alle)}; Tagesergebnis 09.12.2024 in % des Vorabend-Kontos: "
      f"schlechtestes {alle.min() * 100:.1f} %, Median {np.median(alle) * 100:.1f} %, bestes {alle.max() * 100:.1f} %")

# ---- 3) Zinseszins-Varianten, Hebel 3 und 1 ----
print("3) Groesse am laufenden Kontostand:")
for name, a, b in (("Entwicklung", 0, SPLIT), ("Pruefzeitraum", SPLIT, T)):
    for hebel in (1.0, 3.0):
        for modus, text in ((1, "Einstieg = Konto x Hebel/10, Stueckzahl fest bis Wechsel"), (2, "zusaetzlich taeglich 00:00 auf Konto x Hebel/10 zurueckgestellt")):
            k, e = pfad(mA.o, mA.c, wA, mA.fund, kA, hebel / 10, a, b, modus, 288)
            sp = np.maximum.accumulate(k); jahre = (b - a) / 288 / 365
            tagk = k[287::288]; tr = np.diff(np.concatenate([[1.0], tagk])) / np.concatenate([[1.0], tagk[:-1]])
            cagr = k[-1] ** (1 / jahre) - 1 if k[-1] > 0 else float("nan")
            print(f"   {name} Hebel {hebel:g}, {text}: Ende {k[-1]:.3f}, CAGR {cagr * 100:.1f} %, Einbruch {((sp - k) / sp).max() * 100:.1f} %, Tief {k.min():.3f}, schlechtester Tag {tr.min() * 100:.1f} % ({idx[a + 287 + 288 * int(np.argmin(tr))].date()}), Konto <= 0: {bool((k <= 0).any())}")

# ---- 4) Test 2 (Stop 5 % / Ziel 15 %): frischer Start je Tag, Hebel 3, feste Groesse (Naeherung: Gewichte des Dauerlaufs) ----
@njit(cache=True)
def frisch(o, c, w, fund, slip, S, starts, t_ende):
    N = o.shape[0]; out = np.empty((len(starts), 3))
    for si in range(len(starts)):
        t0 = starts[si]
        pos = np.zeros(N); held = np.zeros(N); cash = np.zeros(N); tv = 0.0; fu = 0.0; tief = 1.0; i0 = -1.0; k = 1.0
        for t in range(t0, t_ende):
            for j in range(N):
                tgt = w[j, t]; ot = o[j, t]; r = fund[j, t]
                if r != 0.0 and pos[j] != 0.0:
                    fu -= pos[j] * ot * r
                if tgt != held[j]:
                    neu = tgt * S / ot; dq = neu - pos[j]
                    if dq != 0.0:
                        px = ot * (1.0 + (1.0 if dq > 0 else -1.0) * slip[j])
                        cash[j] -= dq * px; tv += abs(dq) * px
                    pos[j] = neu; held[j] = tgt
            g = 0.0
            for j in range(N):
                g += cash[j] + pos[j] * c[j, t]
            k = 1.0 + g - FEE * tv + fu
            if k < tief: tief = k
            if k <= 0.0 and i0 < 0: i0 = t
        out[si, 0] = tief; out[si, 1] = i0; out[si, 2] = k
    return out

wT = R.auf_raster(mA, tpsl.VARIANTEN["sl5_tp15"](mA))
tag0 = np.flatnonzero((idx.hour == 0) & (idx.minute == 0))
kT, eT = pfad(mA.o, mA.c, wT, mA.fund, kA, 0.1, 0, T, 0, 288)
for name, a, b in (("Entwicklung", 0, SPLIT), ("Pruefzeitraum", SPLIT, T)):
    x = kT[a:b] - (kT[a - 1] if a > 0 else 1.0); kk = 1 + x; sp = np.maximum.accumulate(np.maximum(kk, 1.0))
    dd = np.maximum.accumulate(np.maximum(x, 0.0)) - x
    st = tag0[(tag0 >= a) & (tag0 < b)]
    r = frisch(mA.o, mA.c, wT, mA.fund, kA, 0.3, st, b)
    print(f"4) sl5_tp15 {name}: Hebel 1 Einbruch rel. Spitze {((sp - kk) / sp).max():.4f}, absoluter Rueckgang {dd.max():.4f} (x3 = {3 * dd.max():.3f}); "
          f"Hebel 3 frischer Start je Tag: Konto <= 0 bei {(r[:, 1] >= 0).mean() * 100:.1f} %, <= 0,5 bei {(r[:, 0] <= 0.5).mean() * 100:.1f} % der {len(st)} Starttage, schlechtestes Tief {r[:, 0].min():.3f}")

# ---- 5) 10.10.2025 21:00 ----
t = int(idx.searchsorted(pd.Timestamp("2025-10-10 21:00")))
print("5) Stunde 10.10.2025 21:00 UTC (12 Kerzen): Zielgewicht, Tief und Schluss gegen Schluss der Vorstunde")
for j, coin in enumerate(mA.coins):
    vor = mA.c[j, t - 1]; lo = mA.l[j, t:t + 12].min(); hi = mA.h[j, t:t + 12].max(); cl = mA.c[j, t + 11]
    print(f"   {coin:5s} Ziel {wA[j, t]:+.0f}  Tief {lo / vor - 1:+.3f}  Hoch {hi / vor - 1:+.3f}  Schluss {cl / vor - 1:+.3f}")
