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
