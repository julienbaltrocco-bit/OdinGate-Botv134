"""QR (j): (1) gemessene Orderkosten im laufenden Papier-Test 1 (vorwaertstest/lauf/spannen.csv, NUR GELESEN) gegen die
Slippage-Annahme der Rueckrechnung; Takt der Durchlaeufe. (2) Tagesreihe aus (a): feste Groesse (wie berichtet) gegen
Groesse am laufenden Kontostand (Zinseszins, taegliche Anpassung) bei Hebel 1 und 3.
Aufruf aus swing-hybrid/:  .venv/bin/python -I -B -W ignore <dieses Skript> <a_tagesreihe.csv>"""
import sys
import pandas as pd
pd.set_option("display.width", 220)
A = ["BTC", "ETH", "SOL", "XRP", "DOT", "DOGE", "ADA", "LINK", "AVAX", "LTC"]
sp = pd.read_csv("vorwaertstest/lauf/spannen.csv")
st = pd.read_csv("data/processed/yubit_spannen_stichprobe.csv"); st["halb"] = (st.brief - st.geld) / (st.brief + st.geld)
print("Stichprobe der Rueckrechnung:", st.zeit.min(), "bis", st.zeit.max(), "| Messungen je Symbol:", int(st.groupby("symbol").size().median()))
ann = (2 * st.groupby("symbol")["halb"].mean()).clip(lower=0.00005) * 1e4
sp["mittel_bp"] = (pd.to_numeric(sp.kauf_bp, errors="coerce") + pd.to_numeric(sp.verkauf_bp, errors="coerce")) / 2
g = sp.groupby("coin").agg(messungen=("mittel_bp", "count"), gemessen_mittel_bp=("mittel_bp", "mean"), gemessen_p90_bp=("mittel_bp", lambda x: x.quantile(0.9)),
                           gemessen_max_bp=("mittel_bp", "max"), volumen_usd=("volumen", "mean")).reindex(A)
g["annahme_rueckrechnung_bp"] = [ann[c + "USDT"] for c in A]; g["verhaeltnis"] = g.gemessen_mittel_bp / g.annahme_rueckrechnung_bp
print("(1) Papier-Test 1, spannen.csv:", sp.zeit.min(), "bis", sp.zeit.max(), "| Durchlaeufe:", sp.zeit.nunique())
print(g.round(3).to_string())
print("    Mittel ueber Coins: gemessen", round(g.gemessen_mittel_bp.mean(), 3), "bp | Annahme", round(g.annahme_rueckrechnung_bp.mean(), 3), "bp")
z = pd.to_datetime(pd.read_csv("vorwaertstest/lauf/stand.csv").zeit)
erste = z.groupby(z.dt.floor("h")).min()
print("    Erster Durchlauf je voller Stunde (Minute nach der vollen Stunde):", erste.dt.minute.tolist()[1:], "| groesster Abstand zweier Durchlaeufe (min):", float(z.diff().max().total_seconds() / 60))
a = pd.read_csv(sys.argv[1], index_col=0, parse_dates=True)["vor_True"]
def zz(x, h):
    r = h * x; k = (1 + r).cumprod(); n = len(x); f = 1 + r.cumsum()
    return {"hebel": h, "ertrag_jahr_fest": round(float(r.mean() * 365), 4), "cagr_zinseszins": round(float(k.iloc[-1] ** (365 / n) - 1), 4),
            "einbruch_fest_rel_spitze": round(float(((f.cummax() - f) / f.cummax()).max()), 4), "einbruch_zinseszins": round(float(((k.cummax() - k) / k.cummax()).max()), 4),
            "schlechtester_tag": round(float(r.min()), 4), "tag": str(r.idxmin().date())}
print("(2) Feste Groesse am Startkapital gegen Groesse am laufenden Kontostand:")
for name, x in (("Entwicklung", a[:"2025-03-31"]), ("Pruefung", a["2025-04-01":])):
    for h in (1.0, 3.0):
        print("   ", name, zz(x, h))
