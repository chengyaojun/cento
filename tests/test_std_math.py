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
