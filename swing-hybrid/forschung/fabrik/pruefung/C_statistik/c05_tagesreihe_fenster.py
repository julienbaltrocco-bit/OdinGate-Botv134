"""C05 trichter.tagesreihe mit i0/i1 (so wie stufe4 sie für V2 aufruft), geprüft in einer V2-BLINDEN Umgebung (Speicher bei 2024-07-01 abgeschnitten).
1) Rechenprobe der Indizes für V2 (ohne Daten zu lesen).
2) "Probe-V2": V1 wird so behandelt, als wäre es die Schlussprüfung: tagesreihe(z, I_V1, I_ENDE) gegen den V1-Teil eines durchgehenden Laufs ab T.
   Stimmen die Tagesnummern? Wird L.I_ENDE gesetzt und zurückgesetzt? Wie stark hängt das Ergebnis davon ab, dass das Fenster ohne offene Position beginnt?
3) Fenster, das VOR dem Datenende endet (i1 < I_ENDE): keine Kerze ab i1 darf das Ergebnis beeinflussen.
4) "Doppelte Slippage" im Modell "bewegt" (faktor = 2), wie stufe4 sie für die Bedingung n85_2x_v2 > 0 benutzt: wird die Slippage wirklich verdoppelt?"""
import sys, math
import numpy as np
sys.path.insert(0, 'forschung/fabrik/pruefung/C_statistik')
import c_lib as C
from fabrik import daten as D, lauf as L, trichter as T

print("Code-Stand:", C.stand())
print("1) V2-Indizes: I_V2 =", T.I_V2, "=", D.RASTER[T.I_V2], "| I_V2ENDE =", T.I_V2ENDE, "= Rasterlänge", len(D.RASTER), "| Tage (I_V2ENDE - I_V2) // 288 =", (T.I_V2ENDE - T.I_V2) // 288,
      "| Rest", (T.I_V2ENDE - T.I_V2) % 288, "| letzter Rasterpunkt", D.RASTER[-1])
tagnr = np.clip((np.arange(T.I_V2ENDE) - T.I_V2) // 288, 0, 273)
print("   Tagesnummer der Kerze I_V2:", tagnr[T.I_V2], "| der letzten Kerze:", tagnr[-1], "| Kerzen vor I_V2 erhalten Tag", tagnr[T.I_V2 - 1], "(sie werden von sim nicht gebucht, weil der Lauf bei i0 beginnt)")

ende = C.blind()
print("\nV2-blinde Umgebung: D.N =", D.N, "=", D.RASTER[D.N], "| Länge der Kursreihe im Speicher:", L._g["o"].shape[-1])
con = C.ro()
fin = con.execute("SELECT * FROM kandidaten WHERE status = 'final' AND braucht != 't' AND (best IS NULL OR best NOT LIKE '%tiefe%' AND best NOT LIKE '%liq_entzug%') ORDER BY id LIMIT 45").fetchall()
fin += con.execute("SELECT * FROM kandidaten WHERE status = 'final' AND (braucht = 't' OR best LIKE '%tiefe%' OR best LIKE '%liq_entzug%') ORDER BY id LIMIT 15").fetchall()
T.ERG = C.ECHT_ERG                                             # ausstiege.json wird nur gelesen

print("\n2) Probe-V2 = V1 (Kerzen", L.I_V1, "bis", L.I_ENDE, "), 60 Finalisten")
i_mitte = L.idx("2024-01-01")
gleich_tage, korr, dn, dt_, ende_ok, abw3, n3 = [], [], [], [], True, 0, 0
for z in fin:
    tief = z["braucht"] == "t" or (z["best"] and ("tiefe" in z["best"] or "liq_entzug" in z["best"]))
    i0 = L.I_TIEFE if tief else L.I_T
    p_voll, n_voll, _ = T.tagesreihe(z, i0, L.I_ENDE, modell="bewegt")
    ende_ok &= L.I_ENDE == ende
    d_v1 = (L.I_V1 - i0) // 288
    p_fen, n_fen, _ = T.tagesreihe(z, L.I_V1, L.I_ENDE, modell="bewegt")
    a, b = p_voll[d_v1:], p_fen
    assert len(a) == len(b) == 366
    gleich_tage.append(np.mean(np.abs(a - b) < 1e-9)); korr.append(np.corrcoef(a, b)[0, 1] if a.std() > 0 and b.std() > 0 else np.nan)
    dt_.append(T.t_wert(b) - T.t_wert(a))
    # 3) Fenster endet am 2024-01-01: Vergleich mit dem Lauf bis I_ENDE auf den Tagen davor
    p_kurz, n_kurz, _ = T.tagesreihe(z, L.I_V1, i_mitte, modell="bewegt")
    tage_kurz = (i_mitte - L.I_V1) // 288
    ungleich = np.where(np.abs(p_kurz - p_fen[:tage_kurz]) > 1e-9)[0]
    n3 += 1; abw3 += len(ungleich) > 0 and ungleich.min() < tage_kurz - 2          # Abweichungen nur in den letzten Tagen (am Fensterende zwangsweise geschlossene Trades) sind erwartet
korr = np.array(korr)
print(f"   L.I_ENDE nach jedem Aufruf wieder {ende}: {ende_ok}")
print(f"   Anteil der V1-Tage mit bitgleichem Tagesergebnis (Fenster ab V1 gegen durchgehenden Lauf ab T): Median {np.median(gleich_tage):.3f}, kleinster Wert {np.min(gleich_tage):.3f}")
print(f"   Korrelation der Tagesreihen: Median {np.nanmedian(korr):.4f}, kleinster Wert {np.nanmin(korr):.4f} (bei um einen Tag verschobenen Tagesnummern läge sie nahe 0)")
print(f"   Unterschied im t-Wert über V1 allein durch den Start ohne offene Position: Mittel {np.mean(dt_):+.3f}, größter Betrag {np.max(np.abs(dt_)):.3f}")
print(f"3) Fenster bis 2024-01-01: Kandidaten mit Abweichungen früher als zwei Tage vor dem Fensterende: {abw3} von {n3}")

print("\n4) 'Doppelte Slippage' im Modell bewegt: Slippage je Order = max(gemessen, 5 % * faktor * Spanne der letzten Kerze)")
slip = np.asarray(L._g["slip_bp"])
for j in (0, 1, 2, 5, 9):
    b1, b2 = L.slip_bewegt(j, 1.0)[L.I_T:], L.slip_bewegt(j, 2.0)[L.I_T:]
    print(f"   {D.COINS[j]:<5} gemessen {slip[j]:.2f} bp | bewegt faktor 1: Mittel {b1.mean():.2f} | faktor 2: Mittel {b2.mean():.2f} = {b2.mean() / b1.mean():.2f}-fach "
          f"| Kerzen, in denen faktor 2 die Slippage gar nicht erhöht: {np.mean(b2 <= b1 + 1e-12):.1%} | wirklich verdoppelt: {np.mean(b2 >= 2 * b1 - 1e-9):.1%}")
verh, kipp, k1, k2 = [], 0, [], []
for z in fin:
    tief = z["braucht"] == "t" or (z["best"] and ("tiefe" in z["best"] or "liq_entzug" in z["best"]))
    i0 = L.I_TIEFE if tief else L.I_T
    _, n, roh0 = T.tagesreihe(z, i0, L.I_ENDE, modell="basis", faktor=0.0)
    _, _, roh1 = T.tagesreihe(z, i0, L.I_ENDE, modell="bewegt")
    _, _, roh2 = T.tagesreihe(z, i0, L.I_ENDE, modell="bewegt", faktor=2.0)
    s1, s2 = roh0 - roh1, roh0 - roh2
    verh.append(s2 / s1); k1.append(s1); k2.append(s2)
    kipp += (roh2 - L.KOSTEN85 > 0) and (roh0 - 2 * s1 - L.KOSTEN85 <= 0)
print(f"   60 Finalisten über T und V1: Slippage je Trade im Mittel {np.mean(k1):.2f} bp (faktor 1) und {np.mean(k2):.2f} bp (faktor 2); Verhältnis Median {np.median(verh):.2f}, "
      f"kleinster Wert {np.min(verh):.2f}, größter {np.max(verh):.2f} (verlangt: 2,00)")
print(f"   Kandidaten, die mit faktor 2 positiv bleiben, bei echter Verdopplung aber nicht: {kipp} von {len(fin)}")
