"""QR (l): White's Reality Check fuer die AUSWAHL des Kandidaten selbst (nur Entwicklungszeitraum).

Im Protokoll wurde die gemeinsame Zufallspruefung nur fuer Abwandlungen GEGEN den Kandidaten gerechnet (Runden 21, 24).
Der Kandidat wurde in den Runden 1-3 aus 32 verschiedenen Signal-Einstellungen gewaehlt (30 aus Runde 1 plus
tsmom_L336 mit/ohne Filter aus Runde 2). Hier: dieselben 32 Einstellungen, sofortige Ausfuehrung (Taker), Hebel 1,
ohne Tageslimit, Tagesergebnis netto mit Rebate, Nullhypothese "keine Einstellung hat einen positiven Ertrag".
Verfahren: mutationen.reality_check (stationaerer Bootstrap, Bloecke im Mittel 20 Tage, 5000 Ziehungen).
Zwei Kostenannahmen: 0,05 % pauschal (Stand der Auswahl in Runde 3) und Yubit-Spannen (Stand heute).

Aufruf aus swing-hybrid/:  NUMBA_CACHE_DIR=<scratch>/numba .venv/bin/python -I -B <dieses Skript> <ausgabe.json>
"""
import json
import sys

sys.path.insert(0, "src")
import numpy as np
import pandas as pd
from hybrid import mutationen as M, research as R, runner

AUS_JSON = sys.argv[1]
KONFIG = ([("tsmom", dict(L=L, bias=b)) for L in (12, 24, 48, 96, 168, 336) for b in (False, True)]
          + [("ensemble", dict(bias=b)) for b in (False, True)]
          + [("reversal", dict(n=n, k=k, bias=b)) for n in (24, 72) for k in (1.5, 2.0, 2.5) for b in (False, True)]
          + [("querschnitt", dict(L=L, modus=mo)) for L in (4, 24, 72) for mo in ("mom", "rev")])


def name(fam, p):
    return fam + "_" + "_".join(f"{k}{v}" for k, v in p.items())


m = R.markt(R.GRUPPE_A)
W = {name(f, p): R.auf_raster(m, R.FAMILIEN[f](m, **p)) for f, p in KONFIG}
out = {"anzahl_einstellungen": len(W)}
for kosten, slip in (("slip_5bp", 0.0005), ("slip_yubit", R.yubit_kosten(R.GRUPPE_A)[0])):
    reihen = {}
    for n, w in W.items():
        l = R.lauf(m, w, taker=True, slip=slip, day_limit=9.0)
        x = l.daily_pnl(runner.MIT).sum(axis=1)
        reihen[n] = x[x.index < pd.Timestamp(R.SPLIT)]
    d = pd.DataFrame(reihen)
    sh = (d.mean() / d.std() * np.sqrt(365)).sort_values(ascending=False)
    mittel, schwelle, p = M.reality_check(d.to_numpy())
    dn = d / d.std()                                              # je Einstellung auf gleiche Schwankung gebracht
    mittel_n, schwelle_n, p_n = M.reality_check(dn.to_numpy())
    out[kosten] = {"sharpe_top5": {k: float(v) for k, v in sh.head(5).items()}, "sharpe_kandidat": float(sh["tsmom_L336_biasFalse"]),
                   "rang_kandidat_nach_sharpe": int(list(sh.index).index("tsmom_L336_biasFalse") + 1),
                   "anzahl_sharpe_positiv": int((sh > 0).sum()),
                   "rc_roh": {"beste": d.columns[int(np.argmax(mittel))], "mittel_beste_jahr": float(mittel.max() * 365),
                              "schwelle_95_jahr": float(schwelle * 365), "p_beste": p},
                   "rc_gleiche_schwankung": {"beste": dn.columns[int(np.argmax(mittel_n))], "sharpe_beste": float(mittel_n.max() * np.sqrt(365)),
                                             "schwelle_95_sharpe": float(schwelle_n * np.sqrt(365)), "p_beste": p_n},
                   "tage": int(len(d))}
    tr = [c for c in d.columns if c.startswith(("tsmom", "ensemble"))]          # nur die 14 Trend-Einstellungen
    mt, st_, pt = M.reality_check(d[tr].to_numpy())
    mtn, stn, ptn = M.reality_check(dn[tr].to_numpy())
    out[kosten]["nur_trend_14"] = {"rc_roh_p": pt, "rc_roh_schwelle_95_jahr": float(st_ * 365), "rc_gleiche_schwankung_p": ptn,
                                   "rc_gleiche_schwankung_schwelle_95_sharpe": float(stn * np.sqrt(365))}
    _, s1, p1 = M.reality_check(d[["tsmom_L336_biasFalse"]].to_numpy())           # ohne Mehrfachvergleich (eine Hypothese)
    out[kosten]["nur_kandidat_1"] = {"p": p1, "schwelle_95_jahr": float(s1 * 365)}
    print(kosten, json.dumps(out[kosten], indent=1))
json.dump(out, open(AUS_JSON, "w"), indent=1, default=float)
