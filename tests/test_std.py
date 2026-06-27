# tests/test_std.py
import pytest
from src.evaluator import eval_str
from src.errors import CentoError


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

def test_string_char_at():
    assert eval_str('(char-at "hello" 0)') == "h"
    assert eval_str('(char-at "hello" 4)') == "o"

def test_string_substring_two_args():
    assert eval_str('(substring "hello" 2)') == "llo"

def test_string_substring_three_args():
    assert eval_str('(substring "hello" 1 3)') == "el"

def test_string_from_code():
    assert eval_str('(from-code 65)') == "A"
    assert eval_str('(from-code 10)') == "\n"

def test_string_digit_q():
    assert eval_str('(digit? "5")') is True
    assert eval_str('(digit? "a")') is False
    assert eval_str('(digit? "")') is False

def test_string_alpha_q():
    assert eval_str('(alpha? "a")') is True
    assert eval_str('(alpha? "Z")') is True
    assert eval_str('(alpha? "1")') is False
    assert eval_str('(alpha? "")') is False

def test_string_space_q():
    assert eval_str('(space? " ")') is True
    assert eval_str('(space? "a")') is False
    assert eval_str('(space? "")') is False

def test_string_space_q_control_chars():
    assert eval_str('(space? (from-code 9))') is True
    assert eval_str('(space? (from-code 10))') is True
    assert eval_str('(space? (from-code 13))') is True

def test_string_parse_number_int():
    assert eval_str('(parse-number "42")') == 42.0

def test_string_parse_number_float():
    assert eval_str('(parse-number "3.14")') == 3.14

def test_string_parse_number_error():
    with pytest.raises(CentoError, match="Cannot parse number"):
        eval_str('(parse-number "abc")')
