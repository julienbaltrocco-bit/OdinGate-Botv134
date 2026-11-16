"""INF: Konsistenz zwischen protokoll.csv, stand.csv, zustand.json, dashboard.json (nur lesend, aus git HEAD gelesen).
Aufruf: python3 -I konsistenz.py <repo>
"""
import csv, io, json, subprocess, sys, datetime as dt
REPO = sys.argv[1]
def blob(pfad, commit="HEAD"):
    return subprocess.run(["git", "-C", REPO, "show", f"{commit}:{pfad}"], capture_output=True, text=True, check=True).stdout
print("gelesen aus Commit", subprocess.run(["git", "-C", REPO, "log", "-1", "--format=%h %cI"], capture_output=True, text=True).stdout.strip())
for name, ordner, cfgp in (("Test 1", "swing-hybrid/vorwaertstest/lauf", "swing-hybrid/vorwaertstest/config_lauf.json"),
                           ("Test 2", "swing-hybrid/vorwaertstest/lauf_tpsl", "swing-hybrid/vorwaertstest/config_lauf_tpsl.json")):
    print("\n==========", name)
    z = json.loads(blob(f"{ordner}/zustand.json")); cfg = json.loads(blob(cfgp))
    pr = list(csv.DictReader(io.StringIO(blob(f"{ordner}/protokoll.csv"))))
    st = list(csv.DictReader(io.StringIO(blob(f"{ordner}/stand.csv"))))
    d = json.loads(blob(f"{ordner}/dashboard.json"))
    pos, kasse = {}, {}
    for r in pr:
        q = float(r["menge"]) * (1 if r["seite"] == "kauf" else -1)
        pos[r["coin"]] = pos.get(r["coin"], 0.0) + q
        kasse[r["coin"]] = kasse.get(r["coin"], 0.0) - q * float(r["fuellkurs"])
    ok = lambda a, b, tol=1e-6: abs(a - b) <= tol
    print("  Orders: protokoll", len(pr), "| zustand.orders", z["orders"], "| stand.csv letzte Zeile", st[-1]["orders"], "->", "ok" if len(pr) == z["orders"] == int(st[-1]["orders"]) else "ABWEICHUNG")
    print("  Positionen aus Protokoll == zustand.pos:", all(ok(pos.get(c, 0), z["pos"].get(c, 0), 1e-9) for c in cfg["coins"]))
    print("  Kasse aus Protokoll == zustand.kasse:", all(ok(kasse.get(c, 0), z["kasse"].get(c, 0), 1e-6) for c in cfg["coins"]),
          "max. Abweichung %.2e" % max(abs(kasse.get(c, 0) - z["kasse"].get(c, 0)) for c in cfg["coins"]))
    g, rb = sum(float(r["gebuehr"]) for r in pr), sum(float(r["rebate"]) for r in pr)
    print(f"  Gebuehr Protokoll {g:.6f} vs. Zustand {z['gebuehr']:.6f}; Rebate {rb:.6f} vs. {z['rebate']:.6f}")
    brutto = sum(z["kasse"].get(c, 0) + z["pos"].get(c, 0) * z["kurs"].get(c, 0) for c in set(z["kasse"]) | set(z["pos"]))
    ohne = brutto - z["gebuehr"] + z["funding"]
    l = st[-1]
    print(f"  Vermoegen aus zustand.json: brutto {brutto:.4f}, netto_mit_rebate {ohne + z['rebate']:.4f} | stand.csv letzte Zeile: brutto {l['brutto']}, netto_mit_rebate {l['netto_mit_rebate']} ->",
          "ok" if ok(brutto, float(l["brutto"]), 1e-3) and ok(ohne + z["rebate"], float(l["netto_mit_rebate"]), 1e-3) else "ABWEICHUNG")
    print("  letzter Lauf stand.csv:", l["zeit"], "| funding_zeit:", sorted({dt.datetime.fromtimestamp(v / 1000, dt.timezone.utc).strftime('%F %T') for v in z["funding_zeit"].values()}),
          "| letzte_kerze:", dt.datetime.fromtimestamp(z["letzte_kerze"] / 1000, dt.timezone.utc).strftime('%F %T'))
    print("  dashboard.json: letzter_lauf", d["kennzahlen"][0]["letzter_lauf"], "| geschrieben", d["geschrieben"], "| laeufe", d["kennzahlen"][0]["laeufe"], "(stand.csv:", len(st), ") | takt_minuten", d["takt_minuten"])
    print("  Zeitformat: stand.csv 'zeit' ohne Zeitzonenangabe:", repr(l["zeit"]), "| dashboard verlauf:", d["verlauf"][-1]["zeit"])
    # Felder im Zustand, die fuer einen Wiederanlauf fehlen wuerden
    print("  Schluessel im Zustand:", sorted(z.keys()))
    print("  Einstiegskurs nur im Zustand (einstieg)?", "einstieg" in z, "| tag_start", z["tag_start"], "| tagesverlust_limit cfg", cfg["tagesverlust_limit"])
    # Sprung-/Rueckwaertszeit in stand.csv
    zt = [r["zeit"] for r in st]
    print("  stand.csv Zeit streng aufsteigend:", all(a < b for a, b in zip(zt, zt[1:])))
    # Spaltenzahl
    for datei in ("stand.csv", "protokoll.csv", "spannen.csv"):
        zeilen = blob(f"{ordner}/{datei}").splitlines()
        n = {len(next(csv.reader([x]))) for x in zeilen}
        print(f"  {datei}: {len(zeilen) - 1} Datenzeilen, Spaltenzahlen {n}, {len(blob(f'{ordner}/{datei}'))} Bytes, CRLF: {chr(13) in blob(f'{ordner}/{datei}')}")
