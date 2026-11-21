"""Zufallsvergleich als Test: Bot-Schritt gegen die unabhängige Referenz (referenz.py), Tagesregel (Test 4) und
Stundenregel (Test 1), mit festem Startwert. Referenz und Vergleich stammen aus der Gegenprüfung vom 21.11.2026
(unabhängiger Nachbau aus dem Wortlaut der Festlegung, Forschungszweig, forschung/protokoll.md Abschnitt 53).

    python -m pytest tests/tagesregel_gegenpruefung -q                    (40 Szenarien; SZENARIEN=300 für den vollen Lauf,
                                                                           rund zwei Minuten; BOT_PFAD=... für eine andere Bot-Kopie)
"""
import os
import sys
from pathlib import Path

HIER = Path(__file__).resolve().parent
sys.path.insert(0, str(HIER))
import vergleich as vg                                                      # noqa: E402

BOT_PFAD = Path(os.environ.get("BOT_PFAD", HIER.parents[1]))                # der Bot dieses Repositorys (swing-hybrid)
SZENARIEN = int(os.environ.get("SZENARIEN", "40"))                          # voller Lauf der Gegenprüfung: SZENARIEN=300


def _kurz(r):
    return [(e["nr"], e["abweichungen"][:2]) for e in r["fehler"][:3]]


def test_tagesregel_haelt_nach_jedem_lauf_die_richtung_der_festlegung():
    r = vg.lauf(BOT_PFAD, SZENARIEN, vg.STARTWERT, "tag")
    assert r["szenarien_mit_abweichung"] == 0, _kurz(r)
    i = r["inhalt"]                                                         # die schwierigen Fälle kommen wirklich vor
    for schluessel in ("uebernahme_planmaessig", "uebernahme_aufgeholt", "uebernahme_aufgeholt_nach_01uhr", "uebernahme_gleichstand",
                       "uebernahme_dreht", "laeufe_0000", "laeufe_235959999", "lauf_coin_tageskerze_fehlt", "lauf_coin_keine_marktdaten",
                       "lauf_coin_tag_ungleich_stunde", "coin_tage_ohne_uebernahme", "lauf_coin_erste_minute"):
        assert i.get(schluessel, 0) > 0, schluessel
    if SZENARIEN >= 100:
        assert i.get("tage_ohne_lauf", 0) > 0


def test_stundenregel_ohne_schalter_wie_bisher_und_ohne_neues_feld():
    r = vg.lauf(BOT_PFAD, SZENARIEN, vg.STARTWERT, "stunde")
    assert r["szenarien_mit_abweichung"] == 0, _kurz(r)
    assert r["summe"]["orders"] > 10 * r["szenarien"]                       # die Stundenregel handelt hier sehr oft
