"""Tests zu E27 (Tagesvariante der Trendregel), Festlegung in forschung/protokoll.md Abschnitt 51."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "forschung"))
pytest.importorskip("numba")
from experimente import e23_marktstruktur as E  # noqa: E402
from experimente import e27_tagesvariante as X  # noqa: E402


def kurs(n, seed):
    rng = np.random.default_rng(seed)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.003, n)))
    o = np.concatenate([[100.0], c[:-1]])
    return o, np.maximum(o, c) * 1.001, np.minimum(o, c) * 0.999, c


@pytest.mark.parametrize("abstand,phase", [(24, 0), (24, 8), (24, 20), (4, 0), (12, 0)])
def test_abgefragte_richtung_wie_einfache_schleife(abstand, phase):
    rng = np.random.default_rng(abstand + phase)
    d = rng.integers(-1, 2, 24 * 40).astype(np.int8)
    soll, halte = [], 0
    for t in range(len(d)):
        if (t + 1) % abstand == phase % abstand:                   # die Stundenkerze t schließt zur vollen Stunde t+1
            halte = int(d[t])
        soll.append(halte)
    assert X.richtung_abgefragt(d, abstand, phase).tolist() == soll
    d2 = d.copy(); d2[500:] = -d2[500:]                             # spätere Stunden ändern frühere Werte nicht
    assert np.array_equal(X.richtung_abgefragt(d2, abstand, phase)[:500], X.richtung_abgefragt(d, abstand, phase)[:500])


def test_tagesvariante_handelt_nur_um_0005_utc_und_haelt_die_richtung_von_mitternacht():
    n = 12 * 24 * 80
    o, h, l, c = kurs(n, 4)
    d = E.richtung_stunden(c)
    dh = X.richtung_abgefragt(d, 24, 0)
    nt = n // E.TAG + 1
    leer, leer8, od = np.zeros(1), np.zeros(1, np.int8), np.zeros((5000, 4))
    no = E.lauf(o, h, l, c, np.ones(n, bool), np.zeros(n), 1.0, dh, 12, 3, leer, leer, leer, leer, leer8, leer8, E.B0, n,
                np.zeros((2, nt)), np.zeros((2, nt)), np.zeros((2, nt)), np.zeros(nt), np.zeros(7), od)
    assert no > 6 and (od[:no, 0] % 288 == 1).all()                # Ausführung zur Eröffnung der Kerze 00:05 UTC
    pos = np.zeros(n, int)
    for kerze, seite, anlass, _ in od[:no]:
        pos[int(kerze):] = int(seite) if anlass == 1 else 0
    for tag in range(16, 79):                                      # Position des Tages = d der Stunde, die um 00:00 UTC dieses Tages schloss
        assert (pos[288 * tag + 1:288 * (tag + 1) + 1] == d[24 * tag - 1]).all()
    b0 = np.zeros((5000, 4))
    nb = E.lauf(o, h, l, c, np.ones(n, bool), np.zeros(n), 1.0, d, 12, 3, leer, leer, leer, leer, leer8, leer8, E.B0, n,
                np.zeros((2, nt)), np.zeros((2, nt)), np.zeros((2, nt)), np.zeros(nt), np.zeros(7), b0)
    assert nb > no                                                 # die Stundenregel stellt mehr Orders


def eingabe(tag_ohne=0.002, tag_mit=0.002, b0_ohne=0.0005, b0_mit=0.002, phasen_gut=6, orders=(100.0, 500.0)):
    rng = np.random.default_rng(1)
    rausch = rng.normal(0, 0.01, 300)
    rausch -= rausch.mean()                                        # ohne eigenen Beitrag zur Summe
    r = {("B0", "bewegt", "ohne"): rausch + b0_ohne, ("B0", "bewegt", "mit"): rausch + b0_mit}
    for i, p in enumerate(X.PHASEN):
        k = X.name_phase(p)
        r[(k, "bewegt", "ohne")] = rausch + (tag_ohne if i < phasen_gut else -0.001)
        r[(k, "bewegt", "mit")] = rausch + tag_mit
    r[("TAG", "bewegt", "ohne")] = rausch + tag_ohne
    return r, {"TAG": orders[0], "B0": orders[1]}


def test_bedingungen_einzeln():
    assert X.bedingungen(*eingabe())["alle"]
    b = X.bedingungen(*eingabe(tag_ohne=0.0004))
    assert not b["A_ohne_rebate_besser"] and not b["alle"]
    b = X.bedingungen(*eingabe(tag_mit=0.001))                     # mit Rebate nur die Hälfte von B0
    assert b["A_ohne_rebate_besser"] and not b["B_mit_rebate_nicht_schlechter"] and not b["alle"]
    assert X.bedingungen(*eingabe(tag_mit=0.0014))["B_mit_rebate_nicht_schlechter"]            # gut zwei Drittel reichen
    assert X.bedingungen(*eingabe(tag_mit=-0.001, b0_mit=-0.002))["B_mit_rebate_nicht_schlechter"]   # B0 negativ: TAG nur nicht schlechter
    assert not X.bedingungen(*eingabe(tag_mit=-0.003, b0_mit=-0.002))["B_mit_rebate_nicht_schlechter"]
    b = X.bedingungen(*eingabe(orders=(200.0, 500.0)))
    assert not b["C_hoechstens_ein_drittel_der_orders"] and not b["alle"]
    assert X.bedingungen(*eingabe(phasen_gut=4))["D_mindestens_vier_von_sechs_uhrzeiten"]
    b = X.bedingungen(*eingabe(phasen_gut=3))
    assert b["A_ohne_rebate_besser"] and not b["D_mindestens_vier_von_sechs_uhrzeiten"] and not b["alle"]


def test_v2_nur_einmal_und_nur_nach_freigabe(tmp_path, monkeypatch):
    monkeypatch.setattr(X, "ERGEBNIS", tmp_path / "e27.json")
    X.ERGEBNIS.write_text(json.dumps({"v2_frei": False}))
    with pytest.raises(SystemExit):
        X.stufe2()                                                 # Stufe 1 gibt nicht frei
    X.ERGEBNIS.write_text(json.dumps({"v2_frei": True, "V2": {"stand": "x"}}))
    with pytest.raises(SystemExit):
        X.stufe2()                                                 # schon geöffnet
    with pytest.raises(SystemExit):
        X.stufe1()                                                 # und Stufe 1 überschreibt das Ergebnis nicht mehr
    assert json.loads(X.ERGEBNIS.read_text()) == {"v2_frei": True, "V2": {"stand": "x"}}
    assert X.regeln(False).keys() == {"B0", "TAG", "TAG_04", "TAG_08", "TAG_12", "TAG_16", "TAG_20"} and "ALLE_4H" in X.regeln(True)
    assert E.tage("V2").stop * E.TAG == X.D.N and str(X.D.RASTER[-1]) == "2025-03-31 23:55:00"   # der Speicher endet mit V2
