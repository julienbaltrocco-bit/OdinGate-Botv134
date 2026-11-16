"""SEC: Belegt ohne Entschluesselung, dass docs/stand*.enc.json denselben Inhalt traegt wie die im selben Commit
unverschluesselt eingecheckte Datei vorwaertstest/lauf*/dashboard.json: AES-256-CBC mit PKCS7 erzeugt genau
(len(klartext)//16 + 1) * 16 Byte Chiffrat. Es wird nichts entschluesselt und kein Passwort verwendet."""
import base64, json, subprocess, sys
REPO = sys.argv[1]
def show(commit, pfad):
    return subprocess.run(["git", "-C", REPO, "show", f"{commit}:{pfad}"], capture_output=True, check=True).stdout
paare = [("docs/stand.enc.json", "swing-hybrid/vorwaertstest/lauf/dashboard.json"),
         ("docs/stand_tpsl.enc.json", "swing-hybrid/vorwaertstest/lauf_tpsl/dashboard.json")]
commits = subprocess.run(["git", "-C", REPO, "log", "--format=%h", "--", "docs/stand.enc.json", "docs/stand_tpsl.enc.json"],
                         capture_output=True, text=True, check=True).stdout.split()
print("commit   chiffrat-datei              bytes(chiffrat)  bytes(klartext)  erwartet=(n//16+1)*16  gleich")
ok = n = 0
for c in commits:
    for enc, klar in paare:
        try:
            e = json.loads(show(c, enc)); k = show(c, klar)
        except subprocess.CalledProcessError:
            continue
        lc = len(base64.b64decode(e["d"])); erw = (len(k) // 16 + 1) * 16
        n += 1; ok += lc == erw
        print(f"{c}  {enc:26s}  {lc:15d}  {len(k):15d}  {erw:20d}  {lc == erw}")
print(f"\n{ok} von {n} Paaren: Chiffratlaenge passt exakt zur Klartextdatei im selben Commit.")
