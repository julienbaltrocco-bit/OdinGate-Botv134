"""Rechenteil des Datensammlers, ohne Netz und ohne Dateien (dadurch gut testbar).

Drei Tabellen entstehen, je Lauf werden Zeilen angehängt (Zeit `t` = Beginn des Laufs in Sekunden seit 1970, UTC):

- ticker:  Yubit, ein Abruf für alle Kontrakte. Geld, Brief, Mark, Index, offene Kontrakte, Funding-Vorschau.
           Kontrakte der Gruppe A (Aktien, Indizes, Rohstoffe, zehn Coins) in jedem Lauf, alle übrigen einmal je Stunde.
- tiefe:   Yubit-Orderbuch (ganzes sichtbares Buch) verdichtet auf Merkmale: bester Geld-/Briefkurs mit Menge, Zahl der Stufen,
           Volumen je Seite in USDT (gesamt und in Bändern um die Mitte: g20 = Geldseite bis 20 Basispunkte unter der Mitte,
           b20 = Briefseite bis 20 darüber; ganze USDT), Kosten einer Marktorder gegenüber der Mitte in Basispunkten
           (k1500 = Kauf über 1.500 USDT, v1500 = Verkauf; leer, wenn das sichtbare Buch nicht reicht). `versatz_ms`: Zeit des
           Buchs laut Börse minus Beginn des Laufs. Coins in jedem Lauf, die übrigen reihum.
- binance: bester Geld-/Briefkurs mit Menge, Mark, Index und Funding derselben Kontrakte bei Binance (die Spanne fehlt im
           öffentlichen Binance-Archiv; Tiefe, Kerzen und offene Kontrakte stehen dort und werden nicht mitgeschrieben).
           `zeit_ms`: Zeit des Kurses laut Binance (der Abruf folgt erst nach den Yubit-Orderbüchern).

Bänder: Die Grenze gehört zum Band (eine Stufe genau 20 Basispunkte neben der Mitte zählt zu g20 bzw. b20).

Zahlen der Börsen werden als Text übernommen, wie sie geliefert wurden (kein Runden, kein Umrechnen).
"""
TICKER = ["t", "sym", "geld", "brief", "mark", "index", "oi", "funding_ppm"]
BINANCE = ["t", "sym", "zeit_ms", "geld", "geld_menge", "brief", "brief_menge", "mark", "index", "funding"]
LAEUFE = ["t", "lauf_nr", "boersenzeit_ms", "ticker", "tiefe_soll", "tiefe_ist", "binance", "dauer_s", "fehler"]
RAND = 1e-12        # Bandgrenze eingeschlossen: so entscheidet nicht die Rundung der Gleitkommazahl, ob eine Stufe genau auf der Grenze zählt


def tiefe_spalten(baender_bp: list, groessen_usd: list) -> list:
    return (["t", "sym", "versatz_ms", "geld", "geld_menge", "brief", "brief_menge", "stufen_geld", "stufen_brief", "summe_geld", "summe_brief"]
            + [f"g{b}" for b in baender_bp] + [f"b{b}" for b in baender_bp]
            + [x for g in groessen_usd for x in (f"k{g}", f"v{g}")])


def ticker_zeilen(liste: list, t: int, gruppe_a: set, alle: bool) -> list:
    """Zeilen aus der Ticker-Liste von Yubit. `alle`: auch die Kontrakte außerhalb der Gruppe A (einmal je Stunde)."""
    out = []
    for x in liste:
        sym = x.get("symbol", "")
        if not sym or not (alle or sym in gruppe_a):
            continue
        out.append({"t": t, "sym": sym, "geld": x.get("bidPrice", ""), "brief": x.get("askPrice", ""), "mark": x.get("markPrice", ""),
                    "index": x.get("indexPrice", ""), "oi": x.get("openInterest", ""), "funding_ppm": x.get("fundingRate", "")})
    return out


def tiefe_auswahl(coins: list, reihum: list, lauf_nr: int, teile: int) -> list:
    """Welche Orderbücher dieser Lauf holt: alle Coins, dazu jeder `teile`-te der übrigen Kontrakte (reihum, jeder alle `teile` Läufe)."""
    teile = max(1, int(teile))
    return list(coins) + [s for i, s in enumerate(reihum) if i % teile == lauf_nr % teile]


def _zahl(x) -> str:
    """Basispunkte mit zwei Nachkommastellen, ohne überflüssige Nullen."""
    return f"{x:.2f}".rstrip("0").rstrip(".") if x == x else ""


def _ganz(x) -> str:
    """Volumen in ganzen USDT."""
    return str(int(round(x)))


def _kosten_bp(seite: list, mitte: float, usd: float, kauf: bool) -> str:
    """Kosten einer Marktorder über `usd` gegenüber der Mitte in Basispunkten; leer, wenn das sichtbare Buch nicht reicht."""
    rest, wert, menge = usd, 0.0, 0.0
    for p, q in seite:
        nimm = min(rest, p * q)
        wert += nimm; menge += nimm / p; rest -= nimm
        if rest <= 1e-9:
            break
    if rest > 1e-9 or menge <= 0:
        return ""
    return _zahl((wert / menge / mitte - 1) * 1e4 * (1 if kauf else -1))


def buch_merkmale(d: dict, t: int, baender_bp: list, groessen_usd: list) -> dict:
    """Merkmale eines Yubit-Orderbuchs (`data` der Antwort). Wirft ValueError bei leerem oder gekreuztem Buch."""
    geld = sorted(((float(p), float(q)) for p, q in d.get("b") or [] if float(q) > 0), reverse=True)     # bester Geldkurs zuerst
    brief = sorted((float(p), float(q)) for p, q in d.get("a") or [] if float(q) > 0)                    # bester Briefkurs zuerst
    if not geld or not brief:
        raise ValueError("leeres Orderbuch")
    if geld[0][0] >= brief[0][0]:
        raise ValueError("gekreuztes Orderbuch")
    mitte = (geld[0][0] + brief[0][0]) / 2
    # Text der Börse für die besten Kurse, aus denselben Stufen wie die Rechnung (nur Stufen mit Menge)
    roh_g = max((x for x in d["b"] if float(x[1]) > 0), key=lambda x: float(x[0]))
    roh_b = min((x for x in d["a"] if float(x[1]) > 0), key=lambda x: float(x[0]))
    z = {"t": t, "sym": d.get("s", ""), "versatz_ms": int(d.get("ts") or 0) // 1000 - t * 1000, "geld": roh_g[0], "geld_menge": roh_g[1],
         "brief": roh_b[0], "brief_menge": roh_b[1], "stufen_geld": len(geld), "stufen_brief": len(brief),
         "summe_geld": _ganz(sum(p * q for p, q in geld)), "summe_brief": _ganz(sum(p * q for p, q in brief))}
    for b in baender_bp:                                               # Volumen (USDT) bis b Basispunkte unter der Mitte
        z[f"g{b}"] = _ganz(sum(p * q for p, q in geld if p >= mitte * (1 - b / 1e4) * (1 - RAND)))
    for b in baender_bp:                                               # und bis b Basispunkte über der Mitte
        z[f"b{b}"] = _ganz(sum(p * q for p, q in brief if p <= mitte * (1 + b / 1e4) * (1 + RAND)))
    for g in groessen_usd:
        z[f"k{g}"] = _kosten_bp(brief, mitte, g, True)
        z[f"v{g}"] = _kosten_bp(geld, mitte, g, False)
    return z


def binance_zeilen(buecher: list, praemien: list, t: int, symbole: set) -> list:
    """Zeilen aus /fapi/v1/ticker/bookTicker und /fapi/v1/premiumIndex (je alle Symbole), beschränkt auf `symbole`."""
    p = {x.get("symbol"): x for x in (praemien if isinstance(praemien, list) else []) if isinstance(x, dict)}
    out = []
    for x in (buecher if isinstance(buecher, list) else []):
        sym = x.get("symbol") if isinstance(x, dict) else None
        if sym not in symbole:
            continue
        y = p.get(sym, {})
        out.append({"t": t, "sym": sym, "zeit_ms": x.get("time", ""), "geld": x.get("bidPrice", ""), "geld_menge": x.get("bidQty", ""), "brief": x.get("askPrice", ""),
                    "brief_menge": x.get("askQty", ""), "mark": y.get("markPrice", ""), "index": y.get("indexPrice", ""),
                    "funding": y.get("lastFundingRate", "")})
    return out
