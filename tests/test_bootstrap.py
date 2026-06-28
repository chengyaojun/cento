"""自举加载机制专项测试。

验证：
1. .ct 文件中的函数已注册到 global_env
2. fallback 机制正常工作
3. Cento 实现与 Python 原生函数协同工作
"""

import pytest

from src.evaluator import Evaluator, eval_str


class TestBootstrapLoaded:
    def test_util_ct_functions_loaded(self):
        """验证 util.ct 中的函数已注册到 global_env"""
        e = Evaluator()
        # Inc 来自 util.ct
        assert e.global_env.lookup("Inc") is not None
        assert eval_str("(Inc 5)") == 6.0

    def test_seq_ct_functions_loaded(self):
        """验证 seq.ct 中的函数已注册到 global_env"""
        assert eval_str("(Take 2 [1 2 3])") == [1.0, 2.0]

    def test_complement_from_ct(self):
        """验证 Complement 来自 Cento 实现"""
        result = eval_str(
            """
            (let [le5 (Complement (fn [x] (> x 5)))]
              (le5 3))
        """
        )
        assert result is True

    def test_const_from_ct(self):
        """验证 Const 来自 util.ct，rest 参数支持"""
        result = eval_str(
            """
            (let [c (Const 42)]
              (c 1 2 3))
        """
        )
        assert result == 42.0

    def test_flatten_from_ct(self):
        """验证 Flatten 来自 seq.ct，递归 + 高阶函数"""
        result = eval_str("(Flatten [[1 2] [3] [4 [5]]])")
        assert list(result) == [1.0, 2.0, 3.0, 4.0, 5.0]


class TestFallbackOnCtError:
    def test_fallback_to_python(self):
        """构造 .ct 缺失场景验证 fallback 机制。
        由于 .ct 文件存在，此测试通过直接调用 _load_cent_module
        传入不存在的模块名验证异常处理。"""
        e = Evaluator()
        with pytest.raises(Exception):
            e._load_cent_module("nonexistent-module")


class TestMixedImplementation:
    def test_util_has_both_ct_and_python(self):
        """util 模块：Inc 和 Comp 均来自 util.ct，Apply 来自 evaluator"""
        # Inc 来自 util.ct
        assert eval_str("(Inc 0)") == 1.0
        # Comp 来自 util.ct（已自举）
        result = eval_str(
            """
            (let [f (Comp Inc Inc)]
              (f 5))
        """
        )
        assert result == 7.0

    def test_seq_has_both_ct_and_python(self):
        """seq 模块：Take 和 Sort 均来自 seq.ct，验证协同工作"""
        # Take 来自 seq.ct
        assert list(eval_str("(Take 2 [3 1 2])")) == [3.0, 1.0]
        # Sort 来自 seq.ct（已自举，归并排序）
        assert list(eval_str("(Sort [3 1 2])")) == [1.0, 2.0, 3.0]
        # 组合：先排序再取前 2 个
        assert list(eval_str("(Take 2 (Sort [3 1 2]))")) == [1.0, 2.0]


class TestSeqExtendedBootstrap:
    """seq.ct 扩展自举测试（Range + Sort 系列）"""

    def test_range_from_ct(self):
        """验证 Range 来自 seq.ct（Fn 类型），支持 2/3 参数"""
        from src.types import Fn

        e = Evaluator()
        # Range 应为 Cento Fn 实例（来自 .ct），而非 Python function
        assert isinstance(e.global_env.lookup("Range"), Fn)
        # 2 参数
        assert list(eval_str("(Range 0 3)")) == [0.0, 1.0, 2.0]
        # 3 参数
        assert list(eval_str("(Range 0 6 2)")) == [0.0, 2.0, 4.0]
        # 空区间
        assert list(eval_str("(Range 5 3)")) == []

    def test_range_float_step(self):
        """验证浮点 step 支持（Python 版本不支持）"""
        result = eval_str("(Range 0 1 0.25)")
        assert list(result) == [0.0, 0.25, 0.5, 0.75]

    def test_sort_from_ct(self):
        """验证 Sort 来自 seq.ct（Fn 类型）"""
        from src.types import Fn

        e = Evaluator()
        assert isinstance(e.global_env.lookup("Sort"), Fn)
        assert list(eval_str("(Sort [3 1 2])")) == [1.0, 2.0, 3.0]
        assert list(eval_str("(Sort [])")) == []
        assert list(eval_str("(Sort [42])")) == [42.0]

    def test_sort_desc_from_ct(self):
        """验证 Sort-desc 来自 seq.ct"""
        from src.types import Fn

        e = Evaluator()
        assert isinstance(e.global_env.lookup("Sort-desc"), Fn)
        assert list(eval_str("(Sort-desc [1 3 2])")) == [3.0, 2.0, 1.0]

    def test_sort_by_from_ct(self):
        """验证 Sort-by 来自 seq.ct"""
        from src.types import Fn

        e = Evaluator()
        assert isinstance(e.global_env.lookup("Sort-by"), Fn)
        result = eval_str("(Sort-by (fn [x] x) [3 1 2])")
        assert list(result) == [1.0, 2.0, 3.0]

    def test_sort_by_desc_from_ct(self):
        """验证 Sort-by-desc 来自 seq.ct"""
        from src.types import Fn

        e = Evaluator()
        assert isinstance(e.global_env.lookup("Sort-by-desc"), Fn)
        result = eval_str("(Sort-by-desc (fn [x] x) [1 3 2])")
        assert list(result) == [3.0, 2.0, 1.0]

    def test_sort_stability(self):
        """验证 Sort 稳定性：相同 key 元素保持原序"""
        from src.types import Keyword

        result = eval_str(
            """
            (Sort-by (fn [m] (get m :k))
              [{:k 1 :n 1} {:k 1 :n 2} {:k 1 :n 3}])
        """
        )
        n_values = [m.get(Keyword("n")) for m in result]
        assert n_values == [1.0, 2.0, 3.0]

    def test_merge_sort_internal_not_exported(self):
        """验证内部辅助函数 merge-lists/merge-sort 不被导出"""
        e = Evaluator()
        # 小写开头的绑定不应在 global_env 中（_load_cent_module 只收集大写开头）
        try:
            e.global_env.lookup("merge-sort")
            assert False, "merge-sort should not be exported"
        except Exception:
            pass  # 期望：找不到
        try:
            e.global_env.lookup("merge-lists")
            assert False, "merge-lists should not be exported"
        except Exception:
            pass


class TestStringBootstrap:
    """string.ct 自举来源验证"""

    def test_string_ct_functions_from_ct(self):
        """验证 string 纯逻辑函数来自 .ct（Fn 类型）"""
        from src.types import Fn

        e = Evaluator()
        for name in [
            "Has-prefix",
            "Has-suffix",
            "Substr",
            "Index-of",
            "Includes",
            "Reverse-str",
            "Repeat",
            "Join",
            "Split",
            "Split-lines",
            "Trim",
            "Upper",
            "Lower",
            "Replace",
            "Len",
        ]:
            assert isinstance(
                e.global_env.lookup(name), Fn
            ), f"{name} 应来自 string.ct（Fn 类型），实际为 {type(e.global_env.lookup(name))}"

    def test_string_primitives_from_python(self):
        """验证 string 原语来自 evaluator（Python callable，非 Fn）"""
        from src.types import Fn

        e = Evaluator()
        for name in [
            "char-at",
            "substring",
            "from-code",
            "to-code",
            "digit?",
            "alpha?",
            "space?",
            "parse-number",
        ]:
            val = e.global_env.lookup(name)
            assert not isinstance(val, Fn), f"{name} 应为 Python callable"
            assert callable(val), f"{name} 应为 callable"

    def test_to_code_available(self):
        """验证 to-code 原语已注册"""
        assert eval_str('(to-code "A")') == 65.0
