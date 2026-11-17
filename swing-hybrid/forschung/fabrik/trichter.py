"""Trichter der Fabrik ab Stufe 3 und die Prüfgrößen gegen Zufallstreffer (Regeln: protokoll.md Abschnitt 19).

  .venv/bin/python -I forschung/fabrik/trichter.py statistik        Anteil über Zufall, Reality Check, PBO (liest nur T und V1)
  .venv/bin/python -I forschung/fabrik/trichter.py stufe3           Robustheit und Gruppenbildung -> Finalisten (eingefroren)
  .venv/bin/python -I forschung/fabrik/trichter.py stufe4           Schlussprüfung V2 für die eingefrorenen Finalisten (einmal)
"""
import json
import math
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np

F = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(F))
from fabrik import daten as D, generator as G, kern as FK, lauf as L, signale as S

ERG = F / "fabrik/ergebnisse"
I_V2, I_V2ENDE = L.idx("2024-07-01"), D.N                       # Schlussprüfung V2: 01.07.2024 bis 31.03.2025
phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))


def phi_inv(p):                                                  # Näherung nach Acklam, genügt für die Prüfgrößen
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02, 1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02, 6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00, -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    if p < 0.02425:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > 1 - 0.02425:
        return -phi_inv(1 - p)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def db():
    con = sqlite3.connect(L.DB, timeout=60)
    con.row_factory = sqlite3.Row
    return con


def aufgabe_aus(z) -> dict:
    """Aus einer Datenbankzeile wieder die Einstiegsregel und den einen Ausstieg bauen."""
    si = S.NAMEN.index(z["signal"])
    a = {"si": si, "signal": z["signal"], "familie": z["familie"], "braucht": z["braucht"], "th": z["th"], "r": z["r"], "f": z["f"], "k": z["k"]}
    if z["best"]:
        b = json.loads(z["best"])
        a["best"] = {"si": S.NAMEN.index(b[0]), "signal": b[0], "th": b[1], "r": b[2], "braucht": S.SIGNALE[S.NAMEN.index(b[0])][3]}
    return a


def ausstieg_aus(z):
    alle = json.loads((ERG / "ausstiege.json").read_text()) if (ERG / "ausstiege.json").exists() else {}
    x = G.AUSSTIEGE.get(z["x"]) or alle[z["x"]]
    return tuple(x)


def markt_von(z, a=None):
    a = a or aufgabe_aus(z)
    return [c for c in G.MAERKTE[z["m"]] if not (c == 0 and L.ohne_btc(a))]


def tagesreihe(z, i0, i1, verzug=0, modell="basis", faktor=1.0):
    """Rechnet einen Kandidaten über die Kerzen [i0, i1) neu: Tagesergebnis netto mit Rebate (bp des Kapitals), Trades, roh je Trade.
    modell "basis": gemessene Yubit-Slippage (mal faktor). modell "bewegt": zusätzlich mindestens 5 % (mal faktor) der Spanne der letzten Kerze je Order."""
    a = aufgabe_aus(z)
    halte, sl, tp, tr, ta, sx = ausstieg_aus(z)
    M = markt_von(z, a)
    n_tage = (i1 - i0) // 288
    tag = np.clip((np.arange(D.N) - i0) // 288, 0, n_tage - 1).astype(np.int32)
    arr = [np.zeros((len(D.COINS), n_tage)) for _ in range(6)]
    altes_ende, L.I_ENDE = L.I_ENDE, i1                           # einstieg() schneidet die Reihen am Ende des geprüften Zeitraums ab
    try:
        for j in M:
            ein, wert = L.einstieg(a, j)
            slip = (L.slip_bewegt(j, 1.0) if modell == "bewegt" else L._g["slip_basis"][j]) * faktor
            FK.sim(L._g["o"][j], L._g["h"][j], L._g["l"][j], L._g["fcum"][j], ein, wert, L._g["sigma"][j], tag, i0, i1, halte, sl, tp, tr, ta,
                   np.nan if sx is None else sx, slip, L.KOSTEN85, *(x[j] for x in arr), verzug)
    finally:
        L.I_ENDE = altes_ende
    n = arr[1][M].sum()
    p85 = (arr[0][M].sum(0) - arr[1][M].sum(0) * L.KOSTEN85) / len(M)
    return p85, int(n), (arr[0][M].sum() / n if n else 0.0)


def marktbereinigt(z, i0, i1):
    """Alpha (bp je Tag), t-Wert des Alpha und Beta gegen die gleichgewichtete Tagesrendite der gehandelten Coins."""
    p, _, _ = tagesreihe(z, i0, i1)
    M = markt_von(z)
    schluss = i0 - 1 + 288 * np.arange(len(p) + 1)                 # letzte Kerze vor Beginn, danach jedes Tagesende
    c = np.stack([np.asarray(D.laden("c")[j])[schluss] for j in M])
    m = (c[:, 1:] / c[:, :-1] - 1).mean(0) * 1e4
    p, X = p[:-1], np.column_stack([np.ones(len(p) - 1), m[:-1], m[1:]])     # Trades laufen bis 12 Stunden: auch die Marktrendite des Folgetags erklärt mit
    koef, *_ = np.linalg.lstsq(X, p, rcond=None)
    rest = p - X @ koef
    se = math.sqrt(rest.var(ddof=3) * np.linalg.inv(X.T @ X)[0, 0])
    return float(koef[0]), float(koef[0] / se) if se > 0 else 0.0, float(koef[1])


def t_wert(p):
    s = p.std(ddof=1)
    return float(p.mean() / s * math.sqrt(len(p))) if s > 0 else 0.0


# ---------------------------------------------------------------- Prüfgrößen über alle Versuche
def statistik():
    con = db()
    try:
        n_gen1 = con.execute("SELECT COUNT(*) FROM kandidaten WHERE gen = 'gen1'").fetchone()[0]
    except sqlite3.OperationalError:
        n_gen1 = 0
    if n_gen1 == 0 or not (L.AUS / "tage_gen1.npy").exists():      # frische Sitzung: die Zufallsprüfung wertet nur Generation 1 aus und liegt im Repository
        print("Statistik unverändert: Generation 1 liegt in dieser Sitzung nicht vor; statistik.json im Repository gilt weiter.")
        return
    aus = {"stand": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "gruppen": {}}
    for gruppe, wo in (("Kurs, Volumen, Derivate (T 08/2021–06/2023)", "braucht != 't' AND (best IS NULL OR best NOT LIKE '%tiefe%' AND best NOT LIKE '%liq_entzug%')"),
                       ("Orderbuch-Tiefe (T 2023)", "(braucht = 't' OR best LIKE '%tiefe%' OR best LIKE '%liq_entzug%')")):
        alle = con.execute(f"SELECT gen, zeile, t_roh_t, t85_t, status, sharpe_t FROM kandidaten WHERE n_t >= 200 AND {wo}").fetchall()
        z = [r for r in alle if r["gen"] == "gen1"]               # Zufallsvergleiche nur auf der unausgewählten Grundmenge
        if not z:
            continue
        spaeter = [r for r in alle if r["gen"] != "gen1"]
        n = len(z)
        s1 = sum(1 for r in z if r["status"] not in ("verworfen_1",))
        s2 = sum(1 for r in z if r["status"] in ("stufe2", "stufe3", "final", "validiert", "verworfen_3", "verworfen_4"))
        seg = L.SEGMENTE["t" if "Tiefe" in gruppe else "k"]
        d0, d1 = seg[0], seg[1]
        # Tagesmatrix T (netto mit Rebate) in Blöcken; Reality Check mit stationärem Bootstrap, studentisiert
        rng = np.random.default_rng(19)
        B, tage, block = 400, d1 - d0, 10
        W = np.zeros((B, tage), np.float32)
        for b in range(B):
            pos, idxs = 0, np.empty(tage, np.int64)
            neu = rng.random(tage) < 1.0 / block
            starts = rng.integers(0, tage, tage)
            for i in range(tage):
                pos = starts[i] if (neu[i] or i == 0) else (pos + 1) % tage
                idxs[i] = pos
            W[b] = np.bincount(idxs, minlength=tage) / tage
        maxima = np.full(B, -np.inf, np.float32)
        beste, t_best, sr_alle, reihe_best = None, -np.inf, [], None
        nach_gen = {}
        for r in z:
            nach_gen.setdefault(r["gen"], []).append(r["zeile"])
        # PBO: zehn Zeitblöcke über T und V1
        e0, e1, K = seg[0], seg[2], 10
        grenzen = np.linspace(e0, e1, K + 1).astype(int)
        S1, S2, NB = [], [], np.diff(grenzen)
        for gen, zeilen in nach_gen.items():
            tage_mm = np.load(L.AUS / f"tage_{gen}.npy", mmap_mode="r")
            zeilen = np.sort(np.array(zeilen))
            for c0 in range(0, len(zeilen), 20000):
                m = np.asarray(tage_mm[zeilen[c0:c0 + 20000]])
                t = m[:, d0:d1]
                mittel, sd = t.mean(1), t.std(1, ddof=1)
                ok = sd > 0
                tw = np.where(ok, mittel / np.where(ok, sd, 1) * np.sqrt(tage), 0)
                if tw.max() > t_best:
                    t_best, beste = float(tw.max()), (gen, int(zeilen[c0 + int(tw.argmax())]))
                t64 = t.astype(np.float64)
                mb = t64 @ W.T.astype(np.float64)                                                # Mittel je Bootstrap-Stichprobe
                vb = np.maximum((t64 * t64) @ W.T.astype(np.float64) - mb ** 2, 0) * tage / (tage - 1)  # Streuung DERSELBEN Stichprobe (Befund C1)
                gut = ok[:, None] & (vb > 0)
                boot = np.where(gut, (mb - mittel[:, None]) / np.sqrt(np.where(gut, vb, 1)) * np.sqrt(tage), -np.inf)   # zentriert: Verteilung ohne echten Vorteil
                maxima = np.maximum(maxima, boot.max(0))
                sr_alle.append(np.where(ok, mittel / np.where(ok, sd, 1), 0.0))
                if tw.max() >= t_best:
                    reihe_best = t64[int(tw.argmax())].copy()
                S1.append(np.stack([m[:, grenzen[i]:grenzen[i + 1]].sum(1) for i in range(K)], 1))
                S2.append(np.stack([(m[:, grenzen[i]:grenzen[i + 1]] ** 2).sum(1) for i in range(K)], 1))
        S1, S2 = np.concatenate(S1).astype(np.float64), np.concatenate(S2).astype(np.float64)
        import itertools
        logits, oos_neg = [], 0
        for kombi in itertools.combinations(range(K), K // 2):
            a = np.zeros(K, bool); a[list(kombi)] = True
            def sharpe(maske):
                nn = NB[maske].sum()
                mu = S1[:, maske].sum(1) / nn
                var = S2[:, maske].sum(1) / nn - mu ** 2
                return np.where(var > 0, mu / np.sqrt(np.where(var > 0, var, 1)), -np.inf)
            sis, soos = sharpe(a), sharpe(~a)
            k_best = int(sis.argmax())
            oos_neg += soos[k_best] <= 0
            rang = (soos < soos[k_best]).mean()                    # Rang des im einen Teil besten Kandidaten im anderen Teil
            rang = min(max(rang, 1 / (len(soos) + 1)), 1 - 1 / (len(soos) + 1))
            logits.append(math.log(rang / (1 - rang)))
        sr_alle = np.concatenate(sr_alle)
        srb = reihe_best.mean() / reihe_best.std(ddof=1)
        x = (reihe_best - reihe_best.mean()) / reihe_best.std()
        schiefe, woelbung, EM = float((x ** 3).mean()), float((x ** 4).mean()), 0.5772156649
        sr0 = math.sqrt(float(sr_alle.var())) * ((1 - EM) * phi_inv(1 - 1 / n) + EM * phi_inv(1 - 1 / (n * math.e)))     # erwartetes Maximum ohne Vorteil
        dsr = phi((srb - sr0) * math.sqrt(tage - 1) / math.sqrt(max(1e-12, 1 - schiefe * srb + (woelbung - 1) / 4 * srb ** 2)))
        s1x = sum(1 for r in spaeter if r["status"] not in ("verworfen_1",))
        aus["gruppen"][gruppe] = {"grundmenge": "Generation 1 (ohne Auswahl erzeugt)", "gueltige_kandidaten": n, "stufe1_bestanden": s1, "anteil_stufe1": round(s1 / n, 4),
                                 "zufallserwartung_stufe1": "0,5 % (Streuung 0,4), wenn die Regeln nichts wissen und die Slippage verlieren; 2,8 % (Streuung 1,5) bei Erwartungswert null (Bootstrap der Gegenprüfung)",
                                 "stufe2_bestanden": s2, "anteil_stufe2": round(s2 / n, 5),
                                 "spaetere_generationen": {"gueltig": len(spaeter), "anteil_stufe1": round(s1x / len(spaeter), 4) if spaeter else None,
                                                           "hinweis": "aus Gewinnern des Trainings abgeleitet, daher kein Zufallsvergleich"},
                                 "deflated_sharpe_ratio": round(dsr, 3), "deflated_sharpe_hinweis": "gesichert gälte ein Wert über 0,95",
                                 "bester_t_wert_T": round(t_best, 2), "reality_check_p": round(float((maxima >= t_best).mean()), 4),
                                 "zufalls_maximum_median": round(float(np.median(maxima)), 2), "zufalls_maximum_95": round(float(np.percentile(maxima, 95)), 2),
                                 "pbo": round(float(np.mean(np.array(logits) <= 0)), 3), "pbo_kombinationen": len(logits),
                                 "bester_verliert_im_anderen_teil": round(oos_neg / len(logits), 3)}
        print(gruppe, json.dumps(aus["gruppen"][gruppe], ensure_ascii=False), flush=True)
    ERG.mkdir(parents=True, exist_ok=True)
    (ERG / "statistik.json").write_text(json.dumps(aus, ensure_ascii=False, indent=1))
    return aus


# ---------------------------------------------------------------- Stufe 3: Robustheit, Nachbarn, Gruppen
BASIS = lambda s: s.rsplit("_", 1)[0] if s.rsplit("_", 1)[-1].replace(".", "").isdigit() else s


def nachbarn_ok(con, z) -> tuple:
    """Nachbarn: gleiches Signal mit benachbarter Schwelle, oder benachbarte Länge derselben Signalart; sonst alles gleich."""
    basis = BASIS(z["signal"])
    verwandt = sorted((s[2], s[0]) for s in S.SIGNALE if BASIS(s[0]) == basis and s[0] != basis or s[0] == z["signal"])
    namen = [s for _, s in verwandt]
    i = namen.index(z["signal"]) if z["signal"] in namen else -1
    nachb_sig = [namen[k] for k in (i - 1, i + 1) if i >= 0 and 0 <= k < len(namen)]
    wo = "f = ? AND k = ? AND x = ? AND m = ? AND r = ? AND n_t >= 200 AND best IS NULL"
    arg = (z["f"], z["k"], z["x"], z["m"], z["r"])
    # mit Bestätigungssignal: Nachbarn sind die Eltern-Regel ohne Bestätigung (gleiche Schwelle) und deren Nachbarn
    zeilen = con.execute(f"SELECT n85_t FROM kandidaten WHERE signal = ? AND {'1=1' if z['best'] else 'th != ?'} AND ABS(th - ?) <= 1.01 AND {wo}",
                         ((z["signal"], z["th"], *arg) if z["best"] else (z["signal"], z["th"], z["th"], *arg))).fetchall()
    for s in nachb_sig:
        zeilen += con.execute(f"SELECT n85_t FROM kandidaten WHERE signal = ? AND th = ? AND {wo}", (s, z["th"], *arg)).fetchall()
    werte = [r[0] for r in zeilen]
    return (len(werte) > 0 and sum(1 for w in werte if w > 0) >= len(werte) / 2), len(werte), sum(1 for w in werte if w > 0)


def stufe3():
    L._init()
    con = db()
    con.execute("CREATE INDEX IF NOT EXISTS nachbar ON kandidaten (signal, f, k, x, m, r, th)")
    kand = con.execute("SELECT * FROM kandidaten WHERE status = 'stufe2'").fetchall()
    print(len(kand), "Kandidaten aus Stufe 2", flush=True)
    if not kand:                                                   # nichts zu prüfen: die eingefrorene Finalistenliste bleibt, wie sie ist
        print("Keine neuen Kandidaten aus Stufe 2: finalisten.json und finalisten_reihen.npz bleiben unverändert.")
        return
    grund_zahl, weiter = {}, []
    for z in kand:
        if not (z["n85_v"] > 0 and z["t85_v"] >= 1):
            g = "V1 nicht positiv genug"
        else:
            ok, nn, npos = nachbarn_ok(con, z)
            if not ok:
                g = "Nachbar-Einstellungen überwiegend negativ"
            else:
                tief = z["braucht"] == "t" or (z["best"] and ("tiefe" in z["best"] or "liq_entzug" in z["best"]))
                i0 = L.I_TIEFE if tief else L.I_T
                p, n, roh = tagesreihe(z, i0, L.I_ENDE, verzug=1)
                g = None if (n > 0 and roh - L.KOSTEN85 > 0) else "eine Kerze Verzögerung"
                if g is None:                                      # Kosten in bewegtem Markt: Slippage wächst mit der Spanne der letzten Kerze
                    v0 = L.I_T + L.SEGMENTE["t" if tief else "k"][1] * 288
                    _, nt, roh_t = tagesreihe(z, i0, v0, modell="bewegt")
                    _, nv, roh_v = tagesreihe(z, v0, L.I_ENDE, modell="bewegt")
                    if not (nt > 0 and nv > 0 and roh_t - L.KOSTEN85 > 0 and roh_v - L.KOSTEN85 > 0):
                        g = "Kosten in bewegtem Markt"
                if g is None:
                    alpha, t_alpha, beta = marktbereinigt(z, i0, L.I_ENDE)
                    if not (alpha > 0 and t_alpha >= 2):
                        g = "nach Abzug des Marktes kein gesicherter Ertrag"
        if g:
            grund_zahl[g] = grund_zahl.get(g, 0) + 1
            con.execute("UPDATE kandidaten SET status = 'verworfen_3', grund = ? WHERE id = ? AND gen = ?", (g, z["id"], z["gen"]))
        else:
            weiter.append(z)
    con.commit()
    print("verworfen in Stufe 3:", grund_zahl, "| übrig:", len(weiter), flush=True)
    # Gruppen: gleichlaufende Kandidaten (Korrelation der Tagesergebnisse > 0,8 über T und V1); je Gruppe der beste nach V1
    weiter.sort(key=lambda z: -z["sharpe_v"])
    weiter = [z for z in weiter if z["status"] == "stufe2"]
    reihen, final, gruppen = [], [], []
    frueher = json.loads((ERG / "schlusspruefung.json").read_text())["ergebnisse"] if (ERG / "schlusspruefung.json").exists() else []
    archiv = np.load(ERG / "finalisten_reihen.npz") if (ERG / "finalisten_reihen.npz").exists() else None
    alt_datei = json.loads((ERG / "finalisten.json").read_text()) if (ERG / "finalisten.json").exists() else {}
    alt_fin = {f["id"]: f for f in alt_datei.get("finalisten", [])}
    for e in frueher:                                              # schon geprüfte Finalisten: neue, gleichlaufende Kandidaten schließen sich ihnen an
        if archiv is not None and e["id"] in archiv.files and e["id"] in alt_fin:   # Tagesreihen liegen im Repository, auch ohne lokale Datenbank
            reihen.append(archiv[e["id"]].astype(np.float64)); final.append(alt_fin[e["id"]]); gruppen.append([e["id"]])
    n_frueher = len(final)
    for z in weiter:
        seg = L.SEGMENTE["t" if (z["braucht"] == "t" or (z["best"] and ("tiefe" in z["best"] or "liq_entzug" in z["best"]))) else "k"]
        r = np.asarray(np.load(L.AUS / f"tage_{z['gen']}.npy", mmap_mode="r")[z["zeile"]], dtype=np.float64)
        r = np.where(np.arange(len(r)) >= seg[0], r, 0.0)
        treffer = None
        for gi, rr in enumerate(reihen):
            gem = (r != 0) | (rr != 0)
            if gem.sum() > 30 and np.corrcoef(r[gem], rr[gem])[0, 1] > 0.8:
                treffer = gi
                break
        if treffer is None:
            reihen.append(r); final.append({k: z[k] for k in z.keys()}); gruppen.append([z["id"]])
            con.execute("UPDATE kandidaten SET status = 'final', grund = ? WHERE id = ? AND gen = ?", (f"Gruppe {len(final)}", z["id"], z["gen"]))
        else:
            gruppen[treffer].append(z["id"])
            con.execute("UPDATE kandidaten SET status = 'stufe3', grund = ? WHERE id = ? AND gen = ?", (f"Gruppe {treffer + 1}, vertreten durch {final[treffer]['id']}", z["id"], z["gen"]))
    con.commit()
    ERG.mkdir(parents=True, exist_ok=True)
    neue_mitglieder = sum(len(g) - 1 for g in gruppen[:n_frueher])        # neue Kandidaten, die sich einem früheren Finalisten anschließen
    if alt_datei and len(final) == n_frueher and neue_mitglieder == 0:      # nichts Neues: die eingefrorene Liste bleibt, wie sie ist
        print("Keine neuen Finalisten und keine neuen Gruppenmitglieder: finalisten.json und finalisten_reihen.npz bleiben unverändert.", flush=True)
        return
    # Frühere Finalisten behalten ihre Gruppengröße (plus neue Mitglieder); die Kopfzahlen laufen über alle Chargen weiter
    groesse = [(z.get("gruppengroesse", 1) + len(g) - 1) if i < n_frueher else len(g) for i, (z, g) in enumerate(zip(final, gruppen))]
    verworfen = dict(alt_datei.get("verworfen", {}))
    for g, n in grund_zahl.items():
        verworfen[g] = verworfen.get(g, 0) + n
    (ERG / "finalisten.json").write_text(json.dumps({"eingefroren": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "datenbank": str(L.DB),
        "stufe2": alt_datei.get("stufe2", 0) + len(kand), "verworfen": verworfen, "robust": alt_datei.get("robust", 0) + len(weiter), "gruppen": len(final), "davon_frueher_geprueft": n_frueher,
        "letzte_charge": {"stufe2": len(kand), "verworfen": grund_zahl, "robust": len(weiter), "neue_finalisten": len(final) - n_frueher, "neue_gruppenmitglieder": neue_mitglieder},
        "finalisten": [dict(z) | {"gruppengroesse": n} for z, n in zip(final, groesse)]}, ensure_ascii=False, indent=1))
    np.savez_compressed(ERG / "finalisten_reihen.npz", **{z["id"]: r.astype(np.float32) for z, r in zip(final, reihen)})   # für spätere Zyklen in frischen Sitzungen
    print("Finalisten (Gruppen):", len(final), "| davon schon früher geprüft:", n_frueher, flush=True)
    for z, g in list(zip(final, gruppen))[:40]:
        print(f"  {z['id']} {z['signal']:<20} th {z['th']} r {z['r']:+d} {z['f']:<11} k{z['k']:<2} {z['x']:<20} {z['m']:<6} | T n85 {z['n85_t']:>6} t {z['t85_t']:>5} | V1 n85 {z['n85_v']:>6} t {z['t85_v']:>5} | Gruppe {len(g)}")


# ---------------------------------------------------------------- Stufe 4: Schlussprüfung V2 (einmal)
def stufe4():
    """Schlussprüfung V2. Jeder Finalist wird genau einmal geprüft. Kommen in späteren Zyklen neue Finalisten dazu, wird die
    Korrektur für Mehrfachtests über ALLE jemals geprüften Finalisten gerechnet (die Hürde wird also mit jeder Charge strenger)."""
    L._init()
    con = db()
    fin = json.loads((ERG / "finalisten.json").read_text())
    pfad = ERG / "schlusspruefung.json"
    alt = json.loads(pfad.read_text()) if pfad.exists() else {"chargen": [], "ergebnisse": []}
    bekannt = {e["id"] for e in alt["ergebnisse"]}                  # Sperre nach Kennung: dieselbe Einstellung wird nie zweimal geprüft
    neu = [f for f in fin["finalisten"] if f["id"] not in bekannt]
    if not neu:
        print("Keine neuen Finalisten; die Schlussprüfung wird für bereits geprüfte Kandidaten nicht wiederholt."); return
    charge = len(alt["chargen"]) + 1
    erg = list(alt["ergebnisse"])
    for f in neu:
        z = con.execute("SELECT * FROM kandidaten WHERE id = ? AND gen = ?", (f["id"], f["gen"])).fetchone()
        pb, n, roh_basis = tagesreihe(z, I_V2, I_V2ENDE)                    # gemessene Slippage (Bericht)
        p, n, roh = tagesreihe(z, I_V2, I_V2ENDE, modell="bewegt")          # maßgeblich: Slippage wächst mit der Spanne der letzten Kerze
        _, _, roh2 = tagesreihe(z, I_V2, I_V2ENDE, modell="bewegt", faktor=2.0)
        t = t_wert(p)
        erg.append({"id": z["id"], "gen": z["gen"], "charge": charge, "signal": z["signal"], "th": z["th"], "r": z["r"], "f": z["f"], "k": z["k"], "x": z["x"], "m": z["m"],
                    "best": z["best"], "familie": z["familie"], "n_v2": n, "roh_v2": round(roh, 2), "n85_v2": round(roh - L.KOSTEN85, 2), "n0_v2": round(roh - L.GEBUEHR, 2),
                    "n85_2x_v2": round(roh2 - L.KOSTEN85, 2), "n85_basis_v2": round(roh_basis - L.KOSTEN85, 2), "t85_v2": round(t, 2), "p_v2": round(1 - phi(t), 6),
                    "sharpe_v2": round(float(p.mean() / p.std() * math.sqrt(365)), 2) if p.std() > 0 else 0.0, "ertrag_jahr_pct": round(float(p.mean()) * 365 / 100, 1),
                    "n85_t": z["n85_t"], "t85_t": z["t85_t"], "n85_v": z["n85_v"], "t85_v": z["t85_v"], "n0_t": z["n0_t"], "dauer_min": z["dauer_min"],
                    "gruppengroesse": f.get("gruppengroesse"),
                    "tiefe": bool(z["braucht"] == "t" or (z["best"] and ("tiefe" in z["best"] or "liq_entzug" in z["best"])))})
    m = len(erg)
    erg.sort(key=lambda e: e["p_v2"])
    grenze = 0
    for i, e in enumerate(erg, 1):                                 # Benjamini-Hochberg über alle jemals geprüften Finalisten, Fehlentdeckungsrate 10 %
        if e["p_v2"] <= 0.10 * i / m:
            grenze = i
    cm = sum(1 / i for i in range(1, m + 1))                        # Benjamini-Yekutieli: gilt auch bei beliebig abhängigen Kandidaten
    grenze_by = 0
    for i, e in enumerate(erg, 1):
        if e["p_v2"] <= 0.10 * i / (m * cm):
            grenze_by = i
    for i, e in enumerate(erg, 1):
        e["bh_bestanden"] = i <= grenze
        e["by_bestanden"] = i <= grenze_by
        e["validiert"] = bool(e["bh_bestanden"] and e["n85_v2"] > 0 and e["n85_2x_v2"] > 0)
        e["regel"] = f"{e['signal']}|{e['th']}|{e['r']}|{e['f']}|{e['k']}"
        con.execute("UPDATE kandidaten SET status = ?, grund = ? WHERE id = ? AND gen = ?",
                    ("validiert" if e["validiert"] else "verworfen_4", f"V2 netto {e['n85_v2']} bp, t {e['t85_v2']}, p {e['p_v2']}", e["id"], e["gen"]))
    con.commit()
    alt["chargen"].append({"charge": charge, "geoeffnet": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "neue_finalisten": len(neu)})
    aus = {"chargen": alt["chargen"], "finalisten_gesamt": m, "positiv_in_v2": sum(1 for e in erg if e["n85_v2"] > 0),
           "p_unter_5pct": sum(1 for e in erg if e["p_v2"] < 0.05), "zufallserwartung_p_unter_5pct": round(0.05 * m, 1), "bh_bestanden": grenze,
           "validiert": sum(1 for e in erg if e["validiert"]), "validiert_ohne_rebate_positiv": sum(1 for e in erg if e["validiert"] and e["n0_v2"] > 0),
           "validiert_streng_by": sum(1 for e in erg if e["validiert"] and e["by_bestanden"]),
           "validierte_einstiegsregeln": len({e["regel"] for e in erg if e["validiert"]}),
           "validierte_einstiegsregeln_streng": len({e["regel"] for e in erg if e["validiert"] and e["by_bestanden"]}), "ergebnisse": erg}
    pfad.write_text(json.dumps(aus, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in aus.items() if k != "ergebnisse"}, ensure_ascii=False))
    for e in erg[:40]:
        print(f"  {e['id']} {e['signal']:<20} th {e['th']} r {e['r']:+d} {e['f']:<11} k{e['k']:<2} {e['x']:<20} {e['m']:<6} {str(e['best'] or ''):<28} | V2 n {e['n_v2']:>5} n85 {e['n85_v2']:>7} n0 {e['n0_v2']:>7} t {e['t85_v2']:>5} p {e['p_v2']:<8} {'VALIDIERT' if e['validiert'] else ''}")


if __name__ == "__main__":
    {"statistik": statistik, "stufe3": stufe3, "stufe4": stufe4}[sys.argv[1]]()
