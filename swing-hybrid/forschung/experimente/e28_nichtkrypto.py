"""E28: Orderbuch-Stütze OS-1.1 und die Wochenend-Frage auf Aktien-, Index- und Rohstoff-Kontrakten.

Festlegung: forschung/protokoll.md Abschnitt 56 samt Präzisierungen. Daten: forschung/experimente/e28_daten.py.

    python -m forschung.experimente.e28_nichtkrypto            (aus swing-hybrid/; schreibt ergebnisse/e28_nichtkrypto.json)

Teil 1 rechnet die eingefrorene Regel (forschung/papier/strategien/orderbuch_stuetze.py, Parameter von OS-1.1) je Kontrakt und
bucht jeden Trade wie der Papier-Runner. Teil 2 misst je Wochenende die Steigung der Montags-Bewegung auf die Wochenend-Bewegung.
"""
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from forschung.papier import runner as R
from forschung.papier.strategien import orderbuch_stuetze as OS

UTC = dt.timezone.utc
H = 3_600_000
TAG = 24 * H
TAKER_BP, REBATE = 8.0, 0.85
SPANNE_MIN_BP = 0.5
VORLAUF_TAGE = 2
ZIEHUNGEN, STARTWERT = 5000, 28
P_GRENZE = 0.025
MIN_TRADES = 300
HAELFTE_AB = int(dt.datetime(2026, 9, 1, tzinfo=UTC).timestamp() * 1000)      # Teil 1: zweite Hälfte ab 01.09.2026
MIN_KONTRAKTE_WE = 30
ROHSTOFF = {"XAUUSDT", "XAGUSDT", "CLUSDT", "BZUSDT", "PAXGUSDT"}
FONDS = {"SOXLUSDT", "SOXSUSDT", "QQQUSDT", "EWYUSDT", "DRAMUSDT", "MUUUSDT"}
ERGEBNIS = ROOT / "forschung/ergebnisse/e28_nichtkrypto.json"
TRADES = ROOT / "forschung/ergebnisse/e28_trades.csv"
SPALTEN = ["sym", "ein", "aus", "richtung", "z", "roh_bp", "slip_bp", "funding_bp", "n85_bp", "n0_bp", "funding_fehlt"]


def os11() -> dict:
    """Eingefrorene Parameter von OS-1.1; bricht ab, wenn Regel oder Parameter nicht mehr dem Stand der Freigabe entsprechen."""
    cfg = json.loads((ROOT / "forschung/papier/OS-1.1/konfiguration.json").read_text())
    if R.pruefsumme(cfg) != cfg["strategie_sha256"]:
        raise SystemExit("Die Regel OS-1.1 entspricht nicht mehr dem Stand der Freigabe.")
    return cfg["parameter"]


def gruppe(sym: str) -> str:
    return "Rohstoff" if sym in ROHSTOFF else "Fonds" if sym in FONDS else "Einzelwert"


# ------------------------------------------------------------------------ Teil 1 ----
def monat(t_ms: int) -> str:
    return dt.datetime.fromtimestamp(t_ms / 1000, UTC).strftime("%Y-%m")


def monate_ohne_funding(zeit: np.ndarray, fund_zeit: np.ndarray) -> list:
    """Kalendermonate zwischen erster und letzter Kerze, für die es keine einzige Funding-Angabe gibt (Monatsdatei fehlt)."""
    if not len(zeit):
        return []
    d, ende, alle = dt.datetime.fromtimestamp(int(zeit[0]) / 1000, UTC).replace(day=1), monat(int(zeit[-1])), []
    while d.strftime("%Y-%m") <= ende:
        alle.append(d.strftime("%Y-%m"))
        d = (d + dt.timedelta(days=32)).replace(day=1)
    da = {monat(int(z)) for z in fund_zeit}
    return [m for m in alle if m not in da]


def trades_kontrakt(sym: str, zeit: np.ndarray, ohlc: np.ndarray, u: np.ndarray, fund_zeit: np.ndarray, fund_rate: np.ndarray,
                    spanne_bp: float, p: dict) -> list:
    """Alle abgeschlossenen Trades der Regel auf einem Kontrakt, gebucht wie im Papier-Runner (Basispunkte je Trade).

    Fällt ein Trade in einen Monat ohne Funding-Angabe, wird sein Funding mit null gebucht und er trägt funding_fehlt = True."""
    if len(zeit) < p["min_perioden"]:
        return []
    ohne = set(monate_ohne_funding(zeit, fund_zeit))
    kz = [(int(z), float(o), float(h), float(l), float(c)) for z, (o, h, l, c) in zip(zeit, ohlc)]
    start_ms = int(zeit[0]) + VORLAUF_TAGE * TAG
    slip = 2 * max(SPANNE_MIN_BP, spanne_bp)                           # zwei Orders, je die gemessene Yubit-Spanne
    out = []
    for t in OS.trades(kz, [float(x) for x in u], p, start_ms):
        if t["aus"] is None:
            continue                                                   # am Datenende noch offen: zählt nicht
        roh = t["richtung"] * (t["aus_kurs"] / t["ein_kurs"] - 1) * 1e4
        im_trade = (fund_zeit > t["ein"]) & (fund_zeit <= t["aus"])
        fund = float(np.sum(-t["richtung"] * fund_rate[im_trade] * 1e4))
        out.append({"sym": sym, "ein": int(t["ein"]), "aus": int(t["aus"]), "richtung": int(t["richtung"]), "z": t["z"], "roh_bp": roh,
                    "slip_bp": slip, "funding_bp": fund, "n85_bp": roh - slip + fund - 2 * TAKER_BP * (1 - REBATE),
                    "n0_bp": roh - slip + fund - 2 * TAKER_BP, "funding_fehlt": monat(int(t["ein"])) in ohne or monat(int(t["aus"])) in ohne})
    return out


def tage_stichprobe(tag: np.ndarray, wert: np.ndarray, ziehungen: int = ZIEHUNGEN, startwert: int = STARTWERT) -> float:
    """Anteil der Ziehungen ganzer Tage (mit Zurücklegen), in denen das Mittel über alle Trades der gezogenen Tage nicht über null liegt."""
    tage, index = np.unique(tag, return_inverse=True)
    summe = np.bincount(index, weights=wert, minlength=len(tage))
    zahl = np.bincount(index, minlength=len(tage)).astype(float)
    rng = np.random.default_rng(startwert)
    zug = rng.integers(0, len(tage), size=(ziehungen, len(tage)))
    mittel = summe[zug].sum(1) / zahl[zug].sum(1)
    return float(np.mean(mittel <= 0))


def kennzahlen1(trades: list) -> dict:
    if not trades:
        return {"trades": 0}
    n85, n0, roh = (np.array([t[k] for t in trades]) for k in ("n85_bp", "n0_bp", "roh_bp"))
    return {"trades": len(trades), "roh_bp": float(roh.mean()), "n85_bp": float(n85.mean()), "n0_bp": float(n0.mean()),
            "treffer_n85": float(np.mean(n85 > 0)), "slip_bp": float(np.mean([t["slip_bp"] for t in trades])),
            "funding_bp": float(np.mean([t["funding_bp"] for t in trades]))}


def urteil1(trades: list) -> dict:
    alle = kennzahlen1(trades)
    erste = kennzahlen1([t for t in trades if t["ein"] < HAELFTE_AB])
    zweite = kennzahlen1([t for t in trades if t["ein"] >= HAELFTE_AB])
    if not trades:
        return {"alle": alle, "erste_haelfte": erste, "zweite_haelfte": zweite, "p": None, "einstufung": "A"}
    tag = np.array([t["ein"] // TAG for t in trades])
    p = tage_stichprobe(tag, np.array([t["n85_bp"] for t in trades]))
    positiv = alle["n85_bp"] > 0
    haelften = erste["trades"] > 0 and zweite["trades"] > 0 and erste["n85_bp"] > 0 and zweite["n85_bp"] > 0
    stufe = "C" if (alle["trades"] >= MIN_TRADES and positiv and p < P_GRENZE and haelften) else "B" if positiv else "A"
    return {"alle": alle, "erste_haelfte": erste, "zweite_haelfte": zweite, "p": p, "tage_mit_einstieg": int(len(np.unique(tag))), "einstufung": stufe}


def teil1(universum, laden, spannen: dict, trades_aus: list = None) -> dict:
    """universum: Liste der Symbole; laden(sym) -> dict mit zeit, ohlc, u, fund_zeit, fund_rate; spannen: Symbol -> Spanne in bp.

    trades_aus: Liste, an die alle gewerteten Trades angehängt werden (für die Ablage als Tabelle)."""
    p = os11()
    trades, je_kontrakt = [], {}
    for sym in universum:
        d = laden(sym)
        t = trades_kontrakt(sym, d["zeit"], d["ohlc"], d["u"], d["fund_zeit"], d["fund_rate"], spannen[sym], p)
        trades += t
        luecken = int(np.sum(np.diff(d["zeit"]) != R.KERZE_MS)) if len(d["zeit"]) > 1 else 0
        je_kontrakt[sym] = dict(kennzahlen1(t), gruppe=gruppe(sym), spanne_bp=float(spannen[sym]), kerzen=int(len(d["zeit"])),
                                u_fehlt=int(np.sum(~np.isfinite(d["u"]))), luecken=luecken,
                                von=str(dt.datetime.fromtimestamp(int(d["zeit"][0]) / 1000, UTC).date()) if len(d["zeit"]) else "",
                                funding_fehlt_monate=monate_ohne_funding(d["zeit"], d["fund_zeit"]), fehlende_dateien=list(d.get("fehlend", [])))
    if trades_aus is not None:
        trades_aus += trades
    we = lambda t: dt.datetime.fromtimestamp(t["ein"] / 1000, UTC).weekday() >= 5
    return {"regel": "OS-1.1 unverändert", "parameter": p, "kontrakte": len(universum), **urteil1(trades),
            "funding_fehlt": {"trades": int(sum(t["funding_fehlt"] for t in trades)), "gebucht_mit": 0.0,
                              "nur_trades_mit_funding_angabe": kennzahlen1([t for t in trades if not t["funding_fehlt"]])},
            "je_gruppe": {g: kennzahlen1([t for t in trades if gruppe(t["sym"]) == g]) for g in ("Einzelwert", "Fonds", "Rohstoff")},
            "wochenende": kennzahlen1([t for t in trades if we(t)]), "werktag": kennzahlen1([t for t in trades if not we(t)]),
            "long": kennzahlen1([t for t in trades if t["richtung"] > 0]), "short": kennzahlen1([t for t in trades if t["richtung"] < 0]),
            "je_kontrakt": je_kontrakt}


# ------------------------------------------------------------------------ Teil 2 ----
def wochenenden(von_ms: int, bis_ms: int) -> list:
    """(a, b, c) in ms für jedes Wochenende: Samstag 01:00, Sonntag 23:00, Montag 21:00 UTC, sofern c vor bis_ms liegt."""
    d = dt.datetime.fromtimestamp(von_ms / 1000, UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    while d.weekday() != 5:
        d += dt.timedelta(days=1)
    out = []
    while True:
        a, b, c = d + dt.timedelta(hours=1), d + dt.timedelta(days=1, hours=23), d + dt.timedelta(days=2, hours=21)
        if c.timestamp() * 1000 >= bis_ms:
            return out
        if a.timestamp() * 1000 >= von_ms:
            out.append(tuple(int(x.timestamp() * 1000) for x in (a, b, c)))
        d += dt.timedelta(days=7)


def gestutzt(x: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(x, [1, 99])
    y = np.clip(x, lo, hi)
    return y - y.mean()


def steigung(w: np.ndarray, m: np.ndarray) -> float:
    ws, ms_ = gestutzt(w), gestutzt(m)
    return float(np.sum(ws * ms_) / np.sum(ws * ws)) if np.sum(ws * ws) > 0 else float("nan")


def handel(w: np.ndarray, m: np.ndarray, spanne_bp: np.ndarray, vorzeichen: int) -> dict:
    """Ein Wochenende der Handelsfassung: Gewichte aus dem gestutzten, bereinigten W (Summe der Beträge 1), Ertrag mit dem unveränderten M."""
    ws = gestutzt(w)
    if np.sum(np.abs(ws)) == 0:
        return {"brutto": 0.0, "n85": 0.0, "n0": 0.0}
    g = vorzeichen * ws / np.sum(np.abs(ws))
    brutto = float(np.sum(g * m))
    sp = np.maximum(SPANNE_MIN_BP, spanne_bp)
    kosten = lambda gebuehr: float(np.sum(np.abs(g) * 2 * (gebuehr + sp)) / 1e4)
    return {"brutto": brutto, "n85": brutto - kosten(TAKER_BP * (1 - REBATE)), "n0": brutto - kosten(TAKER_BP)}


def teil2(kurse: dict, spannen: dict, bis_ms: int) -> dict:
    """kurse: Symbol -> {Beginn der Stundenkerze in ms: Eröffnung}; spannen: Symbol -> bp."""
    from scipy import stats
    syms = sorted(kurse)
    von = min(min(k) for k in kurse.values() if k)
    je_we, rest = [], []
    for a, b, c in wochenenden(von, bis_ms):
        dabei = [s for s in syms if a in kurse[s] and b in kurse[s] and c in kurse[s]]
        if len(dabei) < MIN_KONTRAKTE_WE:
            rest.append({"samstag": str(dt.datetime.fromtimestamp(a / 1000, UTC).date()), "kontrakte": len(dabei)})
            continue
        w = np.array([kurse[s][b] / kurse[s][a] - 1 for s in dabei])
        m = np.array([kurse[s][c] / kurse[s][b] - 1 for s in dabei])
        st_we = steigung(w, m)
        if not np.isfinite(st_we):                                     # keine Streuung von W: Steigung nicht bestimmbar
            rest.append({"samstag": str(dt.datetime.fromtimestamp(a / 1000, UTC).date()), "kontrakte": len(dabei), "grund": "keine Streuung"})
            continue
        je_we.append({"samstag": str(dt.datetime.fromtimestamp(a / 1000, UTC).date()), "kontrakte": len(dabei), "steigung": st_we,
                      "korb_w": float(w.mean()), "korb_m": float(m.mean()), "_w": w, "_m": m, "_sp": np.array([spannen[s] for s in dabei])})
    st = np.array([x["steigung"] for x in je_we])
    if len(st) < 3:
        return {"wochenenden": len(st), "einstufung": "A", "hinweis": "zu wenige Wochenenden", "ausgelassen": rest, "je_wochenende": [{k: v for k, v in x.items() if not k.startswith("_")} for x in je_we]}
    t, p = stats.ttest_1samp(st, 0.0)
    aus = {"wochenenden": int(len(st)), "kontrakte_median": int(np.median([x["kontrakte"] for x in je_we])), "steigung_mittel": float(st.mean()),
           "steigung_median": float(np.median(st)), "t": float(t), "p": float(p), "anteil_negativ": float(np.mean(st < 0)),
           "gesichert": bool(p < P_GRENZE), "ausgelassen": rest,
           "korb_korrelation": float(np.corrcoef([x["korb_w"] for x in je_we], [x["korb_m"] for x in je_we])[0, 1])}
    einstufung = "A"
    if aus["gesichert"]:
        vz = -1 if st.mean() < 0 else 1
        h = [handel(x["_w"], x["_m"], x["_sp"], vz) for x in je_we]
        n85, n0, br = (np.array([y[k] for y in h]) for k in ("n85", "n0", "brutto"))
        halb = -(-len(h) // 2)
        tw = float(n85.mean() / (n85.std(ddof=1) / np.sqrt(len(n85)))) if n85.std(ddof=1) > 0 else 0.0
        aus["handel"] = {"richtung": "Umkehr" if vz < 0 else "Fortsetzung", "brutto_mittel": float(br.mean()), "n85_mittel": float(n85.mean()),
                         "n0_mittel": float(n0.mean()), "t_n85": tw, "n85_erste_haelfte": float(n85[:halb].mean()), "n85_zweite_haelfte": float(n85[halb:].mean()),
                         "anteil_positiv_n85": float(np.mean(n85 > 0)), "je_wochenende_n85": [float(x) for x in n85],
                         "je_wochenende_brutto": [float(x) for x in br], "je_wochenende_n0": [float(x) for x in n0]}
        ok = n85.mean() > 0 and tw > 2 and n85[:halb].mean() > 0 and n85[halb:].mean() > 0
        einstufung = "C" if ok else "B"
    aus["einstufung"] = einstufung
    aus["je_wochenende"] = [{k: v for k, v in x.items() if not k.startswith("_")} for x in je_we]
    return aus


def sauber(x):
    """Für die Ergebnisdatei: numpy-Zahlen zu Python-Zahlen, „keine Zahl“ zu null."""
    if isinstance(x, dict):
        return {k: sauber(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [sauber(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return None if not np.isfinite(x) else float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


# ----------------------------------------------------------------------- Hauptlauf ----
def haupt() -> dict:
    from forschung.experimente import e28_daten as D
    u1, u2 = D.universum_teil1(), D.universum_teil2()
    sp = {r.symbol: float(r.spanne_bp) for r in D.kandidaten().itertuples()}

    def laden1(sym):
        with np.load(D.ZIEL / "teil1" / f"{sym}.npz") as z:
            d = {k: z[k] for k in ("zeit", "ohlc", "u", "fund_zeit", "fund_rate")}
            d["fehlend"] = [" ".join(x) for x in json.loads(str(z["fehlend"]))] if "fehlend" in z else []
            return d
    kurse = {}
    for sym in u2.symbol:
        datei = D.ZIEL / "teil2" / f"{sym}.npz"
        if datei.exists():
            with np.load(datei) as z:
                if len(z["zeit"]):
                    kurse[sym] = dict(zip((int(x) for x in z["zeit"]), (float(x) for x in z["ohlc"][:, 0])))
    bis = int(D.YUBIT_BIS.timestamp() * 1000)
    trades = []
    erg = {"experiment": "E28", "festlegung": "forschung/protokoll.md Abschnitt 56", "stand_des_programms": stand(),
           "daten": {"teil_1_bis": str(D.ENDE_TEIL1), "teil_2_bis": str(D.YUBIT_BIS.date()), "trades_tabelle": TRADES.name},
           "teil_1": teil1(list(u1.symbol), laden1, sp, trades), "teil_2": dict(teil2(kurse, sp, bis), kontrakte_mit_daten=len(kurse))}
    ERGEBNIS.parent.mkdir(exist_ok=True)
    ERGEBNIS.write_text(json.dumps(sauber(erg), ensure_ascii=False, indent=1, allow_nan=False))
    zeile = lambda t: ",".join(f"{t[k]:.4f}" if isinstance(t[k], float) else str(int(t[k])) if isinstance(t[k], (bool, np.bool_)) else str(t[k]) for k in SPALTEN)
    TRADES.write_text("\n".join([",".join(SPALTEN)] + [zeile(t) for t in sorted(trades, key=lambda t: (t["ein"], t["sym"]))]) + "\n")
    return erg


def stand() -> str:
    """Kurzname des Programmstands (git), damit das Ergebnis einem Stand zugeordnet werden kann."""
    import subprocess
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


if __name__ == "__main__":
    e = haupt()
    a, b = e["teil_1"], e["teil_2"]
    print("Teil 1:", a["einstufung"], a["alle"], "p", a["p"])
    print("Teil 2:", b["einstufung"], {k: b.get(k) for k in ("wochenenden", "steigung_mittel", "t", "p")})
