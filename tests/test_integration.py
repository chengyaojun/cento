"""End-to-end integration tests for Cento."""
from src.evaluator import eval_str
from src.types import Keyword, CentoList, CentoMap


def test_fibonacci():
    code = '''
    (fn fib [n]
      (if (<= n 1)
        n
        (+ (fib (- n 1)) (fib (- n 2)))))
    (fib 10)
    '''
    assert eval_str(code) == 55.0

def test_higher_order_functions():
    code = '''
    (let [double (fn [x] (* x 2))]
      (Map double [1 2 3]))
    '''
    result = eval_str(code)
    assert list(result) == [2.0, 4.0, 6.0]

def test_closure_counter():
    code = '''
    (let [make-counter (fn []
      (let [r (Ref 0)]
        (fn []
          (Ref-set! r (+ (Ref-get r) 1))
          (Ref-get r))))]
      (let [c (make-counter)]
        (c) (c) (c)))
    '''
    assert eval_str(code) == 3.0

def test_map_operations():
    code = '''
    (let [m {:name "Cento" :version 1}]
      (let [m2 (Assoc m :version 2)]
        (get m2 :version)))
    '''
    assert eval_str(code) == 2.0

def test_string_processing():
    code = '''
    (let [words (Split "hello world foo" " ")]
      (Map Upper words))
    '''
    result = eval_str(code)
    assert list(result) == ["HELLO", "WORLD", "FOO"]

def test_error_handling():
    code = '''
    (fn safe-div [a b]
      (try
        (/ a b)
        (catch [e] nil)))
    (safe-div 10 2)
    '''
    assert eval_str(code) == 5.0

def test_error_handling_catch():
    code = '''
    (fn safe-div [a b]
      (try
        (/ a b)
        (catch [e] nil)))
    (safe-div 10 0)
    '''
    assert eval_str(code) is None

def test_nested_let():
    code = '''
    (let [x 10]
      (let [y 20]
        (let [z (+ x y)]
          z)))
    '''
    assert eval_str(code) == 30.0

def test_immutability():
    code = '''
    (let [xs [1 2 3]]
      (let [ys (Concat xs [4 5])]
        (count xs)))
    '''
    assert eval_str(code) == 3.0

def test_tco_factorial():
    code = '''
    (fn fact [n acc]
      (if (= n 0)
        acc
        (fact (- n 1) (* n acc))))
    (fact 20 1)
    '''
    assert eval_str(code) == 2432902008176640000.0
