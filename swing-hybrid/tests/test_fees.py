import pytest

from hybrid import config, fees


def test_effektive_saetze_mit_rebate():
    f = fees.scenarios(config.load())["mit_rebate"]
    assert f.net(10_000, "maker") == pytest.approx(0.6)   # 0,006 %
    assert f.net(10_000, "taker") == pytest.approx(1.2)   # 0,012 %


def test_ohne_rebate_volle_gebuehr():
    f = fees.scenarios(config.load())["ohne_rebate"]
    assert f.net(10_000, "maker") == pytest.approx(4.0)
    assert f.net(10_000, "taker") == pytest.approx(8.0)
    assert f.rebate_amount(10_000, "taker") == 0


def test_hebel_regeln():
    r = config.load()["risiko"]
    assert r["hebel_standard"] == 3 and r["hebel_max"] <= 5
