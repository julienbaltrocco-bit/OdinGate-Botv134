"""V-ENG-01: ADA-Short 24.02. bis 02.03.2025 (im Befund genannt) in 5-Minuten-Aufloesung: Kursverhaeltnis zum Einstieg
zum Zeitpunkt, zu dem der Bot die Schliess-Order tatsaechlich stellt (einige Minuten nach der vollen Stunde)."""
import sys
sys.path.insert(0, "src")
import pandas as pd
from hybrid import research as R
roh = R._lesen("5m", "ADA", True)
h = roh["close"].resample("1h").last()
for kerze in ("2025-02-24 21:00", "2025-02-24 22:00", "2025-02-24 23:00", "2025-03-02 14:00", "2025-03-02 15:00", "2025-03-02 16:00"):
    t = pd.Timestamp(kerze); ref = t - pd.Timedelta(hours=336)
    print(f"Stundenkerze {kerze}: Schluss {h[t]:.4f} | Schluss 336 h zuvor {h[ref]:.4f} | Signal {'+1' if h[t] > h[ref] else '-1'}")
ein = float(roh.loc[pd.Timestamp("2025-02-24 23:00"), "open"])
print(f"\nEinstieg Short (Eroeffnung 2025-02-24 23:00, direkt nach Schluss der Kerze 22:00): {ein:.4f}")
print("Deckel greift ab Verhaeltnis 1,3327 (2000/1500) bzw. 1,4993 (150/100)")
for ts in pd.date_range("2025-03-02 15:00", "2025-03-02 18:00", freq="5min"):
    o, hi = float(roh.loc[ts, "open"]), float(roh.loc[ts, "high"])
    print(f"  {ts}  Eroeffnung {o:.4f} ({o / ein:.3f})  Hoch {hi:.4f} ({hi / ein:.3f})")
nach = roh.loc[pd.Timestamp("2025-03-02 16:00"):pd.Timestamp("2025-03-31 23:55")]
print(f"\n5m-Schluss ab 2025-03-02 16:00 bis 2025-03-31: Hoch {nach['high'].max():.4f} ({nach['high'].max() / ein:.3f}), erstmals wieder unter 1,3327 x Einstieg: "
      f"{nach.index[(nach['close'] / ein < 2000 / 1500 / 1.0005) & (nach.index > pd.Timestamp('2025-03-02 16:10'))][:1].tolist()}")
