"""V-ENG-02 (Gegenpruefung ENG-02): eigene Nachrechnung, NUR Entwicklungszeitraum (bis 2025-04-01), nur lesend.

Teil A: engine2 direkt aufgerufen (nicht ueber den Skript des Pruefers), Hebel 3 und 1.
Teil B: eigene Stunden-Nachrechnung OHNE engine2 (reines Python/numpy), Abgleich gegen den Kern.
Teil C: frisches Konto je Starttag: Abkuerzung e[t]-e[start] gegen ECHTEN Neustart des Kerns auf dem Ausschnitt.
Teil D: wie viele getrennte Episoden stecken hinter dem Anteil "Konto <= 0"?
Teil E: Empfindlichkeit gegen eine angenommene Erhaltungsmargin (Cross-Margin), nur Annahme, Yubit-Wert unbekannt.
Teil F: Einbruchskennzahl relativ zur Spitze gegen Verlust in Einheiten des Startkapitals (Hebel 1 und 3).
Teil G: Vergleich: Hebel 3 taeglich auf den Kontostand nachgezogen (das tut der Bot NICHT), nur zur Einordnung.
Keine Parameterwahl, keine Dateien geschrieben (Ausgabe nur auf stdout).
Aufruf (liest nur, schreibt nichts; Laufzeit rund 6 Minuten wegen 2.195 echter Neustarts des Kerns):
  cd swing-hybrid && NUMBA_CACHE_DIR=$(mktemp -d) .venv/bin/python -I -B reports/audit/evidence/V-ENG-02/v1_backtest.py
"""
import sys
sys.path.insert(0, "src")
import numpy as np, pandas as pd
from hybrid import research as R, runner, engine2, mutationen as M

voll = R.markt(R.GRUPPE_A, vor=True)
ende = int(voll.index.searchsorted(pd.Timestamp(R.SPLIT)))
idx = voll.index[:ende]
N = len(voll.coins)
A = {k: np.ascontiguousarray(getattr(voll, k)[:, :ende]) for k in ("o", "h", "l", "c", "atr", "fund")}
day = np.ascontiguousarray(voll.day[:ende])
slip = R.yubit_kosten(voll.coins)[0]
w_voll = R.auf_raster(voll, M.basis(voll))
w = np.ascontiguousarray(w_voll[:, :ende])
FEE, REB = runner.TAKER, runner.MIT.rebate
print(f"Entwicklung {idx[0]} bis {idx[-1]}, Bars {ende}, Tage {ende // 288}, Taker {FEE}, Rebate {REB}")
print("Slippage je Coin (bp):", {c: round(float(s) * 1e4, 3) for c, s in zip(voll.coins, slip)})


def kern(a, b, hebel, day_limit=9.0):
    """engine2 direkt, Ausschnitt [a, b). Gibt (equity mit Rebate, equity ohne Rebate, st) zurueck."""
    S = hebel / N
    d = np.ascontiguousarray(day[a:b] - day[a])
    r = engine2.simulate_target(*(np.ascontiguousarray(A[k][:, a:b]) for k in ("o", "h", "l", "c")), np.ascontiguousarray(w[:, a:b]),
                                np.ascontiguousarray(A["atr"][:, a:b]), np.ascontiguousarray(A["fund"][:, a:b]), d, S, R.TTL, runner.EPS,
                                slip, 0.0, 0, 0.0, runner.MAKER, runner.TAKER, day_limit, 4_000_000, True)
    eq, MV, TV, FU = r[0], r[1], r[2], r[3]
    return eq - FEE * (1 - REB) * TV + FU, eq - FEE * TV + FU, r[6]


# ---------------------------------------------------------------- Teil A ----
e3, e3o, st3 = kern(0, ende, 3.0)
e1, e1o, st1 = kern(0, ende, 1.0)
print("\n[A] engine2 direkt")
print(f"  Hebel 1: Ende {e1[-1]:+.4f} = {e1[-1] / (ende / 288) * 365:+.4f}/Jahr; Hebel 3: Ende {e3[-1]:+.4f} = {e3[-1] / (ende / 288) * 365:+.4f}/Jahr")
print(f"  Linearitaet: max |e3 - 3*e1| = {np.abs(e3 - 3 * e1).max():.2e}; Sperrtage {int(st3[4])}, Stops {int(st3[5])}")
print(f"  kleinster Kontostand des durchgehenden Laufs (Start 2021-08-15): Hebel 3 {1 + e3.min():+.3f}, Hebel 1 {1 + e1.min():+.3f}")

# ---------------------------------------------------------------- Teil B ----
# Eigene Stundenrechnung. Signal selbst gebaut aus den Stundenschluessen (Zeilenversatz 336 wie in der Forschung),
# gueltig ab Stundenschluss; Ausfuehrung zum Open der ersten 5-Minuten-Kerze der Folgestunde +/- Slippage.
H = ende // 12
stunden = idx[::12]
W_coin = np.zeros((N, H))                                  # Variante: jeder Coin fuer sich (Luecken werden uebersprungen)
for j, coin in enumerate(voll.coins):
    c = voll.h1[coin]["close"]
    s = np.sign(c / c.shift(336) - 1).fillna(0.0)
    s.index = s.index + pd.Timedelta(hours=1)
    W_coin[j] = s.reindex(stunden.union(s.index)).ffill().reindex(stunden).fillna(0.0).to_numpy()
cc = pd.concat({coin: voll.h1[coin]["close"] for coin in voll.coins}, axis=1)   # Konvention der Forschung: gemeinsamer Stundenindex
sg = np.sign(cc / cc.shift(336) - 1).fillna(0.0); sg.index = sg.index + pd.Timedelta(hours=1)
W = np.ascontiguousarray(sg.reindex(stunden.union(sg.index)).ffill().reindex(stunden).fillna(0.0)[voll.coins].to_numpy().T)
abw = int((W != w[:, ::12]).sum()); innen = int((w.reshape(N, H, 12) != w[:, ::12][:, :, None]).sum())
print(f"\n[B] eigene Stundenrechnung: Signalabweichung zu research.auf_raster {abw} Stunden (Variante je Coin fuer sich: {int((W_coin != w[:, ::12]).sum())}), "
      f"Wechsel innerhalb einer Stunde {innen}")


def eigen(hebel, W=None):
    W = globals()["W"] if W is None else W
    S = hebel / N
    eq_m = np.zeros(H); eq_o = np.zeros(H)
    cash = np.zeros(N); pos = np.zeros(N); held = np.zeros(N); tv = 0.0; fu = 0.0; trades = 0
    for k in range(H):
        t0 = 12 * k
        for j in range(N):
            tgt = W[j, k]
            # Funding in dieser Stunde: Kerze t0 mit Bestand VOR dem Wechsel, spaetere Kerzen mit Bestand danach
            r0 = A["fund"][j, t0]
            if r0 != 0.0 and pos[j] != 0.0:
                fu -= pos[j] * A["o"][j, t0] * r0
            if tgt != held[j]:
                tb = 1 if k == 0 else t0                     # der Kern stellt in Kerze 0 noch keine Order ein
                p = A["o"][j, tb]
                dq = -pos[j] + tgt * S / p
                if dq != 0.0:
                    px = p * (1.0 + (1.0 if dq > 0 else -1.0) * slip[j])
                    cash[j] -= dq * px; pos[j] += dq; tv += abs(dq) * px; trades += 1
                    if abs(pos[j]) < 1e-15:
                        pos[j] = 0.0
                held[j] = tgt
            for t in range(t0 + 1, t0 + 12):
                r = A["fund"][j, t]
                if r != 0.0 and pos[j] != 0.0:
                    fu -= pos[j] * A["o"][j, t] * r
        g = float((cash + pos * A["c"][:, t0 + 11]).sum())
        eq_m[k] = g - FEE * (1 - REB) * tv + fu; eq_o[k] = g - FEE * tv + fu
    return eq_m, eq_o, trades


g3, g3o, ntr = eigen(3.0)
k3 = e3[11::12]
print(f"  Orders (eigene Rechnung) {ntr}; Kontoverlauf Hebel 3 zum Stundenschluss: max |eigen - engine2| = {np.abs(g3[:-1] - k3[:-1]).max():.2e} "
      f"(letzte Stunde ausgenommen: der Kern rechnet dort die Schlussabrechnung)")


def frisch(e, je_tag, Hz, schwelle=0.0):
    """Frisches Konto (Kapital 1) an jedem Starttag i, feste Groesse: Tiefststand binnen Hz Tagen."""
    tag = e[je_tag - 1::je_tag]; n = len(tag); start = np.r_[0.0, tag[:-1]]
    tief = np.array([e[i * je_tag:(i + Hz) * je_tag].min() - start[i] for i in range(n - Hz)])
    return tief


gc3, gc3o, _ = eigen(3.0, W_coin)
print("\n  Anteil Starttage mit Kontostand <= 0 bzw. <= 50 % (Hebel 3, feste Groesse):")
for name, a5, ah, ac in (("mit Rebate", e3, g3, gc3), ("ohne Rebate", e3o, g3o, gc3o)):
    for Hz in (90, 365):
        t5, th, tc = frisch(a5, 288, Hz), frisch(ah, 24, Hz), frisch(ac, 24, Hz)
        print(f"    {name:11s} {Hz:3d} Tage, {len(t5)} Starttage | engine2 5-Minuten: <=0 {np.mean(1 + t5 <= 0) * 100:5.1f} %, <=50 % {np.mean(1 + t5 <= 0.5) * 100:5.1f} %, "
              f"Tief {1 + t5.min():+.2f} | eigene Stundenrechnung: <=0 {np.mean(1 + th <= 0) * 100:5.1f} %, <=50 % {np.mean(1 + th <= 0.5) * 100:5.1f} %, Tief {1 + th.min():+.2f} | "
              f"eigene, Signal je Coin fuer sich: <=0 {np.mean(1 + tc <= 0) * 100:5.1f} %, <=50 % {np.mean(1 + tc <= 0.5) * 100:5.1f} %, Tief {1 + tc.min():+.2f}")

# ---------------------------------------------------------------- Teil C ----
print("\n[C] Abkuerzung gegen echten Neustart des Kerns (Hebel 3, 365 Tage, mit Rebate)")
t5 = frisch(e3, 288, 365)
n_start = len(t5)
wahl = sorted(set(list(range(0, n_start, 40)) + [int(t5.argmin())] + list(np.argsort(t5)[:3])))
diffs = []; ruin_neu = 0; ruin_abk = 0
for i in wahl:
    a = i * 288; b = a + 365 * 288
    em, _, _ = kern(a, b + 1, 3.0)                      # +1 Kerze, damit die Schlussabrechnung ausserhalb des Fensters liegt
    neu = em[:365 * 288].min()
    diffs.append(neu - t5[i]); ruin_neu += 1 + neu <= 0; ruin_abk += 1 + t5[i] <= 0
diffs = np.array(diffs)
print(f"  {len(wahl)} Starttage (jeder 40. plus die 3 schlechtesten): Tiefststand Neustart minus Abkuerzung: min {diffs.min():+.4f}, max {diffs.max():+.4f}; "
      f"Konto <= 0: Neustart {ruin_neu}, Abkuerzung {ruin_abk}")
for Hz in (90, 365):
    tm, to = [], []
    for i in range(ende // 288 - Hz):
        em, eo, _ = kern(i * 288, (i + Hz) * 288 + 1, 3.0)
        tm.append(em[:Hz * 288].min()); to.append(eo[:Hz * 288].min())
    tm, to = np.array(tm), np.array(to)
    print(f"  ALLE {len(tm)} Starttage echt neu gestartet, {Hz} Tage: mit Rebate <=0 {np.mean(1 + tm <= 0) * 100:5.1f} %, <=50 % {np.mean(1 + tm <= 0.5) * 100:5.1f} %, Tief {1 + tm.min():+.2f} | "
          f"ohne Rebate <=0 {np.mean(1 + to <= 0) * 100:5.1f} %, <=50 % {np.mean(1 + to <= 0.5) * 100:5.1f} %, Tief {1 + to.min():+.2f}")
i = int(t5.argmin()); a = i * 288
em, eo, _ = kern(a, a + 365 * 288 + 1, 3.0)
print(f"  schlechtester Starttag {idx[a].date()}: Neustart-Tiefststand {1 + em[:-1].min():+.3f} am {idx[a + int(em[:-1].argmin())]}, "
      f"erstmals <= 0 am {idx[a + int(np.argmax(1 + em <= 0))]}, Ende nach 365 Tagen {1 + em[-2]:+.3f}")

# ---------------------------------------------------------------- Teil D ----
print("\n[D] Episoden hinter dem Anteil (Hebel 3, 365 Tage)")
for name, e in (("mit Rebate", e3), ("ohne Rebate", e3o)):
    tag = e[287::288]; start = np.r_[0.0, tag[:-1]]; n = len(tag) - 365
    erst = []
    for i in range(n):
        x = 1 + e[i * 288:(i + 365) * 288] - start[i]
        if (x <= 0).any():
            erst.append((i, i * 288 + int(np.argmax(x <= 0))))
    if not erst:
        print(f"  {name}: kein Starttag mit Konto <= 0"); continue
    tage_start = np.array([i for i, _ in erst]); t_ruin = np.array([t for _, t in erst])
    bloecke = np.split(tage_start, np.where(np.diff(tage_start) > 1)[0] + 1)
    mon = pd.Series(idx[t_ruin].to_period("M")).value_counts().sort_index()
    print(f"  {name}: {len(erst)} von {n} Starttagen; zusammenhaengende Bloecke von Starttagen: "
          + ", ".join(f"{idx[b[0] * 288].date()}..{idx[b[-1] * 288].date()} ({len(b)})" for b in bloecke))
    print(f"    Monat, in dem das Konto erstmals <= 0 steht: " + ", ".join(f"{m}: {v}" for m, v in mon.items()))
    print(f"    Tage vom Start bis Konto <= 0: Median {np.median((t_ruin - tage_start * 288) / 288):.0f}, min {((t_ruin - tage_start * 288) / 288).min():.0f}")

# ---------------------------------------------------------------- Teil E ----
print("\n[E] Cross-Margin mit ANGENOMMENER Erhaltungsmargin (Anteil am Positionswert 3,0; Yubit-Wert im Repo nicht belegt)")
for mm in (0.0, 0.005, 0.01, 0.02):
    z = []
    for name, e in (("mit", e3), ("ohne", e3o)):
        for Hz in (90, 365):
            t = frisch(e, 288, Hz)
            z.append(f"{name} Rebate {Hz} T: {np.mean(1 + t <= mm * 3.0) * 100:5.1f} %")
    print(f"  Erhaltungsmargin {mm * 100:.1f} %: Liquidation bei Kontostand <= {mm * 3:.3f} | " + " | ".join(z))

# ---------------------------------------------------------------- Teil F ----
print("\n[F] Einbruchskennzahlen")
for hname, em in (("Hebel 1", e1), ("Hebel 3", e3)):
    sp = np.maximum.accumulate(np.maximum(em, 0.0)); absdd = sp - em; k = int(absdd.argmax()); p = int(np.argmax(em[:k + 1]))
    tg = np.diff(np.r_[0.0, em[287::288]]); kt = 1 + np.cumsum(tg); ktm = np.maximum.accumulate(kt)
    print(f"  {hname}: groesster Rueckgang {absdd.max():.3f} Startkapital (Hoch {idx[p]} bei Konto {1 + em[p]:.3f}, Tief {idx[k]} bei {1 + em[k]:.3f}); "
          f"runner.max_drawdown 5-Minuten {runner.max_drawdown(em):.3f}; Tagesbasis relativ zur Spitze (Formel Runde 24) {((ktm - kt) / ktm).max():.4f}, "
          f"Tagesbasis in Startkapital {(np.maximum.accumulate(np.maximum(kt, 1.0)) - kt).max():.4f}")

# ---------------------------------------------------------------- Teil G ----
tg1 = np.diff(np.r_[0.0, e1[287::288]])
for h in (1.0, 3.0):
    kz = np.cumprod(1 + h * tg1); dd = float(((np.maximum.accumulate(kz) - kz) / np.maximum.accumulate(kz)).max())
    print(f"\n[G] Nur zur Einordnung (NICHT das Verhalten des Bots): Hebel {h:.0f} taeglich auf den Kontostand nachgezogen: "
          f"Endstand {kz[-1]:.2f}, groesster Einbruch {dd * 100:.1f} %, kleinster Tagesfaktor {1 + h * tg1.min():.3f}")

# ---------------------------------------------------------------- Teil H ----
print("\n[H] Schlechteste Verluste ueber feste Zeitspannen, Hebel 3, feste Groesse, in Einheiten des Startkapitals (5-Minuten-Basis, mit Rebate)")
for name, n in (("1 Stunde", 12), ("4 Stunden", 48), ("24 Stunden", 288), ("3 Tage", 864), ("7 Tage", 2016), ("30 Tage", 8640)):
    d = e3[n:] - e3[:-n]; k = int(d.argmin())
    print(f"  {name:10s}: {d.min():+.3f} (von {idx[k]} bis {idx[k + n]}); Anzahl Spannen mit Verlust >= 0,5: {int((d <= -0.5).sum())}")
tg3 = pd.Series(np.diff(np.r_[0.0, e3[287::288]]), index=voll.days[:ende // 288])
print("  schlechteste Kalendertage (UTC):", ", ".join(f"{d.date()} {v:+.3f}" for d, v in tg3.nsmallest(5).items()))
print(f"  Kalendertage mit Verlust >= 30 % des Startkapitals: {int((tg3 <= -0.30).sum())} von {len(tg3)}; >= 15 %: {int((tg3 <= -0.15).sum())}")

# ---------------------------------------------------------------- Teil I ----
print("\n[I] Groesste Gegenbewegung je Trade (isolierte Margin haengt vom an der Boerse EINGESTELLTEN Hebel ab, den der Bot nie liest oder setzt)")
S = 3.0 / N
r = engine2.simulate_target(A["o"], A["h"], A["l"], A["c"], w, A["atr"], A["fund"], day, S, R.TTL, runner.EPS, slip, 0.0, 0, 0.0,
                            runner.MAKER, runner.TAKER, 9.0, 4_000_000, True)
tr = r[5]
mae = np.empty(len(tr))
for q, (j, art, d, a, b) in enumerate(tr[:, :5]):
    j, a, b = int(j), int(a), int(b); p = A["o"][j, a]
    mae[q] = (1 - A["l"][j, a:b + 1].min() / p) if d > 0 else (A["h"][j, a:b + 1].max() / p - 1)
print(f"  Trades {len(tr)}; Median {np.median(mae) * 100:.2f} %, 99 % {np.quantile(mae, 0.99) * 100:.1f} %, max {mae.max() * 100:.1f} %")
for hb, grenze in ((3, 1 / 3), (5, 0.20), (10, 0.10), (20, 0.05)):
    print(f"  Boersen-Hebel {hb:2d} isoliert (Gegenbewegung >= {grenze * 100:.0f} %, ohne Erhaltungsmargin): {int((mae >= grenze).sum())} Trades = {np.mean(mae >= grenze) * 100:.2f} %")
