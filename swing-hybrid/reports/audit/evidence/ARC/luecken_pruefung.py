"""ARC: Stichproben fuer Rechenwege, die kein bestehender Test abdeckt (Funding und Tageslimit in engine2,
Gebuehren/Rebate in runner.Lauf, Zeitversatz in research.auf_raster, Funding-Buchung im Bot).
Synthetische Daten, keine Dateien im Repo. Aufruf aus swing-hybrid: .venv/bin/python -I -B <skript>
"""
import json, sys, tempfile
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0, "src"); sys.path.insert(0, ".")
import numpy as np, pandas as pd
from hybrid import engine2, research as R, runner
from vorwaertstest import bot, kern

def ok(name, bedingung, detail=""):
    print(f"  [{'OK' if bedingung else 'ABWEICHUNG'}] {name} {detail}")

print("1) engine2: Funding (Vorzeichen, Betrag, Zeitpunkt)")
T = 6
c = np.full((1, T), 100.0); o = c.copy(); h = c.copy(); l = c.copy()
w = np.array([[0, 1, 1, 1, 1, 1]], dtype=float)
fund = np.zeros((1, T)); fund[0, 1] = 0.001; fund[0, 3] = 0.001          # Kerze 1: Einstiegskerze, Kerze 3: Position gehalten
r = engine2.simulate_target(o, h, l, c, w, np.ones((1, T)), fund, np.zeros(T, np.int64), 1.0, 3, 1e-4, np.array([0.0]), 0.0, 0, 0.0,
                            0.0004, 0.0008, 9.0, 100, True)
FU = r[3]
ok("Long zahlt bei positiver Rate, Betrag = Nominal x Rate", abs(FU[3] - (-0.001)) < 1e-12, f"FU[3]={FU[3]:.6f}")
ok("Funding in der Einstiegskerze wird nicht berechnet (Position entsteht erst nach dem Funding-Schritt)", FU[1] == 0.0, f"FU[1]={FU[1]:.6f}")

print("2) engine2: Tagesverlust-Limit (schliesst alles, sperrt bis zum naechsten Tag, danach Wiedereinstieg)")
T = 12
kurs = np.array([100, 100, 100, 95, 95, 95, 95, 95, 95, 95, 95, 95], dtype=float)
c = kurs[None, :]; o = np.concatenate([c[:, :1], c[:, :-1]], axis=1); h = np.maximum(o, c); l = np.minimum(o, c)
day = np.array([0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1], dtype=np.int64)
w = np.ones((1, T)); w[0, 0] = 0
r = engine2.simulate_target(o, h, l, c, w, np.ones((1, T)), np.zeros((1, T)), day, 1.0, 3, 1e-4, np.array([0.0]), 0.0, 0, 0.0,
                            0.0004, 0.0008, 0.03, 100, True)
eq, st, daily = r[0], r[6], r[4]
ok("eine Sperre ausgeloest", st[4] == 1, f"Sperrtage={st[4]:.0f}")
ok("Verlust am Sperrtag realisiert (-5 % zum Open der Folgekerze)", abs(daily[0, 0, 0] - (-0.05)) < 1e-9, f"Tag0 brutto={daily[0,0,0]:.4f}")
ok("am Folgetag Wiedereinstieg (Orders: Einstieg, Sperre, Einstieg, Schluss = 4)", st[0] == 4, f"Orders={st[0]:.0f}")

print("3) runner.Lauf: Gebuehr, Rebate, Tagesreihe")
T = 288 * 2
idx = pd.date_range("2024-01-01", periods=T, freq="5min")
rng = np.random.default_rng(1)
c = (100 * np.exp(np.cumsum(rng.normal(0, 0.002, T))))[None, :]
o = np.concatenate([c[:, :1], c[:, :-1]], axis=1)
m = SimpleNamespace(index=idx, coins=["X"], o=o, h=np.maximum(o, c), l=np.minimum(o, c), c=c, atr=np.ones((1, T)), fund=np.zeros((1, T)),
                    day=np.asarray((idx.normalize() - idx.normalize()[0]).days, dtype=np.int64), days=pd.DatetimeIndex(idx.normalize().unique()))
w = np.sign(np.sin(np.arange(T) / 40.0))[None, :]
L = R.lauf(m, np.ascontiguousarray(w), taker=True, slip=0.0, day_limit=9.0)
tv = L.TV[-1]
ok("netto ohne Rebate = brutto - 0,08 % x Taker-Volumen", abs(L.equity(runner.OHNE)[-1] - (L.eq_gross[-1] - 0.0008 * tv)) < 1e-12)
ok("netto mit Rebate = brutto - 0,012 % x Taker-Volumen", abs(L.equity(runner.MIT)[-1] - (L.eq_gross[-1] - 0.0008 * 0.15 * tv)) < 1e-12)
ok("Summe der Tagesgewinne = Endstand des Kontoverlaufs", abs(L.daily_pnl(runner.MIT).to_numpy().sum() - L.equity(runner.MIT)[-1]) < 1e-9)
s = R.sicht(L)
ok("sicht(): N = G - F + R (ohne Funding)", abs(s["N"] - (s["G"] - s["F"] + s["R"])) < 1e-9, f"G={s['G']:.5f} F={s['F']:.5f} R={s['R']:.5f} N={s['N']:.5f}")

print("4) research.tsmom + auf_raster: Signal der Stunde H gilt erst ab H+1:00, spaetere Kurse aendern nichts Frueheres")
stunden = 800
hidx = pd.date_range("2024-01-01", periods=stunden, freq="1h")
def markt(aendern_ab=None):
    rng = np.random.default_rng(7)
    k = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, stunden)))
    if aendern_ab is not None: k[aendern_ab:] *= 1.5
    grid = pd.date_range(hidx[0], periods=stunden * 12, freq="5min")
    return SimpleNamespace(coins=["X"], h1={"X": pd.DataFrame({"close": k}, index=hidx)}, index=grid)
a, b = markt(), markt(aendern_ab=600)
wa, wb = R.auf_raster(a, R.tsmom(a, 336)), R.auf_raster(b, R.tsmom(b, 336))
grenze = (600 + 1) * 12                       # Kerze 600 schliesst um 601:00; ihr Signal darf erst ab dort wirken
ok("identisch bis zum Schluss der geaenderten Stunde", np.array_equal(wa[:, :grenze], wb[:, :grenze]))
ok("Unterschied erst ab H+1:00 moeglich", not np.array_equal(wa[:, grenze:], wb[:, grenze:]))
sig = R.tsmom(a, 336)
H = 400
ok("Rasterwert um H+1:00 = Signal der Stunde H; um H+0:55 noch das der Stunde H-1",
   wa[0, (H + 1) * 12] == sig["X"].iloc[H] and wa[0, (H + 1) * 12 - 1] == sig["X"].iloc[H - 1])

print("5) Bot: Funding-Buchung (bot.py:185-189) ueber einen 8-Stunden-Termin")
Hms = kern.STUNDE_MS
JETZT = 1_800_000_000_000 - (1_800_000_000_000 % Hms) + 5 * 60_000        # 08:05 UTC
class Boerse:
    key = secret = ""; aufrufe = 0
    def kerzen(self, sym, minuten=60, limit=3, start_ms=None, ende_ms=None):
        if start_ms is not None: return [{"start": start_ms, "close": 90.0}]
        letzte = self.jetzt - self.jetzt % Hms - Hms
        return [{"start": letzte, "close": 100.0}]
    def kontrakt(self, sym): return {"status": "Trading", "min_menge": 0.1, "schritt": 0.1, "tick": 0.01, "funding_minuten": 480}
    def ticker(self, sym): return {"mark": 100.0, "funding": 0.0001}
    def buch(self, sym, tiefe=25): return {"geld": [(100.0, 1e9)], "brief": [(100.0, 1e9)]}
cfg = {"modus": "papier", "kapital_usd": 5000, "hebel": 1.0, "coins": ["AAA"], "tagesverlust_limit": 1.0, "preisgrenze": 0.0005, "max_order_usd": 9e9}
with tempfile.TemporaryDirectory() as d:
    d = Path(d); api = Boerse()
    for dt_h in (0, 1, 7, 8, 9):                # 08:05, 09:05, 15:05, 16:05 (Termin 16:00 liegt dazwischen), 17:05
        api.jetzt = JETZT + dt_h * Hms
        bot.schritt(cfg, api, d, api.jetzt, melden=lambda *_: None)
        z = json.loads((d / "zustand.json").read_text())
        print(f"     +{dt_h} h: Position {z['pos']['AAA']:.1f}, Funding kumuliert {z['funding']:+.4f} $")
    ok("Long 50 Stueck x 100 $ x 0,01 % = -0,50 $, genau einmal gebucht", abs(z["funding"] - (-0.5)) < 1e-9)
