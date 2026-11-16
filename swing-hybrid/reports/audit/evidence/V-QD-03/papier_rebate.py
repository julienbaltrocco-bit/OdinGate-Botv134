"""V-QD-03: Papier-Modus schreibt das Rebate sofort gut (85 % der Gebuehr). Laeuft nur in einem temporaeren Ordner
mit nachgestellter Boerse (Klasse aus tests/test_vorwaertstest_bot.py); beruehrt weder lauf/ noch lauf_tpsl/ noch docs/."""
import sys, json, tempfile, inspect
from pathlib import Path
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid")
sys.path.insert(0, "/home/user/OdinGate-Botv134/swing-hybrid/tests")
import test_vorwaertstest_bot as T
from vorwaertstest import bot, kern

with tempfile.TemporaryDirectory(dir=str(Path(__file__).parent)) as tmp:
    d = Path(tmp) / "daten"
    api = T.Boerse({"AAA": 100.0, "BBB": 50.0}, {"AAA": 90.0, "BBB": 60.0})
    cfg = {**T.CFG, "hebel": 3.0, "tagesverlust_limit": 1.0, "max_order_usd": 1e9}
    r1 = bot.schritt(cfg, api, d, T.JETZT, melden=lambda *_: None)
    api.kurse["AAA"] = 80.0                       # AAA dreht
    r2 = bot.schritt(cfg, api, d, T.JETZT + 2 * T.H, melden=lambda *_: None)
    z = json.loads((d / "zustand.json").read_text())
    v = r2["vermoegen"]
    pr = bot.lesen(d / "protokoll.csv")
    print("Modus:", r2["modus"], "| Orders im Protokoll:", len(pr))
    print("Gebuehr gesamt:", round(z["gebuehr"], 6), "| Rebate gesamt:", round(z["rebate"], 6), "| Verhaeltnis:", round(z["rebate"] / z["gebuehr"], 6))
    print("je Order Rebate/Gebuehr:", sorted({round(float(p["rebate"]) / float(p["gebuehr"]), 4) for p in pr}))
    print("netto_mit_rebate - netto_ohne_rebate:", round(v["netto_mit_rebate"] - v["netto_ohne_rebate"], 6), "(= Rebate, sofort im Stand)")
    assert abs(z["rebate"] - 0.85 * z["gebuehr"]) < 1e-9
    assert abs(v["netto_mit_rebate"] - v["netto_ohne_rebate"] - z["rebate"]) < 1e-9
src = inspect.getsource(bot.schritt)
i = src.index("if live:\n                    kurs, q, gebuehr = live_order")
print("\nLive-Zweig im Quelltext von bot.schritt (nur gelesen, nicht ausgefuehrt):")
print(src[i:i + 230])
print("Stellen in yubit.py mit 'rebate':", sum("rebate" in l.lower() for l in open("/home/user/OdinGate-Botv134/swing-hybrid/vorwaertstest/yubit.py")))
