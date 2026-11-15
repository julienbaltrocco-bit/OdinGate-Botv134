"""RSK 04: Korrelation und Konzentration. Korrelationsmatrix der zehn Coins, effektive Zahl unabhängiger Wetten,
Anteil der Zeit mit gleicher Richtung, Beta des Portfolios zum Markt. Liest die Zwischenspeicher aus s01."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
import pandas as pd
from rsk_common import A, R, SCRATCH

pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
OUT = {}
N = len(A)


def neff(x: pd.DataFrame) -> dict:
    """Drei übliche Maße für die Zahl unabhängiger Wetten aus den Spalten von x (Renditen oder Tagesergebnisse)."""
    k = x.corr().to_numpy()
    n = k.shape[0]
    rho = (k.sum() - n) / (n * (n - 1))
    ev = np.linalg.eigvalsh(k)
    s = x.std().to_numpy()
    summe = x.sum(axis=1).std()
    return {"mittlere_korrelation": float(rho), "kleinste": float(k[~np.eye(n, dtype=bool)].min()), "groesste": float(k[~np.eye(n, dtype=bool)].max()),
            "neff_formel": float(n / (1 + (n - 1) * rho)), "neff_eigenwerte": float(ev.sum() ** 2 / (ev ** 2).sum()),
            "neff_streuung": float((s.sum() / summe) ** 2), "anteil_erster_faktor": float(ev.max() / ev.sum())}


for name in ("vor", "haupt"):
    d = np.load(SCRATCH / f"lauf_{name}.npz")
    idx = pd.DatetimeIndex(d["index"])
    c = pd.DataFrame(d["c"].T, index=idx, columns=A)
    w = pd.DataFrame(d["w"].T.astype(float), index=idx, columns=A)
    pos = pd.DataFrame(np.sign(d["pos"]).T, index=idx, columns=A)
    tg = pd.read_pickle(SCRATCH / f"tage_{name}.pkl")
    fen = {"Vorperiode": (None, None)} if name == "vor" else {"Entwicklung": (None, R.SPLIT), "Pruefzeitraum": (R.SPLIT, None)}
    for fname, (a, b) in fen.items():
        sl = slice(pd.Timestamp(a) if a else None, (pd.Timestamp(b) - pd.Timedelta(minutes=5)) if b else None)
        cs, ps, ts = c.loc[sl], pos.loc[sl], tg.loc[sl]
        e = OUT[fname] = {}
        print(f"\n=== {fname} ({cs.index[0]} bis {cs.index[-1]}) ===")
        rh = cs.resample("1h").last().pct_change().dropna(how="all")
        rd = cs.resample("1D").last().pct_change().dropna(how="all")
        if fname == "Vorperiode":       # Coins, die noch nicht handeln, stehen im Raster still: erst ab dem Zeitpunkt werten, an dem alle zehn handeln
            start_alle = pd.Timestamp("2020-10-08")
            rh, rd = rh.loc[start_alle:], rd.loc[start_alle:]
            print(f"  (Korrelationen der Vorperiode erst ab {start_alle.date()}, vorher handeln nicht alle zehn Coins)")
        for rn, r in (("Stundenrenditen", rh), ("Tagesrenditen", rd)):
            k = neff(r)
            e[f"coins_{rn}"] = k
            print(f"  Coins, {rn}: mittlere paarweise Korrelation {k['mittlere_korrelation']:.2f} (kleinste {k['kleinste']:.2f}, größte {k['groesste']:.2f}); "
                  f"erster Faktor erklärt {k['anteil_erster_faktor']:.0%} der Streuung; effektive Zahl unabhängiger Wetten: {k['neff_formel']:.2f} (Formel n/(1+(n-1)rho)), "
                  f"{k['neff_eigenwerte']:.2f} (Eigenwerte), {k['neff_streuung']:.2f} (Streuungsverhältnis)")
        print("  Korrelationsmatrix der Tagesrenditen:")
        print(rd.corr().round(2).to_string())
        e["matrix_tagesrenditen"] = rd.corr().round(3).to_dict()
        # Tagesergebnisse der zehn Positionen (mit Vorzeichen der Position): das ist die für das Konto maßgebliche Korrelation
        tsx = ts.loc[rd.index[0]:] if fname == "Vorperiode" else ts
        k = neff(tsx)
        e["positionen_tagesergebnis"] = k
        print(f"  Tagesergebnisse der zehn Positionen (Kandidat): mittlere paarweise Korrelation {k['mittlere_korrelation']:.2f} (kleinste {k['kleinste']:.2f}, größte {k['groesste']:.2f}); "
              f"effektive Zahl unabhängiger Wetten: {k['neff_formel']:.2f} (Formel), {k['neff_eigenwerte']:.2f} (Eigenwerte), {k['neff_streuung']:.2f} (Streuungsverhältnis)")
        print("  Korrelationsmatrix der Tagesergebnisse je Position:")
        print(tsx.corr().round(2).to_string())
        # Richtungen (stündlich, zu Beginn jeder Stunde nach dem Handel)
        ph = ps.iloc[1::12] if False else ps[ps.index.minute == 5]
        if fname == "Vorperiode":
            ph = ph.loc[rd.index[0]:]
        nl, ns = (ph > 0).sum(axis=1), (ph < 0).sum(axis=1)
        voll = (nl + ns) == N
        gleich = np.maximum(nl, ns)
        netto = (nl - ns) / N
        k = {"stunden": int(len(ph)), "anteil_alle_zehn_gleich": float((gleich[voll] == N).mean()), "anteil_mind_neun_gleich": float((gleich[voll] >= 9).mean()),
             "anteil_mind_acht_gleich": float((gleich[voll] >= 8).mean()), "anteil_alle_long": float((nl[voll] == N).mean()), "anteil_alle_short": float((ns[voll] == N).mean()),
             "anteil_5_zu_5": float((gleich[voll] == 5).mean()), "mittlere_netto_richtung_betrag": float(netto.abs().mean()), "mittlere_netto_richtung": float(netto.mean()),
             "verteilung_long_anzahl": {int(i): float(v) for i, v in nl[voll].value_counts(normalize=True).sort_index().items()}}
        # längste Phase am Stück mit allen zehn in derselben Richtung
        g = (gleich == N).to_numpy(); best = lauf = 0
        for x in g:
            lauf = lauf + 1 if x else 0
            best = max(best, lauf)
        k["laengste_phase_alle_gleich_stunden"] = int(best)
        e["richtungen"] = k
        print(f"  Richtungen ({k['stunden']} Stunden): alle zehn gleich in {k['anteil_alle_zehn_gleich']:.1%} (alle Long {k['anteil_alle_long']:.1%}, alle Short {k['anteil_alle_short']:.1%}), "
              f"mindestens neun gleich {k['anteil_mind_neun_gleich']:.1%}, mindestens acht gleich {k['anteil_mind_acht_gleich']:.1%}, genau 5 zu 5 {k['anteil_5_zu_5']:.1%}; "
              f"mittlerer Betrag der Netto-Richtung {k['mittlere_netto_richtung_betrag']:.2f} (1 = alle gleich); längste Phase mit allen zehn gleich {best} Stunden ({best / 24:.0f} Tage)")
        print("    Verteilung Anzahl Long-Positionen: " + ", ".join(f"{i}: {v:.1%}" for i, v in k["verteilung_long_anzahl"].items()))
        # Beta zum Markt (Korb der zehn Coins, gleichgewichtet) und zu BTC, auf Tagesbasis; Hebel 1
        pnl = tsx.sum(axis=1)
        korb = rd.mean(axis=1).reindex(pnl.index)
        btc = rd["BTC"].reindex(pnl.index)
        netto_tag = netto.resample("1D").first().reindex(pnl.index)               # Netto-Richtung am Tagesbeginn
        ok = korb.notna() & netto_tag.notna()
        pnl, korb, btc, netto_tag = pnl[ok], korb[ok], btc[ok], netto_tag[ok]
        beta = lambda y, x: float(np.cov(y, x)[0, 1] / np.var(x, ddof=1))
        faktor = netto_tag * korb
        k = {"tage": int(len(pnl)), "beta_korb": beta(pnl, korb), "korr_korb": float(np.corrcoef(pnl, korb)[0, 1]), "beta_btc": beta(pnl, btc),
             "korr_btc": float(np.corrcoef(pnl, btc)[0, 1]),
             "korr_richtungswette": float(np.corrcoef(pnl, faktor)[0, 1]), "r2_richtungswette": float(np.corrcoef(pnl, faktor)[0, 1] ** 2),
             "beta_richtungswette": beta(pnl, faktor)}
        for rn, sel in (("netto_long_ab_0.8", netto_tag >= 0.8), ("netto_short_ab_0.8", netto_tag <= -0.8), ("gemischt", netto_tag.abs() < 0.8)):
            if sel.sum() > 20:
                k[f"beta_korb_{rn}"] = beta(pnl[sel], korb[sel]); k[f"tage_{rn}"] = int(sel.sum())
                k[f"std_tag_{rn}"] = float(pnl[sel].std()); k[f"korr_korb_{rn}"] = float(np.corrcoef(pnl[sel], korb[sel])[0, 1])
        e["beta"] = k
        print(f"  Beta des Tagesergebnisses (Hebel 1) zum gleichgewichteten Korb: unbedingt {k['beta_korb']:+.2f} (Korrelation {k['korr_korb']:+.2f}); zu BTC {k['beta_btc']:+.2f} (Korrelation {k['korr_btc']:+.2f})")
        for rn, text in (("netto_long_ab_0.8", "Tage mit mindestens 9 von 10 Long"), ("netto_short_ab_0.8", "Tage mit mindestens 9 von 10 Short"), ("gemischt", "gemischte Tage")):
            if f"beta_korb_{rn}" in k:
                print(f"    {text}: {k[f'tage_{rn}']} Tage, Beta zum Korb {k[f'beta_korb_{rn}']:+.2f} (Korrelation {k[f'korr_korb_{rn}']:+.2f}), Streuung des Tagesergebnisses {k[f'std_tag_{rn}']:.2%}")
        print(f"    Anteil der Streuung des Tagesergebnisses, den die reine Richtungswette (Netto-Richtung am Tagesbeginn x Korbrendite) erklärt: {k['r2_richtungswette']:.0%} "
              f"(Korrelation {k['korr_richtungswette']:.2f}, Steigung {k['beta_richtungswette']:.2f})")
(SCRATCH / "s04.json").write_text(json.dumps(OUT, indent=1, default=str))
