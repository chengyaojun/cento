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

def test_primitives_tokenizer():
    """验证原语协作：用 char-at/digit?/count/Concat/error 写最小 tokenizer。"""
    code = '''
    (let [s "42"
          n (count s)]
      (let [tokenize-loop
            (fn [i acc]
              (if (>= i n)
                acc
                (let [ch (char-at s i)]
                  (if (digit? ch)
                    (tokenize-loop (+ i 1)
                      (Concat acc [{:type :digit :value ch}]))
                    (error "unexpected char")))))]
        (tokenize-loop 0 [])))
    '''
    result = eval_str(code)
    assert len(result) == 2
    assert result[0][Keyword("type")] == Keyword("digit")
    assert result[0][Keyword("value")] == "4"
    assert result[1][Keyword("type")] == Keyword("digit")
    assert result[1][Keyword("value")] == "2"
