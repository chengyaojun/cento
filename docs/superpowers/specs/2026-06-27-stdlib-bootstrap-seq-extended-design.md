# 标准库自举扩展 - seq 剩余函数设计规格

> 用 Cento 语言重新实现 seq 模块中剩余的 5 个函数（Range + Sort 系列），延续标准库自举工作，利用已完成的 `& rest` 可变参数支持解锁 Range，并验证归并排序在 Cento 中的可行性。

## 背景与目标

### 当前状态
- 已完成 util.ct（10 函数）、seq.ct（9 函数）、collection.ct（5 函数）的自举
- `_load_cent_module` 加载机制稳定，支持 Cento 优先 + Python fallback
- 子 evaluator 注入 collection 模块作为依赖
- `& rest` 可变参数支持已完成（commit `e6a0f73`），解锁 Range 可选 step
- 现有 235 个测试全绿

### 目标
1. 用 Cento 语言重新实现 seq 模块中剩余 5 个函数：Range/Sort/Sort-desc/Sort-by/Sort-by-desc
2. 引入归并排序实现，复用现有 seq.ct 函数（Take/Drop/Count）与 collection（Concat）
3. 扩展 `_load_cent_module` 注册 math 模块依赖（提供 Floor）
4. 零回归：现有 235 个测试全绿
5. 新增 bootstrap 测试验证 Cento 实现来源与边界行为

### 非目标
- 不优化 `merge-lists` 性能（YAGNI，学习语言场景可接受 O(n²) 合并）
- 不扩展 `cond` 语法（用嵌套 `if` 替代）
- 不实现 `quot`/`int` 内置（用 `Floor` 替代）
- 不自举其他模块（本轮聚焦 seq 剩余 5 个函数）
- 不修改现有 9 个 seq.ct 函数
- 不自 util/collection 等其他模块

## 架构与加载流程

### 文件布局
```
src/std/
  seq.py    # 保留为 Python fallback（全部 13 个函数保留，作为 .ct 加载失败时的兜底）
  seq.ct    # 扩展：新增 Range + Sort/Sort-desc/Sort-by/Sort-by-desc + merge-sort/merge-lists 内部辅助
```

### 加载流程
复用 util/seq/collection 已建立的机制：
1. evaluator 的 seq 注册段调用 `_load_cent_module("seq")`
2. 成功 → Cento 实现注册到 global_env
3. Python fallback 补齐未自举的函数（本轮后 seq.py 全部 13 个函数都有 Cento 实现，但仍保留作为 fallback 兜底）
4. 失败 → 全部用 Python fallback

### seq.ct 依赖
- **内置**：`first`/`rest`/`empty?`/`count`/`<=`/`>=`/`/`/`if`/`let`/`fn`/`& rest`
- **collection 原生函数**：`Concat`（用于构造列表）
- **math 模块**：`Floor`（用于归并排序中点计算）

### 基础设施改动（_load_cent_module）
当前 `_load_cent_module` 只注册 collection 作为子 evaluator 依赖。需扩展同时注册 math：

```python
sub_evaluator = Evaluator(skip_std=True)
from src.std.collection import FUNCTIONS as COLLECTION_FUNCTIONS
for name, fn in COLLECTION_FUNCTIONS.items():
    sub_evaluator.global_env.define(name, fn, exported=True)
# 新增：注册 math 模块（Floor 等基础数学函数）
from src.std.math import FUNCTIONS as MATH_FUNCTIONS
for name, fn in MATH_FUNCTIONS.items():
    sub_evaluator.global_env.define(name, fn, exported=True)
```

**理由**：
- 改动小（3 行）
- 通用：未来其他 .ct 模块也能使用 math 函数
- merge-sort 实现更自然（用 Floor 计算中点，避免引入交替拆分等隐晦逻辑）

## 函数清单与实现策略

### 新增公开函数（5 个）

#### Range
```lisp
(fn Range-helper [current end step acc]
  (if (>= current end)
    acc
    (Range-helper (+ current step) end step (Concat acc [current]))))

(fn Range [start end & rest]
  (let [step (if (empty? rest) 1 (first rest))]
    (Range-helper start end step [])))
```

**关键点**：
- `& rest` 接收可选 step，默认为 1
- 累加器 `acc` 递归，TCO 友好
- 终止条件 `current >= end`，正确处理 `Range 5 3` 返回 `[]`
- 浮点 step 自然支持（`(+ current step)` 对 float 正常工作）
- 与 Python 版差异：Python 用 `int()` 截断参数，Cento 版保留浮点；现有测试用例均通过

#### Sort 系列
```lisp
; 内部：合并两个已排序的列表（累加器式，TCO 友好）
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

; 公开 API
(fn Sort [xs] (merge-sort xs <=))
(fn Sort-desc [xs] (merge-sort xs >=))
(fn Sort-by [f xs] (merge-sort xs (fn [a b] (<= (f a) (f b)))))
(fn Sort-by-desc [f xs] (merge-sort xs (fn [a b] (>= (f a) (f b)))))
```

**关键决策**：
- `merge-lists` 用 `cmp` 谓词而非硬编码 `<=`，统一支持 4 个 Sort 变体
- 稳定性：当 `cmp` 为真时取 `a`（左侧），保留原顺序 → 稳定排序，与 Python Timsort 行为一致
- 中点用 `(Floor (/ (count xs) 2))` 计算，返回 float（如 `2.0`），但 `Take`/`Drop` 用 `(- n 1)` 递减对 float 正常工作

### 新增内部函数（2 个，小写开头不导出）
- `merge-lists` — 合并两个已排序列表
- `merge-sort` — 归并排序主递归

### 保留原生（0 个）
seq 模块全部 13 个函数本轮后均完成自举。seq.py 仍保留作为 .ct 加载失败时的 fallback 兜底。

## 测试策略

### 复用现有测试（零修改）
- `tests/test_std_seq.py` 中：
  - `TestSort`（4 个测试）：sort_asc/sort_empty/sort_sorted/sort_desc
  - `TestSortBy`（2 个测试）：sort_by_key/sort_by_desc
  - `TestRange`（3 个测试）：range_basic/range_with_step/range_empty
- 共 9 个测试自动验证 Cento 实现的行为与 Python 版一致

### 新增 bootstrap 专项测试
在 `tests/test_bootstrap.py` 添加 `TestSeqExtendedBootstrap` 类：
- `test_range_from_ct` — 验证 Range 来自 seq.ct，支持 2/3 参数
- `test_range_float_step` — 浮点 step（如 `(Range 0 1 0.25)` → `[0 0.25 0.5 0.75]`）
- `test_sort_from_ct` — 验证 Sort 来自 seq.ct
- `test_sort_stability` — 稳定性验证（相同 key 元素保持原序）
- `test_sort_by_from_ct` — 验证 Sort-by 来自 seq.ct
- `test_merge_sort_internal_not_exported` — 验证 `merge-sort`/`merge-lists` 不被导出（小写开头）

### 验证检查点
1. 修改 `_load_cent_module` 后，现有 235 个测试全绿（零回归）
2. 新增 bootstrap 测试全绿
3. 手动验证：`(type Sort)` 应为 `Fn`（Cento 实现），而非 `function`

## 边界情况

| 场景 | 期望行为 | 实现保证 |
|------|----------|----------|
| `(Sort [])` | `[]` | `merge-sort` 命中 `(<= (count xs) 1)` 返回 `xs` |
| `(Sort [42])` | `[42]` | 同上 |
| `(Range 5 3)` | `[]` | `Range-helper` 首次 `current >= end` 即返回 `acc=[]` |
| `(Range 0 3)` | `[0 1 2]` | 递归 3 次后 `current=3 >= end=3` 终止 |
| `(Range 0 1 0.25)` | `[0 0.25 0.5 0.75]` | 浮点递增，4 次后 `current=1.0 >= end=1` 终止 |
| `(Sort [3 1 2])` | `[1 2 3]` | 归并排序 |
| `(Sort [1 1 1])` | `[1 1 1]` | 稳定，cmp 真时取左 |
| `(Sort-by f xs)` 等长 key | 保持原序 | 稳定排序保证 |
| `(merge-sort)` 内部调用 | 不污染 global_env | 小写开头不导出 |

### 已知行为差异（可接受）

| 场景 | Python 版 | Cento 版 | 影响 |
|------|-----------|----------|------|
| `(Range 0 3.5)` | `[0 1 2 3]`（int 截断） | `[0 1 2 3]`（float 比较，自然终止） | 无差异 |
| `(Range 0 6 2)` | `[0 2 4]` | `[0 2 4]` | 无差异 |
| `(Range 0 1 0.3)` | Python `range(0,1,0)` 报错 | `[0 0.3 0.6 0.9]` | **行为改进**，Python 版本不支持浮点 step |

## 实现顺序

1. **修改 `_load_cent_module`**（`src/evaluator.py`）— 在子 evaluator 中额外注册 math 模块依赖
2. **扩展 `seq.ct`** — 新增 Range + Sort 系列 5 个公开函数 + 2 个内部辅助（merge-lists/merge-sort）
3. **更新 `tests/test_bootstrap.py`** — 添加 `TestSeqExtendedBootstrap` 测试类
4. **运行全套测试验证** — 235 + 新增测试全绿
5. **手动验证 + 推送**

## 风险与缓解

### 风险 1：`merge-lists` 性能
- 影响：每次 `Concat acc [x]` 构造新列表，单次合并实际为 O(n²)
- 缓解：学习语言场景可接受；如未来需优化，可引入 `conj`/`prepend` 原语后改用 `cons` + `Reverse` 模式
- 决策：暂不优化，YAGNI

### 风险 2：稳定性语义
- 影响：稳定性要求 cmp 为真时取左侧（`a`）。当前 `merge-lists` 实现 `(if (cmp (first a) (first b)) (取 a) (取 b))` 符合此要求
- 缓解：测试 `test_sort_stability` 显式验证

### 风险 3：`Floor` 依赖注册
- 影响：若 `_load_cent_module` 未注册 math，seq.ct 加载失败 → fallback 到 Python 原生 seq.py
- 缓解：步骤 1 先修改并运行测试验证 math 已注册；fallback 机制保证即使失败也不阻断

### 风险 4：`Take`/`Drop` 接收 float 参数
- 影响：`(Take 2.0 xs)` 在 seq.ct 实现中：`(= 2.0 0)` 为 false，`(- 2.0 1)` = 1.0，再递归 `(= 1.0 0)` false，`(- 1.0 1)` = 0.0，再 `(= 0.0 0)` true 终止。行为正确
- 缓解：已分析确认，无需额外处理

### 风险 5：现有 Sort 测试断言 list 类型
- 影响：`test_sort_asc` 等用 `list(eval_str(...))` 断言，Cento 实现返回 CentoList，`list()` 转换正常
- 缓解：复用现有测试自动验证
