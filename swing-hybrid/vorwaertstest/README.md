# Vorwärtstest Yubit

Prüft den Kandidaten aus `reports/suche_bericht.md` (14-Tage-Trend, stündlich, 10 Coins, Hebel 0,2) an echten
Yubit-Kursen. Die wichtigste Frage: **Wie viel Slippage kostet eine Order bei Yubit wirklich?**
Keine Anlageberatung. Lies zuerst `YUBIT_REGELN.md`.

## Stufe 1: Papier (Standard, ohne Risiko)

- Keine Orders, kein Konto, kein Schlüssel. Der Bot liest nur öffentliche Yubit-Kurse.
- Jede Stunde: Signal je Coin, und jede fällige Order wird gegen das echte Orderbuch dieses Moments abgerechnet.
- Zusätzlich misst er jede Stunde für alle Coins, was eine Order in Standardgröße gekostet hätte.
  Das sind rund 240 Messungen am Tag, nach wenigen Tagen ist die Slippage belastbar.

Ergebnis: `daten/bericht.md` (für Menschen), `daten/spannen.csv`, `daten/protokoll.csv`, `daten/stand.csv`.

### Starten ohne eigenen Rechner (GitHub)

Die Datei `.github/workflows/vorwaertstest.yml` startet den Durchlauf jede Stunde bei GitHub.
Geplante Läufe funktionieren nur, wenn diese Datei im **Standard-Branch** des Repos liegt. Dafür muss dieser
Branch einmal in den Standard-Branch übernommen werden (Pull Request, dann „Merge“).
Danach: Repo auf GitHub öffnen, Branch `vorwaertstest-daten` wählen, `bericht.md` lesen.

### Starten auf einem eigenen Server

```bash
cd swing-hybrid
bash vorwaertstest/server/installieren.sh     # richtet den stündlichen Lauf ein (systemd)
python3 -m vorwaertstest.bot selbsttest       # Verbindung prüfen
python3 -m vorwaertstest.bot bericht          # Zwischenstand anzeigen
```

## Stufe 2: Live in Kleinstgröße (erst nach Freigabe durch Yubit)

Nur so lässt sich prüfen, ob Gebühr und Rebate wirklich wie zugesagt abgerechnet werden.

1. Bei Yubit einen API-Schlüssel anlegen: Handel ja, **Auszahlung nein**.
2. Beim Yubit-Kundendienst die IP-Adresse des Servers freischalten lassen und dabei bestätigen lassen, dass ein
   stündlich laufendes Programm erlaubt ist. Das geht nur mit fester IP, also auf einem Server, nicht bei GitHub.
3. Schlüssel in `/etc/vorwaertstest.env` eintragen (nie in den Chat, nie ins Repo).
4. `python3 -m vorwaertstest.bot selbsttest` zeigt Guthaben, Gebührensätze und Positionen. Es wird nichts geordert.
5. In `config.json` `"modus": "live"` setzen, Kapital klein wählen, in der env-Datei `YUBIT_LIVE=ja`.

Sicherungen im Live-Betrieb:
- Ohne `YUBIT_LIVE=ja` **und** `"modus": "live"` **und** Schlüssel wird nie geordert.
- Jede Order ist ein Limit mit Preisgrenze (höchstens 0,05 % durch den Markt) und gedeckelt (`max_order_usd`).
- Weicht die Position an der Börse vom Protokoll ab, handelt der Bot nicht und meldet es.
- Tagesverlust-Limit 3 %: alles schließen, bis zum nächsten Tag Pause.
- Notbremse: Datei `daten/STOPP` anlegen. Der Bot kann weder auszahlen noch umbuchen.

**Wichtig:** Der Live-Teil ist nach dem offiziellen Yubit-Paket gebaut und mit nachgestellter Börse getestet,
aber noch nie gegen ein echtes Konto gelaufen. Die Kursdaten-Seite ist gegen die echte Schnittstelle geprüft.
Deshalb zuerst der Selbsttest und dann mit wenigen Dollar anfangen. Mindestgrößen: BTC rund 66 $, ETH 19 $,
SOL und AVAX 8 $, die übrigen Coins unter 1 $.

## Einstellungen (`config.json`)

| Feld | Bedeutung |
|---|---|
| `modus` | `papier` oder `live` |
| `kapital_usd` | Rechengröße für die Positionsgrößen (fest, ohne Zinseszins) |
| `hebel` | Anteil des Kapitals im Markt, 0,2 = 20 % |
| `coins` | gehandelte Coins (als `<COIN>USDT` bei Yubit) |
| `tagesverlust_limit` | 0,03 = 3 % vom Kapital |
| `preisgrenze` | wie weit das Limit durch den Markt gehen darf (live) |
| `max_order_usd` | Sicherheitsdeckel je Order (live) |

Bei 5.000 $ und Hebel 0,2 sind es 100 $ je Coin. Liegt der Betrag unter der Mindestgröße eines Coins, wird dieser
Coin ausgelassen und im Lauf gemeldet.
