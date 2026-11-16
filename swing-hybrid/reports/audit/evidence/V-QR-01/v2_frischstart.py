"""V-QR-01 (2): eigener Rechenkern (5-Minuten-Raster, nur Drehsignal, feste Stueckzahl ab Einstieg, Taker zum Open
plus Slippage, Funding, Gebuehr 0,08 % mit 85 % Rebate). Zielgewichte und Marktfelder kommen aus src/hybrid (nur gelesen).

Fragen:
 A) Stimmt der eigene Kern mit engine2 ueberein (Lauf ab 15.08.2021, Hebel 1)?
 B) Einsatz (Summe |Stueck| x Kurs) im Zeitverlauf.
 C) FRISCHER Start an jedem Kalendertag mit Hebel 3, Groesse fest am Startkapital (wie vorwaertstest/bot.py:165),
    ohne Tageslimit, ohne Liquidation: wie oft faellt das Konto auf <= 0 bzw. <= 0,5?
    Zum Vergleich die Naeherung des Pruefers (dieselbe Tagesreihe des Dauerlaufs, mal 3).
 D) Groesse am laufenden Kontostand (Zinseszins, Einstieg mit Konto x Hebel / 10): echter Lauf statt Naeherung.
"""
import json, sys
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from numba import njit
from hybrid import mutationen as M, research as R

AUS = sys.argv[1]
FEE = 0.0008 * (1 - 0.85)

@njit(cache=True)
def kern(o, c, h, l, w, fund, slip, S, t0, t1, zins, mm):
    """Gibt (konto je Kerze [Schluss], einsatz je Kerze, konto_unguenstig je Kerze) zurueck. Konto: Start = 1.
    zins=True: Groesse beim Einstieg = Konto(Vorkerze) x S; sonst S (Startkapital).
    mm: nicht benutzt in der Rechnung (nur Platzhalter)."""
    N = o.shape[0]; n = t1 - t0
    pos = np.zeros(N); held = np.zeros(N); cash = np.zeros(N)
    tv = 0.0; fu = 0.0
    konto = np.empty(n); eins = np.empty(n); kext = np.empty(n)
    k_prev = 1.0
    for i in range(n):
        t = t0 + i
        for j in range(N):
            tgt = w[j, t]; ot = o[j, t]
            r = fund[j, t]
            if r != 0.0 and pos[j] != 0.0:
                fu -= pos[j] * ot * r
            if tgt != held[j]:
                basis = S * (k_prev if zins else 1.0)
                if basis < 0.0:
                    basis = 0.0
                neu = tgt * basis / ot
                dq = neu - pos[j]
                if dq != 0.0:
                    px = ot * (1.0 + (1.0 if dq > 0 else -1.0) * slip[j])
                    cash[j] -= dq * px; tv += abs(dq) * px
                pos[j] = neu; held[j] = tgt
        g = 0.0; e = 0.0; gx = 0.0
        for j in range(N):
            g += cash[j] + pos[j] * c[j, t]
            e += abs(pos[j]) * c[j, t]
            gx += cash[j] + pos[j] * (l[j, t] if pos[j] > 0 else h[j, t])
        k = 1.0 + g - FEE * tv + fu
        konto[i] = k; eins[i] = e; kext[i] = 1.0 + gx - FEE * tv + fu
        k_prev = k
    return konto, eins, kext

@njit(cache=True)
def frisch(o, c, h, l, w, fund, slip, S, starts, t_ende):
    """Fuer jeden Startindex: Konto-Tief (Schlusskurse), Index erstes Konto <= 0 (-1 = nie), Index erstes <= 0.5, Endstand,
    groesstes Verhaeltnis Einsatz/Konto solange Konto > 0, Konto-Tief am unguenstigsten Kurs der Kerze."""
    N = o.shape[0]; out = np.empty((len(starts), 7))
    for si in range(len(starts)):
        t0 = starts[si]
        pos = np.zeros(N); held = np.zeros(N); cash = np.zeros(N)
        tv = 0.0; fu = 0.0; tief = 1.0; i0 = -1.0; i5 = -1.0; lev = 0.0; k = 1.0; tiefx = 1.0; ix0 = -1.0
        for t in range(t0, t_ende):
            for j in range(N):
                tgt = w[j, t]; ot = o[j, t]
                r = fund[j, t]
                if r != 0.0 and pos[j] != 0.0:
                    fu -= pos[j] * ot * r
                if tgt != held[j]:
                    neu = tgt * S / ot
                    dq = neu - pos[j]
                    if dq != 0.0:
                        px = ot * (1.0 + (1.0 if dq > 0 else -1.0) * slip[j])
                        cash[j] -= dq * px; tv += abs(dq) * px
                    pos[j] = neu; held[j] = tgt
            g = 0.0; e = 0.0; gx = 0.0
            for j in range(N):
                g += cash[j] + pos[j] * c[j, t]
                e += abs(pos[j]) * c[j, t]
                gx += cash[j] + pos[j] * (l[j, t] if pos[j] > 0 else h[j, t])
            k = 1.0 + g - FEE * tv + fu
            kx = 1.0 + gx - FEE * tv + fu
            if k < tief: tief = k
            if kx < tiefx: tiefx = kx
            if k <= 0.0 and i0 < 0: i0 = t
            if kx <= 0.0 and ix0 < 0: ix0 = t
            if k <= 0.5 and i5 < 0: i5 = t
            if k > 0.0 and i0 < 0 and e / k > lev: lev = e / k
        out[si, 0] = tief; out[si, 1] = i0; out[si, 2] = i5; out[si, 3] = k; out[si, 4] = lev; out[si, 5] = tiefx; out[si, 6] = ix0
    return out

mA = R.markt(R.GRUPPE_A, vor=True)
wA = R.auf_raster(mA, M.basis(mA))
kA = R.yubit_kosten(R.GRUPPE_A)[0]
idx = mA.index; T = len(idx)
SPLIT = int(idx.searchsorted(pd.Timestamp(R.SPLIT)))
res = {}

# ---- A) Abgleich mit engine2 (Hebel 1, Start t=1 wie im Modul) ----
w1 = wA.copy(); w1[:, 0] = 0.0
k1, e1, kx1 = kern(mA.o, mA.c, mA.h, mA.l, w1, mA.fund, kA, 0.1, 0, T, False, 0.0)
eq_mod = np.load(AUS + "/v1_eq5m.npy")
abw = np.abs((k1 - 1.0)[:-1] - eq_mod[:-1]).max()
print(f"A) eigener Kern gegen engine2 (Hebel 1, alle Kerzen ausser der Schlussabrechnung): max. Abweichung {abw:.3e}")
res["A_abweichung"] = float(abw)
s = pd.Series(k1 - 1.0, index=idx)
tg = s.groupby(idx.normalize()).last().diff().fillna(s.groupby(idx.normalize()).last().iloc[0])
ent, pru = tg[tg.index < pd.Timestamp(R.SPLIT)], tg[tg.index >= pd.Timestamp(R.SPLIT)]
for name, x in (("Entwicklung", ent), ("Pruefung", pru)):
    kk = 1 + x.cumsum()
    print(f"   {name}: Ertrag/Jahr {x.mean() * 365:.4f} Sharpe {x.mean() / x.std() * np.sqrt(365):.4f} Einbruch rel. Spitze {((kk.cummax() - kk) / kk.cummax()).max():.4f} "
          f"schlechtester Tag {x.min():.4f} ({x.idxmin().date()}) Tage<-10%: {int((x < -0.1).sum())} Tage<-5%: {int((x < -0.05).sum())}")

# ---- B) Einsatz ----
E = pd.Series(e1, index=idx)
print("B) Einsatz in Vielfachen des Startkapitals (Hebel 1, Dauerlauf ab 15.08.2021):")
for name, x in (("Entwicklung", E[:SPLIT]), ("Pruefung", E[SPLIT:]), ("Gesamt", E)):
    print(f"   {name}: Mittel {x.mean():.3f} Median {x.median():.3f} p95 {x.quantile(0.95):.3f} Max {x.max():.3f} ({x.idxmax()}) Anteil > 1,5: {(x > 1.5).mean():.4f} Anteil > 5/3: {(x > 5 / 3).mean():.4f}")
res["B_einsatz_max"] = float(E.max()); res["B_einsatz_mittel"] = float(E.mean()); res["B_einsatz_p95"] = float(E.quantile(0.95))
K1 = pd.Series(k1, index=idx)
tx = E.idxmax()
print(f"   am Maximum: Konto des Dauerlaufs Hebel 1 = {K1[tx]:.3f}; Hebel 3: Einsatz {3 * E[tx]:.2f}, Konto {1 + 3 * (K1[tx] - 1):.2f}, Einsatz/Konto {3 * E[tx] / (1 + 3 * (K1[tx] - 1)):.2f}")
v = pd.Timestamp("2024-12-08 23:55")
print(f"   Vorabend 09.12.2024: Einsatz {E[v]:.3f}, Konto Hebel 1 {K1[v]:.3f}; Hebel 3 Dauerlauf: Konto {1 + 3 * (K1[v] - 1):.3f}, Tagesverlust 09.12. = {3 * ent.min():.3f} Startkapital = {3 * ent.min() / (1 + 3 * (K1[v] - 1)) * 100:.1f} % des Kontos vom Vorabend")

# ---- C) Frischer Start an jedem Tag, Hebel 3 ----
tag0 = np.flatnonzero((idx.hour == 0) & (idx.minute == 0))
for name, a, b in (("Entwicklung (Start bis 31.03.2025, Lauf bis 31.03.2025)", 0, SPLIT), ("Pruefzeitraum (Start ab 01.04.2025, Lauf bis 23.10.2026)", SPLIT, T),
                   ("Entwicklung-Starts, Lauf bis Datenende", 0, T)):
    st = tag0[(tag0 >= a) & (tag0 < (SPLIT if a == 0 else T))]
    for hebel in (3.0, 2.0, 1.0):
        r = frisch(mA.o, mA.c, mA.h, mA.l, wA, mA.fund, kA, hebel / 10, st, b)
        null = r[:, 1] >= 0; halb = r[:, 2] >= 0
        print(f"C) {name}, Hebel {hebel:g}: {len(st)} Starttage | Konto <= 0: {null.mean() * 100:.1f} % | Konto <= 0,5: {halb.mean() * 100:.1f} % | "
              f"am unguenstigsten Kerzenkurs <= 0: {(r[:, 6] >= 0).mean() * 100:.1f} % | Median Konto-Tief {np.median(r[:, 0]):.3f} | schlechtestes Tief {r[:, 0].min():.3f} | Median Ende {np.median(r[:, 3]):.2f}")
        if hebel == 3.0:
            d = pd.DataFrame({"start": idx[st], "konto_tief": r[:, 0], "erstes_null": [str(idx[int(i)]) if i >= 0 else "" for i in r[:, 1]],
                              "erstes_halb": [str(idx[int(i)]) if i >= 0 else "" for i in r[:, 2]], "ende": r[:, 3], "max_einsatz_zu_konto": r[:, 4], "tief_unguenstig": r[:, 5]})
            key = "entw" if (a == 0 and b == SPLIT) else "pruef" if a == SPLIT else "entw_bis_ende"
            d.to_csv(f"{AUS}/v2_frischstart_hebel3_{key}.csv", index=False, float_format="%.5f")
            res[f"C_{key}"] = {"starttage": int(len(st)), "anteil_null": float(null.mean()), "anteil_halb": float(halb.mean()), "anteil_null_unguenstig": float((r[:, 6] >= 0).mean())}
            if null.any():
                dn = d[null]
                tage_bis = (pd.to_datetime(dn.erstes_null) - dn.start).dt.total_seconds() / 86400
                print(f"   Starttage mit Konto <= 0: erster {dn.start.min().date()}, letzter {dn.start.max().date()}; Tage bis zum Ereignis: Median {tage_bis.median():.0f}, min {tage_bis.min():.1f}, max {tage_bis.max():.0f}")
                ev = pd.to_datetime(dn.erstes_null).dt.date.value_counts().sort_index()
                print("   Ereignistage (Datum: Anzahl betroffener Starttage):", {str(k): int(v_) for k, v_ in ev.items()})
    # Naeherung des Pruefers: dieselbe Tagesreihe x 3
    x = (ent if a == 0 and b == SPLIT else pru if a == SPLIT else tg).to_numpy()
    if not (a == 0 and b == T):
        kum = np.concatenate([[0.0], np.cumsum(x)]); suf = np.minimum.accumulate(kum[::-1])[::-1]
        tief = suf[1:] - kum[:-1]
        print(f"   Naeherung des Pruefers (Tagesreihe des Dauerlaufs x 3): Konto <= 0 bei {(3 * tief <= -1).mean() * 100:.1f} %, <= 0,5 bei {(3 * tief <= -0.5).mean() * 100:.1f} % der Starttage")

# ---- D) Zinseszins: Groesse beim Einstieg = Konto x Hebel / 10 ----
print("D) Groesse am laufenden Kontostand (echter Lauf, Einstiegsgroesse = Konto x Hebel / 10, Stueckzahl bis zum Wechsel fest):")
for name, a, b in (("Entwicklung", 0, SPLIT), ("Pruefzeitraum", SPLIT, T)):
    for hebel in (1.0, 3.0):
        ww = wA.copy()
        kz, ez, kxz = kern(mA.o, mA.c, mA.h, mA.l, ww, mA.fund, kA, hebel / 10, a, b, True, 0.0)
        sp = np.maximum.accumulate(kz); jahre = (b - a) / 288 / 365
        neg = bool((kz <= 0).any())
        ende = kz[-1]
        cagr = (ende ** (1 / jahre) - 1) if ende > 0 else float("nan")
        print(f"   {name} Hebel {hebel:g}: Ende {ende:.3f} CAGR {cagr * 100:.1f} % | Einbruch vom Hoechststand {((sp - kz) / sp).max() * 100:.1f} % | Konto-Tief {kz.min():.3f} | Konto <= 0: {neg} | max Einsatz/Konto {np.nanmax(np.where(kz > 0, ez / kz, np.nan)):.2f}")
        res[f"D_{name}_{hebel:g}"] = {"ende": float(ende), "cagr": float(cagr), "dd": float(((sp - kz) / sp).max()), "tief": float(kz.min())}
json.dump(res, open(AUS + "/v2_ergebnis.json", "w"), indent=1)
