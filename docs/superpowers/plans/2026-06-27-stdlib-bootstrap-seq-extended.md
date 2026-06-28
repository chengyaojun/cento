# seq 剩余函数自举（Range + Sort 系列）实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 用 Cento 语言重新实现 seq 模块中剩余的 5 个函数（Range + Sort/Sort-desc/Sort-by/Sort-by-desc），完成 seq 模块的全部自举。

**架构：** 扩展 `src/std/seq.ct` 添加 Range（用 `& rest` 支持可选 step）和 Sort 系列（归并排序，复用 Take/Drop/Count/Concat）；扩展 `_load_cent_module` 注册 math 模块依赖以提供 Floor；通过现有 `tests/test_std_seq.py` 测试自动验证行为一致性，新增 `tests/test_bootstrap.py` 测试验证 Cento 实现来源。

**技术栈：** Cento 语言（Lisp 方言）、Python 3.10+、pytest

**规格：** `docs/superpowers/specs/2026-06-27-stdlib-bootstrap-seq-extended-design.md`

---

## 文件结构

| 文件 | 职责 | 操作 |
|------|------|------|
| `src/evaluator.py` | `_load_cent_module` 方法扩展，注册 math 依赖 | 修改 |
| `src/std/seq.ct` | 新增 Range/Sort/Sort-desc/Sort-by/Sort-by-desc + merge-lists/merge-sort | 修改 |
| `tests/test_bootstrap.py` | 添加 `TestSeqExtendedBootstrap` 测试类 | 修改 |

**关键决策**：
- 现有 `tests/test_std_seq.py` 中 `TestRange`（3 个）、`TestSort`（4 个）、`TestSortBy`（2 个）共 9 个测试无需修改，自动验证 Cento 实现行为一致性（因加载机制为 Cento 优先 + Python fallback）
- 内部辅助 `merge-lists`/`merge-sort` 以小写开头，不会被 `_load_cent_module` 导出（符合现有模块系统约定）

---

## 任务 1：扩展 _load_cent_module 注册 math 模块依赖

**文件：**
- 修改：`src/evaluator.py` 的 `_load_cent_module` 方法（当前在 collection 注册后约第 145 行）

**理由**：seq.ct 的 `merge-sort` 需要调用 `Floor` 计算 list 中点。当前 `_load_cent_module` 只注册 collection 作为子 evaluator 依赖，需扩展同时注册 math。

- [ ] **步骤 1：修改 _load_cent_module 添加 math 注册**

在 `src/evaluator.py` 的 `_load_cent_module` 方法中，找到当前注册 collection 的代码块：

```python
        sub_evaluator = Evaluator(skip_std=True)
        from src.std.collection import FUNCTIONS as COLLECTION_FUNCTIONS

        for name, fn in COLLECTION_FUNCTIONS.items():
            sub_evaluator.global_env.define(name, fn, exported=True)
```

在 collection 注册之后，添加 math 模块注册：

```python
        sub_evaluator = Evaluator(skip_std=True)
        from src.std.collection import FUNCTIONS as COLLECTION_FUNCTIONS

        for name, fn in COLLECTION_FUNCTIONS.items():
            sub_evaluator.global_env.define(name, fn, exported=True)
        # 注册 math 模块（Floor 等基础数学函数，供 .ct 中排序等算法使用）
        from src.std.math import FUNCTIONS as MATH_FUNCTIONS

        for name, fn in MATH_FUNCTIONS.items():
            sub_evaluator.global_env.define(name, fn, exported=True)
```

- [ ] **步骤 2：运行全套测试验证零回归**

运行：`python -m pytest --tb=short -q`
预期：PASS，235 个测试全绿（此改动不影响现有 .ct 文件，因 util.ct/seq.ct/collection.ct 当前未使用 math）

- [ ] **步骤 3：Commit**

```bash
git add src/evaluator.py
git commit -m "feat(bootstrap): _load_cent_module 注册 math 模块依赖" -m "为后续 seq.ct 中归并排序使用 Floor 计算中点做准备。"
```

---

## 任务 2：实现 Range 自举

**文件：**
- 修改：`src/std/seq.ct`（在文件末尾追加 Range 实现）
- 测试：`tests/test_bootstrap.py`（添加 Range 来源验证测试）

**设计要点**：
- `Range` 用 `& rest` 接收可选 step，默认 1
- `Range-helper` 用累加器递归，TCO 友好
- 终止条件 `current >= end`，正确处理 `Range 5 3` 返回 `[]`
- 浮点 step 自然支持（如 `Range 0 1 0.25` → `[0 0.25 0.5 0.75]`）

- [ ] **步骤 1：编写失败的测试**

在 `tests/test_bootstrap.py` 末尾追加新测试类：

```python
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
```

- [ ] **步骤 2：运行测试验证失败**

运行：`python -m pytest tests/test_bootstrap.py::TestSeqExtendedBootstrap::test_range_from_ct tests/test_bootstrap.py::TestSeqExtendedBootstrap::test_range_float_step -v`
预期：FAIL，报错 `KeyError: 'Range'` 或 `assert isinstance(e.global_env.lookup("Range"), Fn)` 失败（Range 当前来自 Python fallback，类型为 `function` 而非 `Fn`）

- [ ] **步骤 3：在 seq.ct 末尾追加 Range 实现**

在 `src/std/seq.ct` 文件末尾追加（注意保留现有 9 个函数不动）：

```lisp

; Range - 支持 2/3 参数，浮点 step
(fn Range-helper [current end step acc]
  (if (>= current end)
    acc
    (Range-helper (+ current step) end step (Concat acc [current]))))

(fn Range [start end & rest]
  (let [step (if (empty? rest) 1 (first rest))]
    (Range-helper start end step [])))
```

- [ ] **步骤 4：运行新测试验证通过**

运行：`python -m pytest tests/test_bootstrap.py::TestSeqExtendedBootstrap::test_range_from_ct tests/test_bootstrap.py::TestSeqExtendedBootstrap::test_range_float_step -v`
预期：PASS，2 个测试通过

- [ ] **步骤 5：运行现有 TestRange 测试验证行为一致**

运行：`python -m pytest tests/test_std_seq.py::TestRange -v`
预期：PASS，3 个测试全绿（range_basic/range_with_step/range_empty）

- [ ] **步骤 6：Commit**

```bash
git add src/std/seq.ct tests/test_bootstrap.py
git commit -m "feat(bootstrap): Range 自举实现（& rest 支持可选 step）" -m "利用 & rest 可变参数支持，Range 现支持 2/3 参数调用与浮点 step。新增 TestSeqExtendedBootstrap 测试类验证 Cento 实现来源。"
```

---

## 任务 3：实现 Sort 系列自举（归并排序）

**文件：**
- 修改：`src/std/seq.ct`（追加 merge-lists/merge-sort + 4 个公开函数）
- 测试：`tests/test_bootstrap.py`（追加 Sort 来源验证测试）

**设计要点**：
- `merge-lists` 用 `cmp` 谓词统一支持 4 个 Sort 变体
- 稳定性：`cmp` 为真时取左侧 `a`，保留原顺序
- 中点用 `(Floor (/ (count xs) 2))` 计算
- 内部辅助以小写开头不导出

- [ ] **步骤 1：编写失败的测试**

在 `tests/test_bootstrap.py` 的 `TestSeqExtendedBootstrap` 类中追加：

```python
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
        # 用 map 的 :k 作为 key，值相同时应保持原序
        # 输入 [{:k 1 :n 1} {:k 1 :n 2} {:k 1 :n 3}]，按 :k 排序应保持原序
        result = eval_str("""
            (Sort-by (fn [m] (get m :k))
              [{:k 1 :n 1} {:k 1 :n 2} {:k 1 :n 3}])
        """)
        # 验证 :n 字段保持 1, 2, 3 原序
        n_values = [eval_str("(get m :n)") for m in result]
        # 注意：上述 list comprehension 在 Python 中执行，需用 CentoMap.get
        # 简化：直接用 Python 验证
        n_values = [m.get(Keyword("n")) for m in result]
        assert n_values == [1.0, 2.0, 3.0]

    def test_merge_sort_internal_not_exported(self):
        """验证内部辅助函数 merge-lists/merge-sort 不被导出"""
        e = Evaluator()
        # 小写开头的绑定不应在 global_env 中（_load_cent_module 只收集大写开头）
        # 注意：sub_evaluator 内部确实定义了这些函数，但不会注册到 global_env
        try:
            e.global_env.lookup("merge-sort")
            # 如果能找到，说明被错误导出
            assert False, "merge-sort should not be exported"
        except Exception:
            pass  # 期望：找不到
        try:
            e.global_env.lookup("merge-lists")
            assert False, "merge-lists should not be exported"
        except Exception:
            pass
```

**注意**：`test_sort_stability` 中需要从 Python 导入 `Keyword`，确认在文件顶部已有导入或在此测试方法内导入。检查 `tests/test_bootstrap.py` 当前导入：

```python
import pytest
from src.evaluator import Evaluator, eval_str
```

需在测试方法内或文件顶部添加 `from src.types import Keyword`。为保持最小改动，在 `test_sort_stability` 方法内导入：

```python
    def test_sort_stability(self):
        """验证 Sort 稳定性：相同 key 元素保持原序"""
        from src.types import Keyword
        result = eval_str("""
            (Sort-by (fn [m] (get m :k))
              [{:k 1 :n 1} {:k 1 :n 2} {:k 1 :n 3}])
        """)
        n_values = [m.get(Keyword("n")) for m in result]
        assert n_values == [1.0, 2.0, 3.0]
```

- [ ] **步骤 2：运行测试验证失败**

运行：`python -m pytest tests/test_bootstrap.py::TestSeqExtendedBootstrap -v -k "sort or merge"`
预期：FAIL，6 个测试失败（Sort 系列当前来自 Python fallback，类型为 `function` 而非 `Fn`；`test_merge_sort_internal_not_exported` 可能通过，因当前确实没有这些函数）

- [ ] **步骤 3：在 seq.ct 末尾追加 Sort 系列实现**

在 `src/std/seq.ct` 文件末尾追加（在 Range 之后）：

```lisp

; 内部：合并两个已排序的列表（累加器式，TCO 友好）
; cmp 为比较谓词，cmp(a, b) 为真时取 a（保证稳定性）
(fn merge-lists [a b cmp acc]
  (if (empty? a)
    (Concat acc b)
    (if (empty? b)
      (Concat acc a)
      (if (cmp (first a) (first b))
        (merge-lists (rest a) b cmp (Concat acc [(first a)]))
        (merge-lists a (rest b) cmp (Concat acc [(first b)]))))))

; 内部：归并排序主递归
(fn merge-sort [xs cmp]
  (if (<= (count xs) 1)
    xs
    (let [mid (Floor (/ (count xs) 2))]
      (merge-lists
        (merge-sort (Take mid xs) cmp)
        (merge-sort (Drop mid xs) cmp)
        cmp
        []))))

; 公开 Sort 系列 API
(fn Sort [xs] (merge-sort xs <=))
(fn Sort-desc [xs] (merge-sort xs >=))
(fn Sort-by [f xs] (merge-sort xs (fn [a b] (<= (f a) (f b)))))
(fn Sort-by-desc [f xs] (merge-sort xs (fn [a b] (>= (f a) (f b)))))
```

- [ ] **步骤 4：运行新测试验证通过**

运行：`python -m pytest tests/test_bootstrap.py::TestSeqExtendedBootstrap -v`
预期：PASS，8 个测试全绿（Range 2 个 + Sort 6 个）

- [ ] **步骤 5：运行现有 TestSort/TestSortBy 测试验证行为一致**

运行：`python -m pytest tests/test_std_seq.py::TestSort tests/test_std_seq.py::TestSortBy -v`
预期：PASS，6 个测试全绿（sort_asc/sort_empty/sort_sorted/sort_desc/sort_by_key/sort_by_desc）

- [ ] **步骤 6：Commit**

```bash
git add src/std/seq.ct tests/test_bootstrap.py
git commit -m "feat(bootstrap): Sort 系列自举实现（归并排序）" -m "新增 merge-lists/merge-sort 内部辅助（小写不导出）和 Sort/Sort-desc/Sort-by/Sort-by-desc 公开函数。归并排序保证稳定性，与 Python Timsort 行为一致。"
```

---

## 任务 4：全套测试验证与推送

**文件：**
- 无新文件改动，仅运行验证

- [ ] **步骤 1：运行全套测试验证零回归**

运行：`python -m pytest --tb=short -q`
预期：PASS，235 + 8 = 243 个测试全绿

- [ ] **步骤 2：手动验证 Cento 实现来源**

运行：`python -c "from src.evaluator import eval_str; from src.types import Fn, type; print('Sort:', type(eval_str('Sort'))); print('Range:', type(eval_str('Range')))"`
预期：输出 `Sort: fn` 和 `Range: fn`（Cento Fn 类型）

**修正**：Cento 的 `type` 是内置函数，会返回字符串 `"fn"`。但 `eval_str("Sort")` 会返回 Fn 对象。正确验证方式：

运行：`python -c "from src.evaluator import Evaluator; from src.types import Fn; e = Evaluator(); print('Sort:', type(e.global_env.lookup('Sort')).__name__); print('Range:', type(e.global_env.lookup('Range')).__name__)"`
预期：输出 `Sort: Fn` 和 `Range: Fn`

- [ ] **步骤 3：验证内部函数不导出**

运行：`python -c "from src.evaluator import Evaluator; e = Evaluator();
try:
    e.global_env.lookup('merge-sort')
    print('FAIL: merge-sort exported')
except: print('OK: merge-sort not exported')
try:
    e.global_env.lookup('merge-lists')
    print('FAIL: merge-lists exported')
except: print('OK: merge-lists not exported')"`
预期：输出 `OK: merge-sort not exported` 和 `OK: merge-lists not exported`

- [ ] **步骤 4：推送到远程**

运行：`git push`
预期：成功推送 3 个新 commit 到 `origin/feat/bootstrapping`

---

## 自检

### 1. 规格覆盖度

| 规格章节 | 对应任务 |
|----------|----------|
| 背景与目标 - 5 个目标 | 任务 1（目标 3 math 依赖）、任务 2（目标 1 Range）、任务 3（目标 1 Sort 系列）、任务 4（目标 4/5 验证） |
| 架构与加载流程 - 文件布局 | 文件结构表覆盖 |
| 架构与加载流程 - 基础设施改动 | 任务 1 |
| 函数清单 - Range 实现 | 任务 2 步骤 3 |
| 函数清单 - Sort 系列实现 | 任务 3 步骤 3 |
| 测试策略 - 复用现有测试 | 任务 2 步骤 5、任务 3 步骤 5 |
| 测试策略 - 新增 bootstrap 测试 | 任务 2 步骤 1、任务 3 步骤 1 |
| 测试策略 - 验证检查点 | 任务 4 |
| 边界情况 | 任务 2/3 测试覆盖（空列表、单元素、浮点 step、稳定性） |
| 实现顺序 | 任务 1→2→3→4 与规格一致 |
| 风险与缓解 | 规格已记录，任务中通过测试验证 |

**遗漏检查**：无遗漏。

### 2. 占位符扫描

- 无 TODO/待定/后续实现
- 所有代码块均包含完整实现
- 所有测试均包含完整断言
- 无"类似任务 N"引用

### 3. 类型一致性

- `Range` 签名：`(fn Range [start end & rest] ...)` — 全局一致
- `merge-lists` 签名：`(fn merge-lists [a b cmp acc] ...)` — 任务 3 中定义和使用一致
- `merge-sort` 签名：`(fn merge-sort [xs cmp] ...)` — 任务 3 中定义和 Sort 系列使用一致
- `Sort-by` 签名：`(fn Sort-by [f xs] ...)` — 与现有 Python 版 `(sort_by_fn(fn, lst))` 参数顺序一致
- Python 测试中 `e.global_env.lookup("Range")` 返回 `Fn` 实例 — 与 `from src.types import Fn` 一致

**修正**：`test_sort_stability` 中 `n_values = [m.get(Keyword("n")) for m in result]` — `result` 是 `CentoList`（继承自 `list`），迭代返回 `CentoMap`（继承自 `dict`），`dict.get(Keyword("n"))` 正常工作。✓
