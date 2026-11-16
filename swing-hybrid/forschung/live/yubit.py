"""Misst am öffentlichen Yubit-Orderbuch, was eine Marktorder in diesem Moment kosten würde. Kein Schlüssel, keine Order."""
import json
import time
import urllib.request

BASIS = "https://openapi.yubit.com/oapi/contract/market/public/v1/orderbooks"


def messen(coin: str, usd: float, kauf: bool) -> dict:
    """Kosten gegenüber der Mitte des Orderbuchs in Basispunkten, für eine Order über `usd`. Wirft bei unbrauchbarer Antwort."""
    req = urllib.request.Request(f"{BASIS}?depth=200&symbol={coin}USDT", headers={"User-Agent": "papierhandel/1.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        roh = json.loads(r.read().decode())
    if roh.get("code") != 0:
        raise RuntimeError(f"Yubit meldet {roh.get('code')} {roh.get('message')}")
    d = roh["data"]
    geld = sorted(((float(p), float(q)) for p, q in d["b"]), reverse=True)
    brief = sorted((float(p), float(q)) for p, q in d["a"])
    if not geld or not brief:
        raise RuntimeError("leeres Orderbuch")
    mitte = (geld[0][0] + brief[0][0]) / 2
    rest, wert, menge = usd, 0.0, 0.0
    for p, q in (brief if kauf else geld):                           # Stufe für Stufe durch das Buch, bis die Order gefüllt ist
        nimm = min(rest, p * q)
        wert += nimm; menge += nimm / p; rest -= nimm
        if rest <= 1e-9:
            break
    schnitt = wert / menge if menge else float("nan")
    kosten = (schnitt / mitte - 1) * 1e4 * (1 if kauf else -1)
    return {"zeit": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "coin": coin, "seite": "Kauf" if kauf else "Verkauf", "usd": round(usd, 0),
            "kosten_bp": round(kosten, 2), "spanne_bp": round((brief[0][0] / geld[0][0] - 1) * 1e4, 2), "gefuellt": rest <= 1e-9}
