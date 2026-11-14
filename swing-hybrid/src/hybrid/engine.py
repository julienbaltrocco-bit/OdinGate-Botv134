"""Rechenkern: ein Konto, mehrere Coins, 5-Minuten-Kerzen. Rechnet Baseline und Hybrid mit denselben Regeln.

Aufbau je Coin
- KERN: Anteil `core_frac` der Positionsgröße folgt dem Swing-Zielgewicht.
    core_market=True  -> wie im Labor: Market-Order zum Open der Folgekerze (Baseline).
    core_market=False -> Limit-Order zum letzten Schlusskurs; nach `ttl` Kerzen ungefüllt: verwerfen, neu einstellen.
- TAKTIK (nur Hybrid, `n_tr` Tranchen): zur vollen Stunde ein Limit `dip` x Stunden-ATR gegen die Swing-Richtung
  (Long: unter dem Kurs). Gefüllt -> Limit-Teilgewinn `tp` x ATR darüber. Mit `trail`: bei TP halbe Tranche raus,
  Rest mit nachgezogenem Stop (Abstand = TP-Abstand, Start auf Einstieg), Stop als Market.
- Swing-Signal endet oder dreht: ALLES per Market schließen, alle Orders streichen.

Füllregel (streng): Eine Limit-Order, die zum Open von Kerze t im Buch liegt, wurde mit Daten bis Kerze t-1
entschieden. Sie gilt nur als gefüllt, wenn Kerze t (oder eine spätere) den Preis um mehr als `eps` DURCHhandelt.
Füllpreis = Limitpreis, nie besser. Teilgewinn-Orders frühestens in der Kerze NACH dem Einstiegs-Fill.

Regeln, die der Kern erzwingt und mitzählt
- nie mehr als eine Einstiegsorder je Coin, Kauf-Limits immer unter Verkaufs-Limits (kein Gegeneinanderlaufen)
- Positionsobergrenze je Coin = S (Kern + Taktik zusammen höchstens |Swing-Gewicht| x S)
- Tagesverlust-Limit: Konto seit Tagesbeginn (UTC) um `day_limit` gefallen -> Taktik per Market schließen,
  Taktik-Orders streichen, bis zum nächsten UTC-Tag keine neuen Taktik-Orders. Der Kern folgt weiter dem Swing.
- Order-zu-Fill und kürzeste Standzeit werden gezählt (Auswertung in metrics.py).

Einheiten: Kapital = 1. S = Nominalwert je Coin bei Gewicht 1 (= Hebel / Anzahl Coins). Feste Positionsgröße ohne
Zinseszins, damit die Kapital-Szenarien exakt linear skalieren.
"""
import numpy as np
from numba import njit


@njit(cache=True)
def _fill(j, dq, px, maker, cash, pos, mv, tv):
    cash[j] -= dq * px
    pos[j] += dq
    if maker:
        mv[j] += abs(dq) * px
    else:
        tv[j] += abs(dq) * px


@njit(cache=True)
def simulate(o, h, l, c, w, atr, fund, day, hour_start, S, core_frac, core_market, n_tr, dip, tp, trail,
             ttl, eps, slip, fee_m, fee_t, day_limit, max_trades):
    N, T = c.shape
    K = max(n_tr, 1)
    D = day[T - 1] + 1

    cash = np.zeros(N); pos = np.zeros(N); mv = np.zeros(N); tv = np.zeros(N); fu = np.zeros(N)
    dirn = np.zeros(N)
    # Kern
    core_q = np.zeros(N); core_held = np.zeros(N)
    co_on = np.zeros(N, np.bool_); co_price = np.zeros(N); co_qty = np.zeros(N); co_dfrac = np.zeros(N)
    co_placed = np.zeros(N, np.int64)
    cyc_on = np.zeros(N, np.bool_); cyc_cf = np.zeros(N); cyc_mv = np.zeros(N); cyc_tv = np.zeros(N)
    cyc_in = np.zeros(N, np.int64); cyc_dir = np.zeros(N)
    # Taktik-Tranchen: 0 frei, 1 Einstiegsorder liegt, 2 offen mit TP-Order, 3 Rest mit Trailing-Stop
    ts = np.zeros((N, K), np.int64); tpx = np.zeros((N, K)); tq = np.zeros((N, K)); ttp = np.zeros((N, K))
    tdist = np.zeros((N, K)); tplaced = np.zeros((N, K), np.int64); tfill = np.zeros((N, K), np.int64)
    text = np.zeros((N, K)); tstop = np.zeros((N, K)); tfrac = np.zeros((N, K))
    tcf = np.zeros((N, K)); tmv = np.zeros((N, K)); ttv = np.zeros((N, K))

    eq_gross = np.zeros(T); MV = np.zeros(T); TV = np.zeros(T); FU = np.zeros(T)
    ORD = np.zeros(T); FIL = np.zeros(T)  # laufende Zahl der Orders und Fills
    daily = np.zeros((N, D, 4))
    trades = np.zeros((max_trades, 8)); nt = 0
    # Zähler: 0 Orders, 1 Fills, 2 Stornos, 3 kürzeste Standzeit (Kerzen), 4 Sperrtage, 5 Regelverstöße beide Seiten,
    #         6 größter Positionsanteil je Coin (Einstiegswerte, in S), 7 Market-Orders
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

        for j in range(N):
            ot = o[j, t]
            w_now = w[j, t]
            w_prev = w[j, t - 1] if t > 0 else 0.0
            d_now = 1.0 if w_now > 0 else (-1.0 if w_now < 0 else 0.0)
            d_cur = dirn[j]

            # ---- 1) Swing endet oder dreht: alles per Market schließen (letzte Kerze: Schlussabrechnung) ----
            ende = t == T - 1
            if d_cur != 0.0 and (d_now != d_cur or ende):
                px = ot * (1.0 - d_cur * slip)
                if co_on[j]:
                    co_on[j] = False; st[2] += 1; st[3] = min(st[3], t - co_placed[j])
                if core_q[j] != 0.0:
                    dq = -core_q[j]
                    _fill(j, dq, px, False, cash, pos, mv, tv)
                    cyc_cf[j] -= dq * px; cyc_tv[j] += abs(dq) * px
                    st[0] += 1; st[1] += 1; st[7] += 1
                    core_q[j] = 0.0
                if cyc_on[j]:
                    if nt < max_trades:
                        trades[nt, 0] = j; trades[nt, 1] = 0; trades[nt, 2] = cyc_dir[j]; trades[nt, 3] = cyc_in[j]
                        trades[nt, 4] = t; trades[nt, 5] = cyc_cf[j]; trades[nt, 6] = cyc_mv[j]; trades[nt, 7] = cyc_tv[j]
                    nt += 1
                    cyc_on[j] = False
                core_held[j] = 0.0
                for k in range(K):
                    if ts[j, k] == 1:
                        st[2] += 1; st[3] = min(st[3], t - tplaced[j, k]); ts[j, k] = 0
                    elif ts[j, k] >= 2:
                        if ts[j, k] == 2:
                            st[2] += 1  # liegende TP-Order streichen
                        dq = -tq[j, k]
                        _fill(j, dq, px, False, cash, pos, mv, tv)
                        tcf[j, k] -= dq * px; ttv[j, k] += abs(dq) * px
                        st[0] += 1; st[1] += 1; st[7] += 1
                        if nt < max_trades:
                            trades[nt, 0] = j; trades[nt, 1] = 1; trades[nt, 2] = d_cur; trades[nt, 3] = tfill[j, k]
                            trades[nt, 4] = t; trades[nt, 5] = tcf[j, k]; trades[nt, 6] = tmv[j, k]; trades[nt, 7] = ttv[j, k]
                        nt += 1
                        ts[j, k] = 0; tq[j, k] = 0.0
                d_cur = 0.0
            if ende:
                dirn[j] = 0.0
                continue
            dirn[j] = d_now

            # ---- 2) Tagesverlust-Limit: Taktik schließen ----
            if do_lock and d_now != 0.0:
                px = ot * (1.0 - d_now * slip)
                for k in range(K):
                    if ts[j, k] == 1:
                        st[2] += 1; st[3] = min(st[3], t - tplaced[j, k]); ts[j, k] = 0
                    elif ts[j, k] >= 2:
                        if ts[j, k] == 2:
                            st[2] += 1
                        dq = -tq[j, k]
                        _fill(j, dq, px, False, cash, pos, mv, tv)
                        tcf[j, k] -= dq * px; ttv[j, k] += abs(dq) * px
                        st[0] += 1; st[1] += 1; st[7] += 1
                        if nt < max_trades:
                            trades[nt, 0] = j; trades[nt, 1] = 1; trades[nt, 2] = d_now; trades[nt, 3] = tfill[j, k]
                            trades[nt, 4] = t; trades[nt, 5] = tcf[j, k]; trades[nt, 6] = tmv[j, k]; trades[nt, 7] = ttv[j, k]
                        nt += 1
                        ts[j, k] = 0; tq[j, k] = 0.0

            if d_now != 0.0 and t > 0:
                cp = c[j, t - 1]
                # ---- 3) Kern: Ziel anpassen ----
                tgt = core_frac * abs(w_now)
                if co_on[j] and (t - co_placed[j] >= ttl or w_now != w_prev):
                    co_on[j] = False; st[2] += 1; st[3] = min(st[3], t - co_placed[j])
                diff = tgt - core_held[j]
                if (not co_on[j]) and abs(diff) > 1e-9:
                    if core_market:
                        if diff > 0:
                            px = ot * (1.0 + d_now * slip)
                            dq = d_now * diff * S / px
                        else:
                            px = ot * (1.0 - d_now * slip)
                            dq = -core_q[j] * (-diff) / core_held[j]
                        _fill(j, dq, px, False, cash, pos, mv, tv)
                        if not cyc_on[j]:
                            cyc_on[j] = True; cyc_cf[j] = 0.0; cyc_mv[j] = 0.0; cyc_tv[j] = 0.0
                            cyc_in[j] = t; cyc_dir[j] = d_now
                        cyc_cf[j] -= dq * px; cyc_tv[j] += abs(dq) * px
                        core_q[j] += dq; core_held[j] = tgt
                        st[0] += 1; st[1] += 1; st[7] += 1
                    else:
                        co_on[j] = True; co_price[j] = cp; co_dfrac[j] = diff; co_placed[j] = t
                        if diff > 0:
                            co_qty[j] = d_now * diff * S / cp
                        else:
                            co_qty[j] = -core_q[j] * (-diff) / core_held[j]
                        st[0] += 1

                # ---- 4) Taktik: abgelaufene Einstiegsorder verwerfen, zur vollen Stunde neue einstellen ----
                if n_tr > 0:
                    aktiv = 0; liegt = False; belegt = 0.0; frei = -1; min_sell = 1e300; max_buy = -1e300
                    for k in range(K):
                        if ts[j, k] == 1 and t - tplaced[j, k] >= ttl:
                            ts[j, k] = 0; st[2] += 1; st[3] = min(st[3], t - tplaced[j, k])
                        if ts[j, k] != 0:
                            aktiv += 1; belegt += tfrac[j, k]
                            if ts[j, k] == 1:
                                liegt = True
                            if ts[j, k] == 2:
                                if d_now > 0:
                                    min_sell = min(min_sell, ttp[j, k])
                                else:
                                    max_buy = max(max_buy, ttp[j, k])
                        elif frei < 0:
                            frei = k
                    budget = (1.0 - core_frac) * abs(w_now)
                    frac = budget / n_tr
                    a = atr[j, t]
                    if (hour_start[t] and not locked and not liegt and aktiv < n_tr and frei >= 0
                            and belegt + frac <= budget + 1e-9 and a == a and a > 0.0):
                        p = cp - d_now * dip * a
                        if p > 0.0:
                            if (d_now > 0 and p >= min_sell) or (d_now < 0 and p <= max_buy):
                                st[5] += 1  # würde gegen eigene TP-Order laufen: nicht einstellen
                            else:
                                k = frei
                                ts[j, k] = 1; tpx[j, k] = p; tq[j, k] = d_now * frac * S / p; tfrac[j, k] = frac
                                tdist[j, k] = tp * a; tplaced[j, k] = t
                                tcf[j, k] = 0.0; tmv[j, k] = 0.0; ttv[j, k] = 0.0
                                st[0] += 1
                    ges = core_held[j] + belegt
                    if ges > st[6]:
                        st[6] = ges

            # ---- 5) Funding (auf die Position zum Open) ----
            r = fund[j, t]
            if r != 0.0 and pos[j] != 0.0:
                fu[j] -= pos[j] * ot * r

            # ---- 6) Fills in dieser Kerze ----
            hi = h[j, t]; lo = l[j, t]
            if co_on[j]:
                p = co_price[j]; q = co_qty[j]
                if (q > 0 and lo < p * (1.0 - eps)) or (q < 0 and hi > p * (1.0 + eps)):
                    _fill(j, q, p, True, cash, pos, mv, tv)
                    if not cyc_on[j]:
                        cyc_on[j] = True; cyc_cf[j] = 0.0; cyc_mv[j] = 0.0; cyc_tv[j] = 0.0
                        cyc_in[j] = t; cyc_dir[j] = dirn[j]
                    cyc_cf[j] -= q * p; cyc_mv[j] += abs(q) * p
                    core_q[j] += q; core_held[j] += co_dfrac[j]
                    co_on[j] = False; st[1] += 1
            if n_tr > 0 and dirn[j] != 0.0:
                d = dirn[j]
                for k in range(K):
                    s = ts[j, k]
                    if s == 1:
                        p = tpx[j, k]; q = tq[j, k]
                        if (q > 0 and lo < p * (1.0 - eps)) or (q < 0 and hi > p * (1.0 + eps)):
                            _fill(j, q, p, True, cash, pos, mv, tv)
                            tcf[j, k] -= q * p; tmv[j, k] += abs(q) * p
                            ts[j, k] = 2; tfill[j, k] = t; ttp[j, k] = p + d * tdist[j, k]
                            st[1] += 1; st[0] += 1  # Fill der Einstiegsorder, TP-Order wird eingestellt
                    elif s == 2 and t > tfill[j, k]:
                        p = ttp[j, k]
                        if (d > 0 and hi > p * (1.0 + eps)) or (d < 0 and lo < p * (1.0 - eps)):
                            teil = 0.5 if trail else 1.0
                            dq = -tq[j, k] * teil
                            _fill(j, dq, p, True, cash, pos, mv, tv)
                            tcf[j, k] -= dq * p; tmv[j, k] += abs(dq) * p
                            tq[j, k] += dq; st[1] += 1
                            if trail:
                                ts[j, k] = 3; text[j, k] = p; tstop[j, k] = tpx[j, k]
                                tplaced[j, k] = t
                            else:
                                if nt < max_trades:
                                    trades[nt, 0] = j; trades[nt, 1] = 1; trades[nt, 2] = d; trades[nt, 3] = tfill[j, k]
                                    trades[nt, 4] = t; trades[nt, 5] = tcf[j, k]; trades[nt, 6] = tmv[j, k]; trades[nt, 7] = ttv[j, k]
                                nt += 1
                                ts[j, k] = 0; tq[j, k] = 0.0
                    elif s == 3 and t > tplaced[j, k]:
                        stop = tstop[j, k]
                        if (d > 0 and lo <= stop) or (d < 0 and hi >= stop):
                            basis = min(stop, ot) if d > 0 else max(stop, ot)  # Kurslücke: schlechterer Preis
                            px = basis * (1.0 - d * slip)
                            dq = -tq[j, k]
                            _fill(j, dq, px, False, cash, pos, mv, tv)
                            tcf[j, k] -= dq * px; ttv[j, k] += abs(dq) * px
                            st[0] += 1; st[1] += 1; st[7] += 1
                            if nt < max_trades:
                                trades[nt, 0] = j; trades[nt, 1] = 1; trades[nt, 2] = d; trades[nt, 3] = tfill[j, k]
                                trades[nt, 4] = t; trades[nt, 5] = tcf[j, k]; trades[nt, 6] = tmv[j, k]; trades[nt, 7] = ttv[j, k]
                            nt += 1
                            ts[j, k] = 0; tq[j, k] = 0.0
                        else:
                            if d > 0:
                                if hi > text[j, k]:
                                    text[j, k] = hi
                                neu = text[j, k] - tdist[j, k]
                                if neu > tstop[j, k]:
                                    tstop[j, k] = neu
                            else:
                                if lo < text[j, k]:
                                    text[j, k] = lo
                                neu = text[j, k] + tdist[j, k]
                                if neu < tstop[j, k]:
                                    tstop[j, k] = neu

        # ---- 7) Kontostand am Kerzenschluss ----
        g = 0.0; m = 0.0; x = 0.0; f = 0.0
        for j in range(N):
            g += cash[j] + pos[j] * c[j, t]
            m += mv[j]; x += tv[j]; f += fu[j]
        eq_gross[t] = g; MV[t] = m; TV[t] = x; FU[t] = f
        ORD[t] = st[0]; FIL[t] = st[1]
        eq_net = g - fee_m * m - fee_t * x + f
        if n_tr > 0 and (not locked) and (not lock_pending) and eq_net - day_start_eq <= -day_limit:
            lock_pending = True
        eq_net_prev = eq_net
        if t == T - 1 or day[t + 1] != day[t]:
            di = day[t]
            for j in range(N):
                daily[j, di, 0] = cash[j] + pos[j] * c[j, t]
                daily[j, di, 1] = mv[j]; daily[j, di, 2] = tv[j]; daily[j, di, 3] = fu[j]

    return eq_gross, MV, TV, FU, daily, trades[: min(nt, max_trades)], st, nt, ORD, FIL
