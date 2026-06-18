# tests/test_std.py
from src.evaluator import eval_str


def test_collection_map():
    assert list(eval_str('(Map (fn [x] (* x 2)) [1 2 3])')) == [2.0, 4.0, 6.0]

def test_collection_filter():
    assert list(eval_str('(Filter (fn [x] (> x 2)) [1 2 3 4])')) == [3.0, 4.0]

def test_collection_reduce():
    assert eval_str('(Reduce + 0 [1 2 3])') == 6.0

def test_collection_concat():
    assert list(eval_str('(Concat [1 2] [3 4])')) == [1.0, 2.0, 3.0, 4.0]

def test_collection_contains():
    assert eval_str('(Contains [1 2 3] 2)') is True
    assert eval_str('(Contains [1 2 3] 5)') is False

def test_collection_assoc():
    from src.types import Keyword
    result = eval_str('(Assoc {:a 1} :b 2)')
    assert result[Keyword("a")] == 1.0
    assert result[Keyword("b")] == 2.0

def test_collection_keys():
    result = eval_str('(Keys {:a 1 :b 2})')
    assert len(result) == 2

def test_collection_merge():
    from src.types import Keyword
    result = eval_str('(Merge {:a 1} {:b 2})')
    assert result[Keyword("a")] == 1.0
    assert result[Keyword("b")] == 2.0

def test_string_split():
    result = eval_str('(Split "a,b,c" ",")')
    assert list(result) == ["a", "b", "c"]

def test_string_join():
    assert eval_str('(Join ["a" "b" "c"] ",")') == "a,b,c"

def test_string_trim():
    assert eval_str('(Trim "  hello  ")') == "hello"

def test_string_upper():
    assert eval_str('(Upper "hello")') == "HELLO"

def test_string_lower():
    assert eval_str('(Lower "HELLO")') == "hello"

def test_string_replace():
    assert eval_str('(Replace "hello" "l" "r")') == "herro"

def test_string_has_prefix():
    assert eval_str('(Has-prefix "hello" "he")') is True

def test_string_has_suffix():
    assert eval_str('(Has-suffix "hello" "lo")') is True
