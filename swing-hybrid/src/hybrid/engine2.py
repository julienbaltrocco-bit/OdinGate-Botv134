"""Rechenkern 2: Zielposition per Limit-Order nachführen (für schnellere Strategien mit viel Umsatz).

Je Coin gibt die Strategie ein Zielgewicht w (−1 … +1, Anteil an S) vor, das ab dem Open einer Kerze gilt und nur
aus Daten bis zur Vorkerze stammt. Der Kern führt die Position nach:

- JEDE Änderung (Einstieg, Aufstocken, Reduzieren, Schließen, Drehen) per Limit zum letzten Schlusskurs.
  Nach `ttl` Kerzen ungefüllt: streichen und zum neuen Kurs neu einstellen. Immer nur EINE Order je Coin.
- Market-Orders nur für: Stop (Kurs läuft `stop_atr` x ATR gegen den Einstieg), Tagesverlust-Limit, Schlussabrechnung.
  Nach einem Stop bleibt die Richtung gesperrt, bis das Zielgewicht sie verlässt.
- Füllregel wie im ersten Kern: Limit zählt nur, wenn eine Kerze den Preis um mehr als `eps` durchhandelt.

Stress-Schalter (für die Gegenprüfung, nicht zum Optimieren):
- `adverse`: jeder Limit-Fill wird um diesen Anteil schlechter abgerechnet (Spread / Warteschlange).
- `delay`:   die Order kann erst `delay` Kerzen nach dem Einstellen gefüllt werden.

`taker=True`: statt passiver Limits eine Limit-Order mit Preisgrenze DURCH den Markt (sofort gefüllt, zählt als Taker).
Abgerechnet zum Open der Kerze plus `slip` Slippage. Keine Annahme über Warteschlangen nötig.
"""
import numpy as np
from numba import njit


@njit(cache=True)
def simulate_target(o, h, l, c, w, atr, fund, day, S, ttl, eps, slip, adverse, delay, stop_atr,
                    fee_m, fee_t, day_limit, max_trades, taker):
    N, T = c.shape
    D = day[T - 1] + 1
    cash = np.zeros(N); pos = np.zeros(N); mv = np.zeros(N); tv = np.zeros(N); fu = np.zeros(N)
    held = np.zeros(N)
    od_on = np.zeros(N, np.bool_); od_p = np.zeros(N); od_q = np.zeros(N); od_tgt = np.zeros(N)
    od_t = np.zeros(N, np.int64)
    ent_px = np.zeros(N); ent_atr = np.zeros(N); blocked = np.zeros(N)
    cyc_cf = np.zeros(N); cyc_mv = np.zeros(N); cyc_tv = np.zeros(N); cyc_in = np.zeros(N, np.int64)

    eq_gross = np.zeros(T); MV = np.zeros(T); TV = np.zeros(T); FU = np.zeros(T)
    ORD = np.zeros(T); FIL = np.zeros(T)
    daily = np.zeros((N, D, 4))
    trades = np.zeros((max_trades, 8)); nt = 0
    # 0 Orders, 1 Fills, 2 Stornos, 3 kürzeste Standzeit, 4 Sperrtage, 5 Stops, 6 größter |Zielanteil|, 7 Market-Orders
    st = np.zeros(8); st[3] = 1e9
    lock_pending = False; locked_day = -1
    day_start_eq = 0.0; eq_net_prev = 0.0

    for t in range(T):
        if t > 0 and day[t] != day[t - 1]:
            day_start_eq = eq_net_prev
        do_lock = lock_pending
        if do_lock:
            lock_pending = False; locked_day = day[t]; st[4] += 1
        locked = locked_day == day[t]
        ende = t == T - 1

        for j in range(N):
            ot = o[j, t]; hi = h[j, t]; lo = l[j, t]
            tgt = w[j, t]
            if blocked[j] != 0.0:
                if tgt * blocked[j] <= 0.0:
                    blocked[j] = 0.0
                else:
                    tgt = 0.0
            if locked or ende:
                tgt = 0.0

            # ---- Market: Tagesverlust-Limit oder Schlussabrechnung ----
            if (do_lock or ende) and pos[j] != 0.0:
                d = 1.0 if pos[j] > 0 else -1.0
                px = ot * (1.0 - d * slip)
                dq = -pos[j]
                cash[j] -= dq * px; pos[j] = 0.0; tv[j] += abs(dq) * px
                cyc_cf[j] -= dq * px; cyc_tv[j] += abs(dq) * px
                if nt < max_trades:
                    trades[nt, 0] = j; trades[nt, 1] = 2; trades[nt, 2] = d; trades[nt, 3] = cyc_in[j]
                    trades[nt, 4] = t; trades[nt, 5] = cyc_cf[j]; trades[nt, 6] = cyc_mv[j]; trades[nt, 7] = cyc_tv[j]
                nt += 1
                held[j] = 0.0
                st[0] += 1; st[1] += 1; st[7] += 1
                if od_on[j]:
                    od_on[j] = False; st[2] += 1; st[3] = min(st[3], t - od_t[j])

            # ---- Order pflegen: abgelaufen oder Ziel geändert -> streichen; Abweichung -> neu einstellen ----
            if od_on[j] and (t - od_t[j] >= ttl or od_tgt[j] != tgt):
                od_on[j] = False; st[2] += 1; st[3] = min(st[3], t - od_t[j])
            if (not od_on[j]) and t > 0 and (not ende) and abs(tgt - held[j]) > 1e-9:
                p = ot if taker else c[j, t - 1]
                hj = held[j]
                if hj == 0.0 or abs(tgt) > abs(hj) and tgt * hj > 0.0:
                    dq = (tgt - hj) * S / p                  # eröffnen oder aufstocken
                elif tgt * hj < 0.0:
                    dq = -pos[j] + tgt * S / p               # drehen: schließen und Gegenseite in einer Order
                else:
                    dq = -pos[j] * (1.0 - tgt / hj)          # reduzieren oder schließen
                if dq != 0.0:
                    od_on[j] = True; od_p[j] = p; od_q[j] = dq; od_tgt[j] = tgt; od_t[j] = t
                    st[0] += 1
                    if abs(tgt) > st[6]:
                        st[6] = abs(tgt)

            # ---- Funding ----
            r = fund[j, t]
            if r != 0.0 and pos[j] != 0.0:
                fu[j] -= pos[j] * ot * r

            # ---- Stop (Market) ----
            if stop_atr > 0.0 and pos[j] != 0.0:
                d = 1.0 if pos[j] > 0 else -1.0
                stop = ent_px[j] - d * stop_atr * ent_atr[j]
                if (d > 0 and lo <= stop) or (d < 0 and hi >= stop):
                    basis = min(stop, ot) if d > 0 else max(stop, ot)
                    px = basis * (1.0 - d * slip)
                    dq = -pos[j]
                    cash[j] -= dq * px; pos[j] = 0.0; tv[j] += abs(dq) * px
                    cyc_cf[j] -= dq * px; cyc_tv[j] += abs(dq) * px
                    if nt < max_trades:
                        trades[nt, 0] = j; trades[nt, 1] = 3; trades[nt, 2] = d; trades[nt, 3] = cyc_in[j]
                        trades[nt, 4] = t; trades[nt, 5] = cyc_cf[j]; trades[nt, 6] = cyc_mv[j]; trades[nt, 7] = cyc_tv[j]
                    nt += 1
                    held[j] = 0.0; blocked[j] = d
                    st[0] += 1; st[1] += 1; st[5] += 1; st[7] += 1
                    if od_on[j]:
                        od_on[j] = False; st[2] += 1; st[3] = min(st[3], t - od_t[j])

            # ---- Limit-Fill ----
            if od_on[j] and (taker or t >= od_t[j] + delay):
                p = od_p[j]; q = od_q[j]
                if taker or (q > 0 and lo < p * (1.0 - eps)) or (q < 0 and hi > p * (1.0 + eps)):
                    sq = 1.0 if q > 0 else -1.0
                    px = p * (1.0 + sq * (slip if taker else adverse))
                    alt = pos[j]
                    neu = alt + q
                    if abs(neu) < 1e-15:
                        neu = 0.0
                    cash[j] -= q * px; pos[j] = neu
                    if taker:
                        tv[j] += abs(q) * px; st[7] += 1
                    else:
                        mv[j] += abs(q) * px
                    st[1] += 1
                    vm = 0.0 if taker else 1.0                   # Volumen zählt als Maker (1) oder Taker (0)
                    if alt == 0.0:                               # neuer Trade
                        cyc_cf[j] = -q * px; cyc_mv[j] = vm * abs(q) * px; cyc_tv[j] = (1.0 - vm) * abs(q) * px; cyc_in[j] = t
                        ent_px[j] = px; ent_atr[j] = atr[j, t]
                    elif neu == 0.0 or alt * neu < 0.0:          # geschlossen oder gedreht
                        zu = -alt
                        cyc_cf[j] -= zu * px; cyc_mv[j] += vm * abs(zu) * px; cyc_tv[j] += (1.0 - vm) * abs(zu) * px
                        if nt < max_trades:
                            trades[nt, 0] = j; trades[nt, 1] = 0; trades[nt, 2] = 1.0 if alt > 0 else -1.0
                            trades[nt, 3] = cyc_in[j]; trades[nt, 4] = t; trades[nt, 5] = cyc_cf[j]
                            trades[nt, 6] = cyc_mv[j]; trades[nt, 7] = cyc_tv[j]
                        nt += 1
                        if neu != 0.0:
                            cyc_cf[j] = -neu * px; cyc_mv[j] = vm * abs(neu) * px; cyc_tv[j] = (1.0 - vm) * abs(neu) * px; cyc_in[j] = t
                            ent_px[j] = px; ent_atr[j] = atr[j, t]
                    else:
                        cyc_cf[j] -= q * px; cyc_mv[j] += vm * abs(q) * px; cyc_tv[j] += (1.0 - vm) * abs(q) * px
                        if abs(neu) > abs(alt):                  # aufgestockt: Einstiegspreis mitteln
                            ent_px[j] = (ent_px[j] * abs(alt) + px * abs(q)) / abs(neu)
                    held[j] = od_tgt[j]
                    od_on[j] = False

        g = 0.0; m = 0.0; x = 0.0; f = 0.0
        for j in range(N):
            g += cash[j] + pos[j] * c[j, t]
            m += mv[j]; x += tv[j]; f += fu[j]
        eq_gross[t] = g; MV[t] = m; TV[t] = x; FU[t] = f
        ORD[t] = st[0]; FIL[t] = st[1]
        eq_net = g - fee_m * m - fee_t * x + f
        if (not locked) and (not lock_pending) and eq_net - day_start_eq <= -day_limit:
            lock_pending = True
        eq_net_prev = eq_net
        if ende or day[t + 1] != day[t]:
            di = day[t]
            for j in range(N):
                daily[j, di, 0] = cash[j] + pos[j] * c[j, t]
                daily[j, di, 1] = mv[j]; daily[j, di, 2] = tv[j]; daily[j, di, 3] = fu[j]

    return eq_gross, MV, TV, FU, daily, trades[: min(nt, max_trades)], st, nt, ORD, FIL
