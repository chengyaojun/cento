import pytest

from src.evaluator import eval_str


class TestSort:
    def test_sort_asc(self):
        assert list(eval_str("(Sort [3 1 2])")) == [1.0, 2.0, 3.0]

    def test_sort_empty(self):
        assert list(eval_str("(Sort [])")) == []

    def test_sort_sorted(self):
        assert list(eval_str("(Sort [1 2 3])")) == [1.0, 2.0, 3.0]

    def test_sort_desc(self):
        assert list(eval_str("(Sort-desc [1 3 2])")) == [3.0, 2.0, 1.0]


class TestSortBy:
    def test_sort_by_key(self):
        # 按绝对值排序（输入含正负，但 lexer 不支持负数，用 (- 1) 等）
        result = eval_str("(Sort-by (fn [x] x) [3 1 2])")
        assert list(result) == [1.0, 2.0, 3.0]

    def test_sort_by_desc(self):
        result = eval_str("(Sort-by-desc (fn [x] x) [1 3 2])")
        assert list(result) == [3.0, 2.0, 1.0]


class TestTake:
    def test_take_basic(self):
        assert list(eval_str("(Take 2 [1 2 3 4])")) == [1.0, 2.0]

    def test_take_more_than_len(self):
        assert list(eval_str("(Take 10 [1 2])")) == [1.0, 2.0]

    def test_take_zero(self):
        assert list(eval_str("(Take 0 [1 2 3])")) == []


class TestDrop:
    def test_drop_basic(self):
        assert list(eval_str("(Drop 2 [1 2 3 4])")) == [3.0, 4.0]

    def test_drop_more_than_len(self):
        assert list(eval_str("(Drop 10 [1 2])")) == []

    def test_drop_zero(self):
        assert list(eval_str("(Drop 0 [1 2 3])")) == [1.0, 2.0, 3.0]


class TestNth:
    def test_nth_first(self):
        assert eval_str("(Nth [10 20 30] 0)") == 10.0

    def test_nth_last(self):
        assert eval_str("(Nth [10 20 30] 2)") == 30.0

    def test_nth_out_of_range(self):
        with pytest.raises(Exception):
            eval_str("(Nth [10 20] 5)")


class TestLast:
    def test_last_basic(self):
        assert eval_str("(Last [1 2 3])") == 3.0

    def test_last_single(self):
        assert eval_str("(Last [42])") == 42.0


class TestRange:
    def test_range_basic(self):
        assert list(eval_str("(Range 0 3)")) == [0.0, 1.0, 2.0]

    def test_range_with_step(self):
        assert list(eval_str("(Range 0 6 2)")) == [0.0, 2.0, 4.0]

    def test_range_empty(self):
        assert list(eval_str("(Range 5 3)")) == []


class TestDistinct:
    def test_distinct_basic(self):
        assert list(eval_str("(Distinct [1 2 1 3 2])")) == [1.0, 2.0, 3.0]

    def test_distinct_empty(self):
        assert list(eval_str("(Distinct [])")) == []

    def test_distinct_all_same(self):
        assert list(eval_str("(Distinct [5 5 5])")) == [5.0]


class TestFlatten:
    def test_flatten_one_level(self):
        result = eval_str("(Flatten [[1 2] [3 4]])")
        assert list(result) == [1.0, 2.0, 3.0, 4.0]

    def test_flatten_nested(self):
        result = eval_str("(Flatten [[1 [2 3]] [4]])")
        assert list(result) == [1.0, 2.0, 3.0, 4.0]

    def test_flatten_already_flat(self):
        assert list(eval_str("(Flatten [1 2 3])")) == [1.0, 2.0, 3.0]


class TestZip:
    def test_zip_basic(self):
        result = eval_str("(Zip [1 2] [3 4])")
        # 结果是 [[1 3] [2 4]]
        assert len(result) == 2
        assert list(result[0]) == [1.0, 3.0]
        assert list(result[1]) == [2.0, 4.0]

    def test_zip_unequal(self):
        result = eval_str("(Zip [1 2 3] [4 5])")
        assert len(result) == 2


class TestReverse:
    def test_reverse_basic(self):
        assert list(eval_str("(Reverse [1 2 3])")) == [3.0, 2.0, 1.0]

    def test_reverse_empty(self):
        assert list(eval_str("(Reverse [])")) == []

    def test_reverse_single(self):
        assert list(eval_str("(Reverse [42])")) == [42.0]
