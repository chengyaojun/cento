import pytest

from src.evaluator import eval_str


class TestSubstring:
    def test_substr_basic(self):
        assert eval_str('(Substr "hello" 1 3)') == "el"

    def test_substr_from_start(self):
        assert eval_str('(Substr "hello" 0 2)') == "he"

    def test_substr_to_end(self):
        assert eval_str('(Substr "hello" 2 5)') == "llo"


class TestIndexOf:
    def test_index_of_found(self):
        assert eval_str('(Index-of "hello" "ll")') == 2.0

    def test_index_of_not_found(self):
        assert eval_str('(Index-of "hello" "xy")') == -1.0

    def test_index_of_single_char(self):
        assert eval_str('(Index-of "hello" "o")') == 4.0


class TestIncludes:
    def test_includes_true(self):
        assert eval_str('(Includes "hello" "ell")') is True

    def test_includes_false(self):
        assert eval_str('(Includes "hello" "xyz")') is False

    def test_includes_empty(self):
        assert eval_str('(Includes "hello" "")') is True


class TestReverseStr:
    def test_reverse_str(self):
        assert eval_str('(Reverse-str "abc")') == "cba"

    def test_reverse_str_empty(self):
        assert eval_str('(Reverse-str "")') == ""

    def test_reverse_str_palindrome(self):
        assert eval_str('(Reverse-str "aba")') == "aba"


class TestRepeat:
    def test_repeat_basic(self):
        assert eval_str('(Repeat "ab" 3)') == "ababab"

    def test_repeat_zero(self):
        assert eval_str('(Repeat "ab" 0)') == ""

    def test_repeat_one(self):
        assert eval_str('(Repeat "x" 1)') == "x"


class TestCharAt:
    def test_char_at_first(self):
        assert eval_str('(Char-at "hello" 0)') == "h"

    def test_char_at_last(self):
        assert eval_str('(Char-at "hello" 4)') == "o"


class TestSplitLines:
    def test_split_lines_unix(self):
        # 使用真实换行符（lexer 不支持 \n 转义）
        code = '(Split-lines "a' + chr(10) + "b" + chr(10) + 'c")'
        result = eval_str(code)
        assert list(result) == ["a", "b", "c"]

    def test_split_lines_single(self):
        result = eval_str('(Split-lines "only")')
        assert list(result) == ["only"]


class TestLen:
    def test_len_string(self):
        assert eval_str('(Len "hello")') == 5.0

    def test_len_empty(self):
        assert eval_str('(Len "")') == 0.0
