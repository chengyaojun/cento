# tests/test_evaluator.py
import pytest

from src.errors import CentoError
from src.evaluator import Evaluator


def eval_str(code: str):
    from src.lexer import Lexer
    from src.parser import Parser

    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    ev = Evaluator()
    result = None
    for expr in ast.expressions:
        result = ev.evaluate(expr)
    return result


def test_number():
    assert eval_str("42") == 42.0


def test_float():
    assert eval_str("3.14") == 3.14


def test_string():
    assert eval_str('"hello"') == "hello"


def test_bool_true():
    assert eval_str("true") is True


def test_bool_false():
    assert eval_str("false") is False


def test_nil():
    assert eval_str("nil") is None


def test_keyword():
    from src.types import Keyword

    result = eval_str(":name")
    assert result == Keyword("name")


def test_let_binding():
    assert eval_str("(let [x 10] x)") == 10.0


def test_let_multiple_bindings():
    assert eval_str("(let [x 10 y 20] (+ x y))") == 30.0


def test_let_multiple_body():
    assert eval_str("(let [x 10] 1 2 x)") == 10.0


def test_fn_in_let():
    assert eval_str("(let [add (fn [a b] (+ a b))] (add 3 4))") == 7.0


def test_named_fn_recursion():
    assert (
        eval_str(
            "(fn factorial [n] (if (<= n 1) 1 (* n (factorial (- n 1))))) (factorial 5)"
        )
        == 120.0
    )


def test_if_true():
    assert eval_str("(if true 1 2)") == 1.0


def test_if_false():
    assert eval_str("(if false 1 2)") == 2.0


def test_if_no_else_true():
    assert eval_str("(if true 1)") == 1.0


def test_if_no_else_false():
    assert eval_str("(if false 1)") is None


def test_closure():
    assert (
        eval_str("(let [make-adder (fn [x] (fn [y] (+ x y)))] ((make-adder 5) 3))")
        == 8.0
    )


def test_list_literal():
    from src.types import CentoList

    result = eval_str("[1 2 3]")
    assert isinstance(result, CentoList)
    assert list(result) == [1.0, 2.0, 3.0]


def test_map_literal():
    from src.types import CentoMap, Keyword

    result = eval_str("{:a 1 :b 2}")
    assert isinstance(result, CentoMap)
    assert result[Keyword("a")] == 1.0
    assert result[Keyword("b")] == 2.0


def test_undefined_symbol():
    with pytest.raises(CentoError, match="Undefined symbol"):
        eval_str("foo")


def test_not_a_function():
    with pytest.raises(CentoError, match="not callable"):
        eval_str("(42 1)")


def test_arithmetic():
    assert eval_str("(+ 1 2)") == 3.0
    assert eval_str("(- 5 3)") == 2.0
    assert eval_str("(* 3 4)") == 12.0
    assert eval_str("(/ 10 2)") == 5.0


def test_comparison():
    assert eval_str("(> 3 2)") is True
    assert eval_str("(< 3 2)") is False
    assert eval_str("(= 3 3)") is True
    assert eval_str("(>= 3 3)") is True
    assert eval_str("(<= 3 2)") is False


def test_logic():
    assert eval_str("(and true true)") is True
    assert eval_str("(and true false)") is False
    assert eval_str("(or false true)") is True
    assert eval_str("(not true)") is False


def test_tco_deep_recursion():
    """TCO should handle deep recursion without stack overflow."""
    code = """
    (fn loop [n acc]
      (if (= n 0)
        acc
        (loop (- n 1) (+ acc 1))))
    (loop 10000 0)
    """
    assert eval_str(code) == 10000.0


def test_try_catch():
    code = """
    (try
      (error "oops")
      (catch [e] e))
    """
    assert eval_str(code) == "oops"


def test_try_catch_no_error():
    code = """
    (try
      42
      (catch [e] 0))
    """
    assert eval_str(code) == 42.0


def test_try_catch_structured_error():
    code = """
    (try
      (error {:type :io-error :message "not found"})
      (catch [e] (get e :type)))
    """
    from src.types import Keyword

    result = eval_str(code)
    assert result == Keyword("io-error")


def test_ref():
    assert eval_str("(let [r (Ref 0)] (Ref-set! r 42) (Ref-get r))") == 42


def test_array():
    assert (
        eval_str("(let [arr (Array 3)] (Array-set! arr 0 10) (Array-get arr 0))") == 10
    )


def test_mutable_map():
    from src.types import Keyword

    result = eval_str(
        '(let [m (Mutable-map)] (Mutable-map-set! m :name "Cento") (Mutable-map-get m :name))'
    )
    assert result == "Cento"


class TestVariadicParams:
    def test_call_full_rest(self):
        assert list(eval_str("((fn [& rest] rest) 1 2 3)")) == [1.0, 2.0, 3.0]

    def test_call_mixed_rest(self):
        result = eval_str("((fn [a & rest] rest) 1 2 3)")
        assert list(result) == [2.0, 3.0]

    def test_call_empty_rest(self):
        assert list(eval_str("((fn [& rest] rest))")) == []

    def test_call_no_rest_strict_arity(self):
        with pytest.raises(Exception):
            eval_str("((fn [a] a) 1 2)")

    def test_call_rest_returns_centolist(self):
        from src.types import CentoList

        result = eval_str("((fn [& rest] rest) 1 2 3)")
        assert isinstance(result, CentoList)

    def test_tco_with_rest(self):
        # rest 参数与 TCO 兼容
        result = eval_str(
            """
            (let [count (fn [n acc & rest]
                          (if (= n 0)
                            acc
                            (count (- n 1) (+ acc 1))))]
              (count 100 0))
        """
        )
        assert result == 100.0


def test_apply_with_builtin():
    assert eval_str("(apply + [1 2 3])") == 6.0


def test_apply_with_fn():
    assert eval_str("(apply (fn [x y] (* x y)) [3 4])") == 12.0


def test_apply_with_no_args():
    assert eval_str("(apply (fn [] 42) [])") == 42.0


class TestCond:
    def test_cond_first_match(self):
        assert eval_str("(cond true 1 false 2)") == 1.0

    def test_cond_second_match(self):
        assert eval_str("(cond false 1 true 2)") == 2.0

    def test_cond_else_clause(self):
        assert eval_str("(cond false 1 false 2 :else 3)") == 3.0

    def test_cond_no_match_returns_nil(self):
        assert eval_str("(cond false 1 false 2)") is None

    def test_cond_short_circuit(self):
        # 未匹配分支不求值
        result = eval_str(
            """
            (cond
              true 1
              false (error "should not eval"))
        """
        )
        assert result == 1.0

    def test_cond_with_expressions(self):
        result = eval_str(
            """
            (let [x 5]
              (cond
                (< x 0) "neg"
                (< x 10) "small"
                :else "large"))
        """
        )
        assert result == "small"

    def test_cond_evaluates_test(self):
        # test 表达式被求值
        from src.types import Keyword

        assert eval_str("(cond (= 1 1) :yes :else :no)") == Keyword("yes")

    def test_cond_keyword_truthy(self):
        # :else 作为 keyword 总是 truthy
        from src.types import Keyword

        assert eval_str("(cond :else :ok)") == Keyword("ok")

    def test_cond_single_clause(self):
        from src.types import Keyword

        assert eval_str("(cond true :only)") == Keyword("only")

    def test_cond_empty_returns_nil(self):
        assert eval_str("(cond)") is None

    def test_cond_odd_args_error(self):
        # test/expr 必须成对
        with pytest.raises(Exception):
            eval_str("(cond true 1 false)")


class TestToCode:
    def test_to_code_uppercase(self):
        assert eval_str('(to-code "A")') == 65.0

    def test_to_code_lowercase(self):
        assert eval_str('(to-code "a")') == 97.0

    def test_to_code_digit(self):
        assert eval_str('(to-code "0")') == 48.0

    def test_from_to_code_roundtrip(self):
        assert eval_str('(from-code (to-code "x"))') == "x"

    def test_to_from_code_roundtrip(self):
        assert eval_str("(to-code (from-code 97))") == 97.0
