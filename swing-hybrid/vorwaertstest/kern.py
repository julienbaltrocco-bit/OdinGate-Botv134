"""Rechenlogik des Vorwärtstests, ohne Netz und ohne Dateien (dadurch gut testbar).

Der Kandidat: Steht der Schlusskurs der letzten vollen Stunde höher als vor 336 Stunden (14 Tage), dann Long,
steht er tiefer, dann Short. Jeder Coin gleich groß. Die Größe wird beim Einstieg festgelegt und bis zum
Richtungswechsel nicht angepasst (wie im Backtest).
"""
import math

TAKER, REBATE = 0.0008, 0.85
STUNDE_MS = 3_600_000
TAG_MS = 24 * STUNDE_MS
TAGESREGEL_KARENZ_MS = 60_000   # Tagesregel: die Richtung wird frühestens eine Minute nach dem Tageswechsel übernommen
RUECKBLICK_STUNDEN = 336


def richtung(schluss_jetzt: float, schluss_frueher: float) -> int:
    if schluss_jetzt > schluss_frueher:
        return 1
    if schluss_jetzt < schluss_frueher:
        return -1
    return 0


def menge_runden(nominal: float, preis: float, schritt: float, minimum: float) -> float:
    """Stückzahl für einen Zielbetrag: auf die Schrittweite abgerundet. Unter der Mindestmenge: 0 (Coin wird ausgelassen)."""
    if preis <= 0 or schritt <= 0:
        return 0.0
    n = math.floor(nominal / preis / schritt + 1e-9)
    q = n * schritt
    stellen = max(0, -int(math.floor(math.log10(schritt) + 1e-9)))
    q = round(q, stellen)
    return q if q >= minimum - 1e-12 else 0.0


def als_text(menge: float, schritt: float) -> str:
    stellen = max(0, -int(math.floor(math.log10(schritt) + 1e-9)))
    return f"{menge:.{stellen}f}"


def buch_fill(kauf: bool, menge: float, buch: dict) -> tuple[float, float]:
    """Füllt eine sofort ausgeführte Order gegen das Orderbuch. Gibt (Durchschnittskurs, gefüllte Menge) zurück.

    Kauf läuft die Briefseite hoch, Verkauf die Geldseite runter. Reicht die sichtbare Tiefe nicht, bleibt ein Rest.
    """
    rest, wert = menge, 0.0
    for preis, groesse in (buch["brief"] if kauf else buch["geld"]):
        teil = min(rest, groesse)
        wert += teil * preis
        rest -= teil
        if rest <= 1e-12:
            break
    gefuellt = menge - max(rest, 0.0)
    return (wert / gefuellt if gefuellt > 0 else 0.0), gefuellt


def mitte(buch: dict) -> float:
    return (buch["geld"][0][0] + buch["brief"][0][0]) / 2


def spanne_bp(buch: dict) -> float:
    m = mitte(buch)
    return (buch["brief"][0][0] - buch["geld"][0][0]) / m * 1e4


def slippage(kauf: bool, fuellkurs: float, signalkurs: float) -> float:
    """Wie viel schlechter als der Signalkurs gefüllt wurde (positiv = schlechter)."""
    return (1 if kauf else -1) * (fuellkurs - signalkurs) / signalkurs


def neuer_zustand(kapital: float) -> dict:
    return {"version": 1, "kapital": kapital, "letzte_kerze": 0, "pos": {}, "kasse": {}, "gebuehr": 0.0, "rebate": 0.0,
            "funding": 0.0, "funding_zeit": {}, "tag": "", "tag_start": 0.0, "gesperrt_tag": "", "start": "", "orders": 0}


def buchen(z: dict, coin: str, d_menge: float, preis: float, gebuehr: float, rebate: float) -> None:
    """Eine Ausführung ins Papier-/Kontrollbuch schreiben (d_menge > 0 Kauf, < 0 Verkauf)."""
    z["kasse"][coin] = z["kasse"].get(coin, 0.0) - d_menge * preis
    neu = z["pos"].get(coin, 0.0) + d_menge
    z["pos"][coin] = 0.0 if abs(neu) < 1e-12 else neu
    z["gebuehr"] += gebuehr
    z["rebate"] += rebate
    z["orders"] += 1


def vermoegen(z: dict, kurse: dict) -> dict:
    """Ergebnis seit Start in USDT: vor Gebühren, nach voller Gebühr, mit Rebate. `kurse`: Coin -> Mittelkurs."""
    brutto = sum(z["kasse"].get(c, 0.0) + z["pos"].get(c, 0.0) * kurse.get(c, 0.0) for c in set(z["kasse"]) | set(z["pos"]))
    ohne = brutto - z["gebuehr"] + z["funding"]
    return {"brutto": brutto, "gebuehr": z["gebuehr"], "rebate": z["rebate"], "funding": z["funding"],
            "netto_ohne_rebate": ohne, "netto_mit_rebate": ohne + z["rebate"]}


def funding_faellig(letzte_ms: int, jetzt_ms: int, minuten: int) -> int:
    """Anzahl der Funding-Zeitpunkte (Raster ab 00:00 UTC) zwischen letzter Abrechnung und jetzt."""
    raster = minuten * 60_000
    if letzte_ms <= 0 or raster <= 0:
        return 0
    return max(0, jetzt_ms // raster - letzte_ms // raster)
