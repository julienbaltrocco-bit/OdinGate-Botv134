"""SEC: Nachbau des Schluesselformats von docs/schluessel.json mit EIGENEM Wegwerf-Schluessel und ERFUNDENEM Passwort.

Zeigt zwei Eigenschaften des Verfahrens (PBKDF2-SHA256 -> 48 Byte = AES-Schluessel + IV, AES-256-CBC ueber PKCS8):
 1. Zum Pruefen eines Passwortkandidaten genuegt der ERSTE PBKDF2-Block (32 Byte). Der IV (zweiter Block) ist unnoetig,
    weil sich ab dem zweiten AES-Block jeder Klartextblock aus Schluessel und vorigem Chiffratblock ergibt.
 2. Der Klartext ist weitgehend bekannt: Der PKCS8-Kopf ist fest, und der Modulus steht im oeffentlichen Schluessel.
    Ein Angreifer hat damit eine sichere Offline-Pruefung je Kandidat (eine AES-Blockentschluesselung).

Die echte Datei docs/schluessel.json wird NICHT gelesen. Es wird kein echtes Passwort geraten.
Aufruf: python3 -I kdf_nachbau.py     (braucht nur das Programm openssl)
"""
import hashlib
import os
import subprocess
import tempfile

RUNDEN = 600_000


def ossl(*args, eingabe=None):
    return subprocess.run(["openssl", *args], input=eingabe, capture_output=True, check=True).stdout


with tempfile.TemporaryDirectory() as d:
    priv, pub = os.path.join(d, "wegwerf_priv.pem"), os.path.join(d, "wegwerf_pub.der")
    ossl("genpkey", "-algorithm", "RSA", "-pkeyopt", "rsa_keygen_bits:2048", "-out", priv)
    pkcs8 = ossl("pkcs8", "-topk8", "-nocrypt", "-in", priv, "-outform", "DER")
    ossl("pkey", "-in", priv, "-pubout", "-outform", "DER", "-out", pub)
    pub_der = open(pub, "rb").read()

salz = os.urandom(16)
bits = hashlib.pbkdf2_hmac("sha256", b"erfundenes-passwort", salz, RUNDEN, 48)          # so leitet das Board ab
key, iv = bits[:32], bits[32:48]
chiffrat = ossl("enc", "-aes-256-cbc", "-K", key.hex(), "-iv", iv.hex(), eingabe=pkcs8)
print(f"PKCS8 (RSA-2048): {len(pkcs8)} Byte -> Chiffrat {len(chiffrat)} Byte "
      f"(docs/schluessel.json traegt 1232 Byte; passt zu diesem Format: {len(chiffrat) == 1232})")

# Sicht des Angreifers: kennt Salz, Runden, Chiffrat, oeffentlichen Schluessel. Leitet je Kandidat NUR 32 Byte ab.
kandidat = hashlib.pbkdf2_hmac("sha256", b"erfundenes-passwort", salz, RUNDEN, 32)
print("1. Erster PBKDF2-Block allein ergibt den AES-Schluessel:", kandidat == key)
block = lambda i: chiffrat[16 * i:16 * i + 16]
# Bloecke 2..5 ohne Kenntnis des IV entschluesseln: als "IV" dient der vorige Chiffratblock
klar = ossl("enc", "-d", "-aes-256-cbc", "-nopad", "-K", kandidat.hex(), "-iv", block(0).hex(), eingabe=chiffrat[16:80])
print("   Bloecke 2 bis 5 ohne IV entschluesselt, identisch mit dem echten Klartext:", klar == pkcs8[16:80])
print("   Block 2 (hex):", klar[:16].hex(), "= fester PKCS8-Kopf (rsaEncryption, OCTET STRING, RSAPrivateKey, Version 0)")
modulus_im_pub = pub_der[33:33 + 256]
print("2. Entschluesselte Bytes enthalten den oeffentlich bekannten Modulus:", modulus_im_pub[:32] in klar + b"" or modulus_im_pub[:16] in klar)
falsch = hashlib.pbkdf2_hmac("sha256", b"falscher-kandidat", salz, RUNDEN, 32)
klar_f = ossl("enc", "-d", "-aes-256-cbc", "-nopad", "-K", falsch.hex(), "-iv", block(0).hex(), eingabe=chiffrat[16:32])
print("   Falscher Kandidat ergibt den festen Kopf:", klar_f == pkcs8[16:32], "(Pruefung ist eindeutig)")
print("Folge: Aufwand je Versuch = 600.000 PBKDF2-Runden (ein Block); der rechtmaessige Nutzer zahlt 1.200.000 (zwei Bloecke).")
