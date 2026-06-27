import pytest

from src.evaluator import eval_str


class TestIdentity:
    def test_identity_number(self):
        assert eval_str("(Identity 42)") == 42.0

    def test_identity_string(self):
        assert eval_str('(Identity "hello")') == "hello"

    def test_identity_nil(self):
        assert eval_str("(Identity nil)") is None


class TestIncDec:
    def test_inc(self):
        assert eval_str("(Inc 5)") == 6.0

    def test_inc_zero(self):
        assert eval_str("(Inc 0)") == 1.0

    def test_dec(self):
        assert eval_str("(Dec 5)") == 4.0

    def test_dec_negative(self):
        assert eval_str("(Dec 0)") == -1.0


class TestNumericPredicates:
    def test_even_true(self):
        assert eval_str("(Even? 4)") is True

    def test_even_false(self):
        assert eval_str("(Even? 3)") is False

    def test_odd_true(self):
        assert eval_str("(Odd? 3)") is True

    def test_odd_false(self):
        assert eval_str("(Odd? 4)") is False

    def test_zero_true(self):
        assert eval_str("(Zero? 0)") is True

    def test_zero_false(self):
        assert eval_str("(Zero? 1)") is False

    def test_pos_true(self):
        assert eval_str("(Pos? 5)") is True

    def test_pos_false(self):
        assert eval_str("(Pos? 0)") is False

    def test_neg_true(self):
        assert eval_str("(Neg? 0)") is False
        assert eval_str("(Neg? (- 5))") is True


class TestParseNumber:
    def test_parse_int(self):
        assert eval_str('(Parse-number "42")') == 42.0

    def test_parse_float(self):
        assert eval_str('(Parse-number "3.14")') == pytest.approx(3.14)

    def test_parse_invalid(self):
        with pytest.raises(Exception):
            eval_str('(Parse-number "not a number")')


class TestComp:
    def test_comp_two_fns(self):
        # comp(f, g) => x -> f(g(x)); Inc o Inc = +2
        result = eval_str("""
            (let [f (Comp Inc Inc)]
              (f 5))
        """)
        assert result == 7.0

    def test_comp_identity(self):
        result = eval_str("""
            (let [f (Comp Inc)]
              (f 10))
        """)
        assert result == 11.0


class TestApply:
    def test_apply_basic(self):
        # (Apply + [1 2 3]) => 6
        assert eval_str("(Apply + [1 2 3])") == 6.0

    def test_apply_with_str(self):
        result = eval_str('(Apply (fn [x y] (+ x y)) [10 20])')
        assert result == 30.0


class TestConst:
    def test_const_returns_constant(self):
        result = eval_str("""
            (let [always-42 (Const 42)]
              (always-42 1))
        """)
        assert result == 42.0

    def test_const_ignores_args(self):
        result = eval_str("""
            (let [c (Const "hi")]
              (c 1 2 3))
        """)
        assert result == "hi"


class TestComplement:
    def test_complement_basic(self):
        # (Complement (fn [x] (> x 5))) => x -> not(x > 5)
        result = eval_str("""
            (let [le5 (Complement (fn [x] (> x 5)))]
              (le5 3))
        """)
        assert result is True

    def test_complement_false_case(self):
        result = eval_str("""
            (let [le5 (Complement (fn [x] (> x 5)))]
              (le5 10))
        """)
        assert result is False
