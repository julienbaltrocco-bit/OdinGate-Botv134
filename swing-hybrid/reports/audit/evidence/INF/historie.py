"""INF: Takt, Luecken und Append-only-Eigenschaft der Lauf-Dateien laut git-Historie (nur lesend).
Aufruf: python3 -I historie.py <repo>
"""
import csv, io, json, subprocess, sys, datetime as dt, collections, statistics
REPO = sys.argv[1]
def git(*a):
    return subprocess.run(["git", "-C", REPO, *a], capture_output=True, text=True, check=True).stdout
def blob(commit, pfad):
    r = subprocess.run(["git", "-C", REPO, "show", f"{commit}:{pfad}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None
HEAD = git("rev-parse", "--short", "HEAD").strip()
print("Stand der lokalen Historie: HEAD", HEAD, git("log", "-1", "--format=%cI").strip())
for name, ordner in (("Test 1", "swing-hybrid/vorwaertstest/lauf"), ("Test 2", "swing-hybrid/vorwaertstest/lauf_tpsl")):
    print("\n==========", name, ordner)
    commits = [z.split("|", 2) for z in git("log", "--reverse", "--format=%h|%cI|%s", "--", ordner).splitlines()]
    print("Commits mit Aenderung im Ordner:", len(commits))
    # --- Append-only-Pruefung
    for datei in ("stand.csv", "protokoll.csv", "spannen.csv"):
        vor, verstoesse, n = None, [], 0
        for h, t, s in commits:
            b = blob(h, f"{ordner}/{datei}")
            if b is None:
                continue
            n += 1
            if vor is not None and not b.startswith(vor):
                verstoesse.append((h, t, s[:60]))
            vor = b
        print(f"  {datei}: {n} Versionen, nicht-anhaengende Aenderungen: {len(verstoesse)}", verstoesse[:5])
    # --- Zeitreihe der Laeufe laut stand.csv (HEAD)
    st = list(csv.DictReader(io.StringIO(blob("HEAD", f"{ordner}/stand.csv"))))
    zt = [dt.datetime.fromisoformat(r["zeit"]) for r in st]
    d = [(b - a).total_seconds() / 60 for a, b in zip(zt, zt[1:])]
    print(f"  stand.csv: {len(st)} Laeufe von {st[0]['zeit']} bis {st[-1]['zeit']} UTC")
    print(f"  Abstand zwischen Laeufen (Minuten): min {min(d):.0f}, Median {statistics.median(d):.0f}, Mittel {statistics.fmean(d):.1f}, max {max(d):.0f}")
    print("  Verteilung der Abstaende:", dict(sorted(collections.Counter(int(x) for x in d).items())))
    print("  Abstaende > 7 Minuten:", [(st[i]['zeit'], st[i+1]['zeit'], int(x)) for i, x in enumerate(d) if x > 7])
    dup = [k for k, v in collections.Counter(r["zeit"] for r in st).items() if v > 1]
    print("  doppelte Zeitstempel in stand.csv:", dup)
    # --- erster Lauf nach jeder vollen Stunde
    erste = {}
    for z in zt:
        erste.setdefault(z.replace(minute=0), z)
    print("  erster Lauf je Stunde (Minute nach voller Stunde):", {k.strftime('%H'): v.minute for k, v in erste.items()})
    # --- Laufzeit: Zeitstempel im Lauf gegen Commit-Zeit
    cz = {}
    for h, t, s in commits:
        b = blob(h, f"{ordner}/stand.csv")
        if b:
            letzte = b.strip().splitlines()[-1].split(",")[0]
            cz.setdefault(letzte, t)
    diff = []
    for z, t in cz.items():
        try:
            a = dt.datetime.fromisoformat(z).replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
        diff.append((dt.datetime.fromisoformat(t) - a).total_seconds())
    print(f"  Sekunden zwischen Lauf-Zeitstempel (Minute abgeschnitten) und Commit: min {min(diff):.0f}, Median {statistics.median(diff):.0f}, max {max(diff):.0f}")
    print("  Laeufe ohne eigenen Commit (Zeile in stand.csv, aber kein Commit mit dieser letzten Zeile):", [r['zeit'] for r in st if r['zeit'] not in cz])
    # --- Commit-Meldungen ausserhalb des Musters
    ab = [(h, t, s[:90]) for h, t, s in commits if not s.startswith("Vorwärtstest (Papier") or "fehlgeschlagen" in s]
    print("  Commits ausserhalb des stunde.sh-Musters:", len(ab))
    for x in ab: print("    ", x)
    # --- spannen.csv: Zeilen je Lauf
    sp = list(csv.DictReader(io.StringIO(blob("HEAD", f"{ordner}/spannen.csv"))))
    je = collections.Counter(r["zeit"] for r in sp)
    print("  spannen.csv:", len(sp), "Zeilen; Laeufe mit weniger als 10 Coins:", {k: v for k, v in je.items() if v != 10})
    fehl = set(r["zeit"] for r in st) - set(je)
    print("  Laeufe in stand.csv ohne Zeile in spannen.csv:", sorted(fehl))
    leer = [(r["zeit"], r["coin"]) for r in sp if r["kauf_bp"] == "" or r["verkauf_bp"] == ""]
    print("  Messungen ohne volle Fuellung (kauf_bp/verkauf_bp leer):", leer)
    for zeitp in [k for k, v in je.items() if v != 10]:
        print("   ", zeitp, "vorhanden:", [r["coin"] for r in sp if r["zeit"] == zeitp])
