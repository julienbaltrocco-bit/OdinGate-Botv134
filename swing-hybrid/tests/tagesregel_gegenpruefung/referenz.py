"""Unabhängige Referenz für Test 4 (Tagesregel) und Test 1 (Stundenregel).

Geschrieben nur aus dem Wortlaut von forschung/protokoll.md, Abschnitt 53 samt „Präzisierungen zu Abschnitt 53“,
und aus der Schnittstellenbeschreibung des Prüfauftrags. Reines Python, kein Import aus dem Bot.

Eingabe ist eine Tabelle von Stundenschlusskursen je Coin (`Kerzen`) und eine Liste von Laufzeiten (UTC-Millisekunden).
Ausgabe ist je Lauf die Richtung (+1 Long, 0 keine Position, −1 Short), die der Test nach diesem Lauf je Coin hält.

Nach der Gegenprüfung ergänzt (Präzisierung 5 zu Abschnitt 53, vor dem Start festgelegt): Die Tagesrichtung wird frühestens
eine Minute nach dem Tageswechsel übernommen (`KARENZ`). Diese eine Bedingung hat der Autor des Bots in die Referenz des Prüfers
eingefügt; alles andere ist unverändert vom Prüfer.

Lesarten, die der Wortlaut offen lässt, sind Schalter (siehe `tagesregel`):
  markt_noetig   True  = wie in der Schnittstellenbeschreibung: Der Bot handelt für einen Coin nur, wenn es in diesem
                         Lauf Marktdaten gibt (letzte abgeschlossene Stundenkerze höchstens zwei Stunden alt und die
                         Kerze 336 Stunden davor vorhanden); gibt es für keinen Coin Marktdaten, entfällt der Lauf.
                 False = streng nach Abschnitt 53: Es zählen allein die beiden Kerzen des Tageswechsels.
"""

H = 3_600_000
TAG = 24 * H
RUECKBLICK = 336 * H           # 14 Tage in Stunden
KARENZ = 60_000                # frühestens eine Minute nach dem Tageswechsel wird übernommen (Präzisierung 5)


def vorzeichen(schluss, schluss_frueher):
    """+1, wenn der Schluss über dem Schluss 336 Stunden davor liegt, −1 darunter, 0 bei Gleichstand."""
    return (schluss > schluss_frueher) - (schluss < schluss_frueher)


class Kerzen:
    """Stundenschlusskurse je Coin und wann die Börse sie liefert.

    schluss[coin][start_ms]  Schlusskurs der Stundenkerze, die bei start_ms beginnt (sie schließt bei start_ms + H).
    fehlt[coin][start_ms]    Liste von Zeitspannen (von_ms, bis_ms), in denen die Börse diese Kerze NICHT liefert
                             (von einschließlich, bis ausschließlich). Ohne Eintrag liefert die Börse sie immer.
    """

    def __init__(self, schluss, fehlt=None):
        self.schluss = schluss
        self.fehlt = fehlt or {}

    def vorhanden(self, coin, start, t):
        """Steht die Kerze zur Zeit t bei der Börse (laufend oder abgeschlossen)?"""
        if start > t or start not in self.schluss.get(coin, {}):
            return False
        return not any(von <= t < bis for von, bis in self.fehlt.get(coin, {}).get(start, ()))

    def geliefert(self, coin, start, t):
        """Schlusskurs der ABGESCHLOSSENEN Kerze, wenn die Börse sie zur Zeit t liefert, sonst None."""
        if start + H > t or not self.vorhanden(coin, start, t):
            return None
        return self.schluss[coin][start]


def marktdaten(kerzen, coin, t):
    """Marktdaten eines Coins im Lauf zur Zeit t: (Start, Schluss, Schluss 336 Stunden davor) der letzten gelieferten
    abgeschlossenen Stundenkerze, wenn sie höchstens zwei Stunden alt ist und die Kerze 336 Stunden davor geliefert
    wird. Sonst None (für diesen Coin wird in diesem Lauf nicht gehandelt)."""
    s = t - t % H - H                                   # jüngste Kerze, die zur Zeit t abgeschlossen sein kann
    while t - (s + H) <= 2 * H:
        a = kerzen.geliefert(coin, s, t)
        if a is not None:
            b = kerzen.geliefert(coin, s - RUECKBLICK, t)
            return None if b is None else (s, a, b)
        s -= H
    return None


def stundenregel(kerzen, coins, laeufe):
    """Test 1: In jedem Lauf gilt die Richtung der letzten abgeschlossenen Stundenkerze gegen die 336 Stunden davor."""
    richtung = {c: 0 for c in coins}
    verlauf = []
    for t in laeufe:
        ereignis = {}
        for c in coins:
            m = marktdaten(kerzen, c, t)
            if m is None:
                ereignis[c] = "keine Marktdaten"
                continue
            richtung[c] = vorzeichen(m[1], m[2])
            ereignis[c] = "Stundenkerze"
        verlauf.append({"zeit": t, "richtung": dict(richtung), "ereignis": ereignis, "entfaellt": all(
            e == "keine Marktdaten" for e in ereignis.values())})
    return verlauf


def tagesrichtung(kerzen, coin, t):
    """Richtung des laufenden Tages, wie sie ein Lauf zur Zeit t bekommt: Stundenkerze, die um 00:00 UTC dieses Tages
    schließt (Beginn 23:00 UTC des Vortags), gegen die Kerze 336 Stunden davor. None, solange eine der beiden fehlt.
    Gibt (Tag, Richtung, Schluss, Schluss alt)."""
    tag = t - t % TAG                                   # 00:00 UTC des laufenden Tages
    a = kerzen.geliefert(coin, tag - H, t)
    b = kerzen.geliefert(coin, tag - H - RUECKBLICK, t)
    if a is None or b is None:
        return None
    return tag, vorzeichen(a, b), a, b


def tagesregel(kerzen, coins, laeufe, markt_noetig=True, markt_fn=None):
    """Test 4: Die Richtung wird je Coin nur einmal am Tag übernommen.

    markt_fn(coin, t) -> bool ersetzt, wenn angegeben, die Marktdaten-Bedingung (für die Nachrechnung aus Aufzeichnungen,
    wo zusätzlich zählt, ob die Quelle in diesem Lauf eine Aufzeichnung für den Coin hat).

    - Maßgeblich ist die Stundenkerze, die um 00:00 UTC schließt. Übernommen wird im ersten Lauf des Tages, der beide
      Kerzen bekommt (planmäßig 00:04 UTC, sonst der nächste: Aufholen mit der Richtung der 00:00-Kerze DIESES Tages).
    - Bis zur nächsten Übernahme bleibt die Position stehen. Solange für den laufenden Tag keine Richtung vorliegt,
      wird für diesen Coin nicht gehandelt (die Position vom Vortag bleibt also stehen).
    - Gleichstand: keine Position.
    """
    richtung = {c: 0 for c in coins}
    uebernommen = {c: None for c in coins}              # Tag (00:00 UTC), dessen Richtung zuletzt übernommen wurde
    verlauf = []
    for t in laeufe:
        tag = t - t % TAG
        markt = {c: (markt_fn(c, t) if markt_fn else marktdaten(kerzen, c, t) is not None) for c in coins}
        entfaellt = markt_noetig and not any(markt.values())
        ereignis, beleg = {}, {}
        for c in coins:
            if uebernommen[c] == tag:
                ereignis[c] = "steht"                   # heute schon übernommen: egal, was das Stundensignal zeigt
                continue
            if markt_noetig and not markt[c]:
                ereignis[c] = "keine Marktdaten"
                continue
            if t - tag < KARENZ:
                ereignis[c] = "erste Minute"            # Präzisierung 5: in der ersten Minute des Tages wird noch nicht übernommen
                continue
            r = tagesrichtung(kerzen, c, t)
            if r is None:
                ereignis[c] = "Tageskerze fehlt"        # keine Richtung für den laufenden Tag: nicht handeln
                continue
            uebernommen[c], richtung[c] = tag, r[1]
            beleg[c] = r
            ereignis[c] = "uebernommen"
        verlauf.append({"zeit": t, "richtung": dict(richtung), "ereignis": ereignis, "beleg": beleg,
                        "entfaellt": entfaellt, "uebernommen": dict(uebernommen)})
    return verlauf


def orders_erwartet(vorher, nachher):
    """Zahl der Orders für einen Richtungswechsel: Umkehr schließt und dreht (2), Öffnen oder Schließen je 1."""
    if vorher == nachher:
        return 0
    return (1 if vorher != 0 else 0) + (1 if nachher != 0 else 0)
