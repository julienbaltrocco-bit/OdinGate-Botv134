"""Rechnet eine Regel-Variante auf den Aufzeichnungen eines laufenden Tests nach (gleiche Beobachtungen, gleicher Bot-Code).

Bei jedem Lauf schreibt der Bot je Coin den besten Geld- und Briefkurs und die gemessenen Kosten einer Order in
Standardgröße nach spannen.csv. Daraus wird für jeden früheren Lauf eine Börse nachgestellt; der echte Bot-Schritt
(bot.schritt) läuft darauf mit einer anderen Einstellung. Stundenkerzen kommen aus dem öffentlichen Yubit-Verlauf.

    python3 -m vorwaertstest.nachrechnen --quelle vorwaertstest/lauf --config vorwaertstest/config_lauf_trail.json \
            --ziel vorwaertstest/lauf_trail --fuellungen-der-quelle

Danach Dashboard-Daten und Board-Datei neu schreiben (dashboard_daten, board_verschluesseln), wie in stunde.sh.

Grenzen: Eine Order wird zum Mittelkurs zuzüglich der in diesem Lauf gemessenen Kosten gefüllt (nicht gegen das volle
Orderbuch von damals). Dreht eine Position in einem Lauf (Schließen und neuer Einstieg), wird die zweite Order zum
selben Kurs gefüllt wie die erste, also etwas zu günstig. Mit --fuellungen-der-quelle gelten nur die Orders des ersten
Laufs der Quelle (die gemeinsamen Einstiege) zu deren tatsächlichem Füllkurs. Funding wird anteilig aus dem in der
Quelle gebuchten Funding übernommen. Das Ergebnis ist eine Nachrechnung, kein Vorwärtstest.
"""
import argparse
import datetime as dt
import json
import shutil
from pathlib import Path

from . import bot, kern
from .yubit import Yubit, YubitFehler

H = kern.STUNDE_MS
GROSS = 1e15


def ms(zeit: str) -> int:
    return int(dt.datetime.fromisoformat(zeit).replace(tzinfo=dt.timezone.utc).timestamp() * 1000)


class Aufzeichnung:
    """Nachgestellte Börse für genau einen früheren Lauf."""
    key = secret = ""

    def __init__(self, stunden: dict, kontrakte: dict, fuellungen: dict):
        self.stunden, self.kontrakte, self.fuellungen, self.aufrufe = stunden, kontrakte, fuellungen, 0
        self.jetzt, self.zeit, self.zeilen = 0, "", {}

    def setze(self, zeit: str, zeilen: dict) -> int:
        self.zeit, self.zeilen = zeit, zeilen
        self.jetzt = ms(zeit) + 30_000                          # die Aufzeichnung kennt nur die Minute
        return self.jetzt

    def _zeile(self, sym: str) -> dict:
        r = self.zeilen.get(sym.removesuffix("USDT"))
        if r is None:
            raise YubitFehler(f"{sym}: in diesem Lauf keine Aufzeichnung")
        return r

    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        self.aufrufe += 1
        k = self.stunden[sym.removesuffix("USDT")]
        if start_ms is not None:
            return [{"start": start_ms, "open": 0.0, "high": 0.0, "low": 0.0, "close": k[start_ms]}] if start_ms in k else []
        letzte = self.jetzt // H * H - H                        # letzte abgeschlossene Stunde
        return [{"start": t, "open": 0.0, "high": 0.0, "low": 0.0, "close": k[t]} for t in (letzte - H, letzte) if t in k]

    def kontrakt(self, sym):
        self.aufrufe += 1
        return self.kontrakte[sym.removesuffix("USDT")]

    def ticker(self, sym):
        self.aufrufe += 1
        r = self._zeile(sym)
        g, b = float(r["geld"]), float(r["brief"])
        return {"geld": g, "brief": b, "letzter": (g + b) / 2, "mark": (g + b) / 2, "funding": 0.0, "umsatz24h": 0.0}   # Funding wird getrennt übernommen

    def buch(self, sym, tiefe=25):
        """Bester Geld- und Briefkurs wie aufgezeichnet; dahinter eine Stufe zum damals gemessenen Füllkurs einer Standard-Order."""
        self.aufrufe += 1
        r = self._zeile(sym)
        coin, g, b = sym.removesuffix("USDT"), float(r["geld"]), float(r["brief"])
        m = (g + b) / 2
        kauf = self.fuellungen.get((self.zeit, coin, "kauf")) or (m * (1 + float(r["kauf_bp"]) / 1e4) if r["kauf_bp"] != "" else b)
        verk = self.fuellungen.get((self.zeit, coin, "verkauf")) or (m * (1 - float(r["verkauf_bp"]) / 1e4) if r["verkauf_bp"] != "" else g)
        return {"geld": [(g, 1e-12), (min(g, verk), GROSS)], "brief": [(b, 1e-12), (max(b, kauf), GROSS)]}


def stunden_laden(coins: list, von_ms: int, bis_ms: int, api: Yubit) -> dict:
    out = {}
    for coin in coins:
        k, t = {}, von_ms
        while t < bis_ms:
            e = min(t + 190 * H, bis_ms)
            for x in api.kerzen(coin + "USDT", 60, 200, t, e):
                k[x["start"]] = x["close"]
            t = e
        out[coin] = k
    return out


def laeufe(quelle: Path) -> list:
    """Aufzeichnungen der Quelle in Läufe zerlegen: [(zeit, {coin: zeile})], in der Reihenfolge der Datei."""
    out, zeit, akt = [], None, {}
    for r in bot.lesen(quelle / "spannen.csv"):
        if r["zeit"] != zeit or r["coin"] in akt:               # neuer Lauf (auch wenn zwei Läufe in dieselbe Minute fielen)
            if akt:
                out.append((zeit, akt))
            zeit, akt = r["zeit"], {}
        akt[r["coin"]] = r
    if akt:
        out.append((zeit, akt))
    return out


def nachrechnen(cfg: dict, quelle: Path, ziel: Path, fuellungen_der_quelle: bool, api=None, melden=print) -> dict:
    """Schreibt nach `ziel` denselben Dateisatz wie ein laufender Test. Gibt eine kurze Zusammenfassung zurück."""
    api = api or Yubit()
    ll = laeufe(quelle)
    if not ll:
        raise SystemExit("Die Quelle enthält keine Aufzeichnungen.")
    coins = cfg["coins"]
    stunden = stunden_laden(coins, ms(ll[0][0]) // H * H - (kern.RUECKBLICK_STUNDEN + 3) * H, ms(ll[-1][0]) + H, api)
    kontrakte = {c: api.kontrakt(c + "USDT") for c in coins}
    fuell = {(r["zeit"], r["coin"], r["seite"]): float(r["fuellkurs"]) for r in bot.lesen(quelle / "protokoll.csv")
             if r["zeit"] == ll[0][0]} if fuellungen_der_quelle else {}          # nur die Einstiege des ersten Laufs
    zeiten = [r["zeit"] for r in bot.lesen(quelle / "stand.csv")]
    if len(zeiten) != len(set(zeiten)):
        raise SystemExit("Die Quelle hat zwei Läufe in derselben Minute; der Funding-Anteil wäre so nicht eindeutig.")
    funding_q = {r["zeit"]: float(r["funding"]) for r in bot.lesen(quelle / "stand.csv")}
    menge_q = {}
    for r in bot.lesen(quelle / "protokoll.csv"):               # Positionen der Quelle im Zeitverlauf (für den Funding-Anteil)
        menge_q.setdefault(r["zeit"], []).append((r["coin"], float(r["menge"]) * (1 if r["seite"] == "kauf" else -1)))
    if ziel.exists():
        shutil.rmtree(ziel)
    ziel.mkdir(parents=True)
    boerse, pos_q, f_alt, still = Aufzeichnung(stunden, kontrakte, fuell), {}, 0.0, (lambda *_: None)
    for zeit, zeilen in ll:
        jetzt = boerse.setze(zeit, zeilen)
        mitte = {c: (float(r["geld"]) + float(r["brief"])) / 2 for c, r in zeilen.items()}
        f_neu = funding_q.get(zeit, f_alt)
        if f_neu != f_alt and (ziel / "zustand.json").exists():   # Funding der Quelle anteilig nach offenem Positionswert übernehmen
            z = json.loads((ziel / "zustand.json").read_text())
            wert_q = sum(abs(q) * mitte.get(c, 0.0) for c, q in pos_q.items())
            wert_z = sum(abs(q) * mitte.get(c, 0.0) for c, q in z["pos"].items())
            if wert_q > 0:
                z["funding"] += (f_neu - f_alt) * wert_z / wert_q
                bot.zustand_speichern(ziel, z)
        f_alt = f_neu
        bot.schritt(cfg, boerse, ziel, jetzt, melden=still)
        for c, d in menge_q.get(zeit, []):                      # Orders der Quelle in diesem Lauf: gelten für das Funding ab dem nächsten Lauf
            pos_q[c] = pos_q.get(c, 0.0) + d
    bot.bericht({**cfg, "nachgerechnet_bis": ll[-1][0]}, ziel)
    st, pr = bot.lesen(ziel / "stand.csv"), bot.lesen(ziel / "protokoll.csv")
    melden(f"nachgerechnet: {len(ll)} Läufe von {ll[0][0]} bis {ll[-1][0]} UTC, {len(pr)} Orders, netto mit Rebate {float(st[-1]['netto_mit_rebate']):+.2f} $")
    return {"laeufe": len(ll), "von": ll[0][0], "bis": ll[-1][0], "orders": len(pr), "netto_mit_rebate": float(st[-1]["netto_mit_rebate"])}


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Regel-Variante auf den Aufzeichnungen eines Tests nachrechnen")
    p.add_argument("--quelle", type=Path, required=True); p.add_argument("--config", type=Path, required=True); p.add_argument("--ziel", type=Path, required=True)
    p.add_argument("--fuellungen-der-quelle", action="store_true", help="die Orders des ersten Laufs der Quelle (gemeinsame Einstiege) zu deren tatsächlichem Füllkurs buchen")
    p.add_argument("--vermerk", action="store_true", help="das Ende des nachgerechneten Abschnitts in die Einstellung schreiben (nachgerechnet_bis)")
    a = p.parse_args(argv)
    cfg = bot.konfig(a.config)
    r = nachrechnen(cfg, a.quelle, a.ziel, a.fuellungen_der_quelle)
    if a.vermerk:
        roh = json.loads(a.config.read_text()); roh["nachgerechnet_bis"] = r["bis"]
        a.config.write_text(json.dumps(roh, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
