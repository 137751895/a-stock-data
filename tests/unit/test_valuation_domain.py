import math

from app.domain.valuation import forward_pe, pe_digestion, calc_peg


class TestForwardPE:
    def test_normal_case(self):
        assert forward_pe(100.0, 5.0) == 20.0

    def test_zero_eps(self):
        assert forward_pe(100.0, 0) == float("inf")

    def test_negative_eps(self):
        assert forward_pe(100.0, -1.0) == float("inf")


class TestPEDigestion:
    def test_already_below_target(self):
        assert pe_digestion(25.0, 0.3) == 0.0

    def test_normal_case(self):
        result = pe_digestion(60.0, 0.3)
        assert result > 0
        expected = math.log(60.0 / 30.0) / math.log(1.3)
        assert abs(result - expected) < 0.01

    def test_zero_cagr(self):
        assert pe_digestion(60.0, 0) == float("inf")

    def test_negative_cagr(self):
        assert pe_digestion(60.0, -0.1) == float("inf")

    def test_custom_target(self):
        result = pe_digestion(50.0, 0.2, target_pe=25.0)
        assert result > 0


class TestCalcPEG:
    def test_normal_case(self):
        assert calc_peg(20.0, 0.3) == 20.0 / 30.0

    def test_zero_cagr(self):
        assert calc_peg(20.0, 0) == float("inf")

    def test_negative_cagr(self):
        assert calc_peg(20.0, -0.1) == float("inf")

    def test_peg_below_one_is_cheap(self):
        peg = calc_peg(20.0, 0.3)
        assert peg < 1.0
