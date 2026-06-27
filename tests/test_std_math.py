import math

import pytest

from src.evaluator import eval_str


class TestTrigonometric:
    def test_sin(self):
        assert eval_str("(Sin 0)") == pytest.approx(0.0)
        assert eval_str("(Sin 1.5707963267948966)") == pytest.approx(1.0)  # pi/2

    def test_cos(self):
        assert eval_str("(Cos 0)") == pytest.approx(1.0)
        assert eval_str("(Cos 3.141592653589793)") == pytest.approx(-1.0)  # pi

    def test_tan(self):
        assert eval_str("(Tan 0)") == pytest.approx(0.0)

    def test_asin_acos_atan(self):
        assert eval_str("(Asin 1)") == pytest.approx(math.pi / 2)
        assert eval_str("(Acos 1)") == pytest.approx(0.0)
        assert eval_str("(Atan 1)") == pytest.approx(math.pi / 4)


class TestExponentialLog:
    def test_exp(self):
        assert eval_str("(Exp 0)") == pytest.approx(1.0)
        assert eval_str("(Exp 1)") == pytest.approx(math.e)

    def test_log(self):
        assert eval_str("(Log 1)") == pytest.approx(0.0)  # ln(1) = 0
        assert eval_str("(Log 2.718281828459045)") == pytest.approx(1.0)  # ln(e)

    def test_log10(self):
        assert eval_str("(Log10 100)") == pytest.approx(2.0)
        assert eval_str("(Log10 1000)") == pytest.approx(3.0)

    def test_sqrt(self):
        assert eval_str("(Sqrt 4)") == pytest.approx(2.0)
        assert eval_str("(Sqrt 2)") == pytest.approx(math.sqrt(2))

    def test_pow(self):
        assert eval_str("(Pow 2 3)") == pytest.approx(8.0)
        assert eval_str("(Pow 9 0.5)") == pytest.approx(3.0)


class TestRounding:
    def test_floor(self):
        assert eval_str("(Floor 3.7)") == 3.0
        assert eval_str("(Floor (- 1.5))") == -2.0  # -1.5

    def test_ceil(self):
        assert eval_str("(Ceil 3.2)") == 4.0
        assert eval_str("(Ceil (- 1.5))") == -1.0  # -1.5

    def test_round(self):
        assert eval_str("(Round 3.4)") == 3.0
        assert eval_str("(Round 3.5)") == 4.0
        assert eval_str("(Round 2.5)") == 2.0  # Python banker's rounding

    def test_floor_returns_float(self):
        result = eval_str("(Floor 3.7)")
        assert isinstance(result, float)

    def test_ceil_returns_float(self):
        result = eval_str("(Ceil 3.2)")
        assert isinstance(result, float)


class TestConstants:
    def test_pi(self):
        assert eval_str("Pi") == pytest.approx(math.pi)

    def test_e(self):
        assert eval_str("E") == pytest.approx(math.e)


class TestDomainErrors:
    def test_sqrt_negative(self):
        with pytest.raises(Exception):
            eval_str("(Sqrt (- 1))")

    def test_log_zero(self):
        with pytest.raises(Exception):
            eval_str("(Log 0)")

    def test_asin_out_of_range(self):
        with pytest.raises(Exception):
            eval_str("(Asin 2)")

    def test_error_caught_by_try(self):
        result = eval_str(
            """
            (try
              (Sqrt (- 1))
              (catch [msg] (str "caught: " msg)))
        """
        )
        assert "caught" in result
