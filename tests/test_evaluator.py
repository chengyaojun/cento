# tests/test_evaluator.py
import pytest
from src.evaluator import Evaluator
from src.errors import CentoError


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
    assert eval_str('(let [x 10] x)') == 10.0

def test_let_multiple_bindings():
    assert eval_str('(let [x 10 y 20] (+ x y))') == 30.0

def test_let_multiple_body():
    assert eval_str('(let [x 10] 1 2 x)') == 10.0

def test_fn_in_let():
    assert eval_str('(let [add (fn [a b] (+ a b))] (add 3 4))') == 7.0

def test_named_fn_recursion():
    assert eval_str('(fn factorial [n] (if (<= n 1) 1 (* n (factorial (- n 1))))) (factorial 5)') == 120.0

def test_if_true():
    assert eval_str('(if true 1 2)') == 1.0

def test_if_false():
    assert eval_str('(if false 1 2)') == 2.0

def test_if_no_else_true():
    assert eval_str('(if true 1)') == 1.0

def test_if_no_else_false():
    assert eval_str('(if false 1)') is None

def test_closure():
    assert eval_str('(let [make-adder (fn [x] (fn [y] (+ x y)))] ((make-adder 5) 3))') == 8.0

def test_list_literal():
    from src.types import CentoList
    result = eval_str('[1 2 3]')
    assert isinstance(result, CentoList)
    assert list(result) == [1.0, 2.0, 3.0]

def test_map_literal():
    from src.types import Keyword, CentoMap
    result = eval_str('{:a 1 :b 2}')
    assert isinstance(result, CentoMap)
    assert result[Keyword("a")] == 1.0
    assert result[Keyword("b")] == 2.0

def test_undefined_symbol():
    with pytest.raises(CentoError, match="Undefined symbol"):
        eval_str("foo")

def test_not_a_function():
    with pytest.raises(CentoError, match="not callable"):
        eval_str('(42 1)')

def test_arithmetic():
    assert eval_str('(+ 1 2)') == 3.0
    assert eval_str('(- 5 3)') == 2.0
    assert eval_str('(* 3 4)') == 12.0
    assert eval_str('(/ 10 2)') == 5.0

def test_comparison():
    assert eval_str('(> 3 2)') is True
    assert eval_str('(< 3 2)') is False
    assert eval_str('(= 3 3)') is True
    assert eval_str('(>= 3 3)') is True
    assert eval_str('(<= 3 2)') is False

def test_logic():
    assert eval_str('(and true true)') is True
    assert eval_str('(and true false)') is False
    assert eval_str('(or false true)') is True
    assert eval_str('(not true)') is False

def test_tco_deep_recursion():
    """TCO should handle deep recursion without stack overflow."""
    code = '''
    (fn loop [n acc]
      (if (= n 0)
        acc
        (loop (- n 1) (+ acc 1))))
    (loop 10000 0)
    '''
    assert eval_str(code) == 10000.0

def test_try_catch():
    code = '''
    (try
      (error "oops")
      (catch [e] e))
    '''
    assert eval_str(code) == "oops"

def test_try_catch_no_error():
    code = '''
    (try
      42
      (catch [e] 0))
    '''
    assert eval_str(code) == 42.0

def test_try_catch_structured_error():
    code = '''
    (try
      (error {:type :io-error :message "not found"})
      (catch [e] (get e :type)))
    '''
    from src.types import Keyword
    result = eval_str(code)
    assert result == Keyword("io-error")

def test_ref():
    assert eval_str('(let [r (Ref 0)] (Ref-set! r 42) (Ref-get r))') == 42

def test_array():
    assert eval_str('(let [arr (Array 3)] (Array-set! arr 0 10) (Array-get arr 0))') == 10

def test_mutable_map():
    from src.types import Keyword
    result = eval_str('(let [m (Mutable-map)] (Mutable-map-set! m :name "Cento") (Mutable-map-get m :name))')
    assert result == "Cento"

def test_apply_with_builtin():
    assert eval_str('(apply + [1 2 3])') == 6.0

def test_apply_with_fn():
    assert eval_str('(apply (fn [x y] (* x y)) [3 4])') == 12.0

def test_apply_with_no_args():
    assert eval_str('(apply (fn [] 42) [])') == 42.0
