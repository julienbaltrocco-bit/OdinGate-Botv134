import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import vorwaertstest_auswerten as v


def test_slippage_richtung_und_gewichtung():
    df = pd.DataFrame({
        "zeit": ["2026-11-20 14:00"] * 2, "coin": ["BTC", "ETH"], "seite": ["kauf", "verkauf"],
        "signalkurs": [100.0, 200.0], "fuellkurs": [100.1, 199.9],     # Kauf 0,10 % teurer, Verkauf 0,05 % billiger
        "volumen": [1000.0, 3000.0], "gebuehr": [0.8, 2.4], "rebate": [0.68, 2.04]})
    e = v.auswerten(df)
    assert e["slippage_mittel"] == pytest.approx((0.001 * 1000 + 0.0005 * 3000) / 4000)
    assert e["gebuehr_satz"] == pytest.approx(0.0008) and e["rebate_anteil"] == pytest.approx(0.85)
    assert e["urteil"].startswith("über der Annahme")
