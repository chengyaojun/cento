# 标准库自举实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 用 Cento 语言自身实现 util 和 seq 模块中的 18 个纯逻辑函数，建立 Cento 优先 + Python fallback 的加载机制。

**架构：** 新增 `src/std/util.ct` 和 `src/std/seq.ct` 两个 Cento 源文件；修改 evaluator 的 util/seq 注册段，先尝试加载 .ct 实现，失败则 fallback 到 Python；util.py 和 seq.py 保留为 fallback 源。

**技术栈：** Cento 语言（S-expression 语法、let/fn/if/递归/TCO）、Python（解释器、fallback）、pytest

---

## 文件结构

| 文件 | 职责 | 操作 |
|------|------|------|
| `src/std/util.ct` | Cento 实现 9 个 util 函数 | 新建 |
| `src/std/seq.ct` | Cento 实现 9 个 seq 函数 | 新建 |
| `src/evaluator.py` | 新增 `_load_cent_module`，修改 util/seq 注册段 | 修改 |
| `tests/test_bootstrap.py` | 验证自举加载机制 | 新建 |
| `src/std/util.py` | Python fallback（保留现有 4 个不可自举函数） | 保留 |
| `src/std/seq.py` | Python fallback（保留现有 4 个不可自举函数） | 保留 |
| `tests/test_std_util.py` | 复用现有测试验证 Cento 实现 | 保留 |
| `tests/test_std_seq.py` | 复用现有测试验证 Cento 实现 | 保留 |

---

### 任务 1：创建 util.ct - 单参数纯逻辑函数

**文件：**
- 创建：`src/std/util.ct`

- [ ] **步骤 1：编写 util.ct**

```lisp
; util.ct - Cento 自举实现（9 个纯逻辑函数）

(fn Identity [x] x)

(fn Inc [x] (+ x 1))

(fn Dec [x] (- x 1))

(fn Even? [x] (= (mod x 2) 0))

(fn Odd? [x] (!= (mod x 2) 0))

(fn Zero? [x] (= x 0))

(fn Pos? [x] (> x 0))

(fn Neg? [x] (< x 0))

(fn Complement [f] (fn [x] (not (f x))))
```

- [ ] **步骤 2：验证 .ct 文件可独立执行**

运行：
```bash
python -c "from src.lexer import Lexer; from src.parser import Parser; from src.evaluator import Evaluator; src = open('src/std/util.ct').read(); ast = Parser(Lexer(src).tokenize()).parse(); e = Evaluator(); [e.evaluate(x) for x in ast.expressions]; print(e.global_env.lookup('Inc')(5))"
```
预期：输出 `6.0`

- [ ] **步骤 3：Commit**

```bash
git add src/std/util.ct
git commit -m "feat(bootstrap): 添加 util.ct 自举实现"
```

---

### 任务 2：创建 seq.ct - 序列操作函数

**文件：**
- 创建：`src/std/seq.ct`

- [ ] **步骤 1：编写 seq.ct**

```lisp
; seq.ct - Cento 自举实现（9 个序列操作函数）
; 依赖内置：first, rest, empty?, count, Concat, Contains, error, list?

(fn Take [n xs]
  (if (or (= n 0) (empty? xs))
    []
    (Concat [(first xs)] (Take (- n 1) (rest xs)))))

(fn Drop [n xs]
  (if (or (= n 0) (empty? xs))
    xs
    (Drop (- n 1) (rest xs))))

(fn Nth [xs i]
  (if (empty? xs)
    (error "Nth index out of range")
    (if (= i 0)
      (first xs)
      (Nth (rest xs) (- i 1)))))

(fn Last [xs]
  (if (empty? xs)
    (error "Last of empty list")
    (if (empty? (rest xs))
      (first xs)
      (Last (rest xs)))))

(fn Range-helper [current end step]
  (if (>= current end)
    []
    (Concat [current] (Range-helper (+ current step) end step))))

(fn Range [start end step]
  (Range-helper start end step))

(fn Distinct [xs]
  (if (empty? xs)
    []
    (let [head (first xs)
          tail (rest xs)]
      (if (Contains tail head)
        (Distinct tail)
        (Concat [head] (Distinct tail))))))

(fn Flatten [xs]
  (if (empty? xs)
    []
    (let [head (first xs)
          tail (rest xs)]
      (if (list? head)
        (Concat (Flatten head) (Flatten tail))
        (Concat [head] (Flatten tail))))))

(fn Zip [xs ys]
  (if (or (empty? xs) (empty? ys))
    []
    (Concat [(Concat [(first xs)] [(first ys)])] (Zip (rest xs) (rest ys)))))

(fn Reverse-helper [xs acc]
  (if (empty? xs)
    acc
    (Reverse-helper (rest xs) (Concat [(first xs)] acc))))

(fn Reverse [xs]
  (Reverse-helper xs []))
```

- [ ] **步骤 2：验证 .ct 文件可独立执行**

运行：
```bash
python -c "from src.lexer import Lexer; from src.parser import Parser; from src.evaluator import Evaluator; src = open('src/std/seq.ct').read(); ast = Parser(Lexer(src).tokenize()).parse(); e = Evaluator(); [e.evaluate(x) for x in ast.expressions]; print(e.global_env.lookup('Take')(2, [1.0, 2.0, 3.0]))"
```
预期：输出 `[1.0, 2.0]`（CentoList）

- [ ] **步骤 3：Commit**

```bash
git add src/std/seq.ct
git commit -m "feat(bootstrap): 添加 seq.ct 自举实现"
```

---

### 任务 3：修改 evaluator - 实现 _load_cent_module 加载逻辑

**文件：**
- 修改：`src/evaluator.py`

- [ ] **步骤 1：编写 _load_cent_module 辅助方法**

在 `_register_builtins` 方法之后，添加 `_load_cent_module` 方法：

```python
def _load_cent_module(self, module_name):
    """加载 Cento 源文件实现的标准库模块。
    返回 {name: callable} 字典。失败时抛异常由调用方 fallback。
    """
    import os
    from src.lexer import Lexer
    from src.parser import Parser

    ct_path = os.path.join(os.path.dirname(__file__), "std", f"{module_name}.ct")
    if not os.path.exists(ct_path):
        raise FileNotFoundError(f"No .ct file: {ct_path}")

    with open(ct_path, "r", encoding="utf-8") as f:
        source = f.read()

    tokens = Lexer(source).tokenize()
    ast = Parser(tokens).parse()

    # 使用独立 evaluator 避免污染当前 global_env
    sub_evaluator = Evaluator()
    for expr in ast.expressions:
        sub_evaluator.evaluate(expr)

    exports = {}
    for name, value in sub_evaluator.global_env.bindings.items():
        if name and name[0].isupper():
            exports[name] = value
    return exports
```

- [ ] **步骤 2：修改 util 注册段为 Cento 优先 + Python fallback**

将 evaluator.py 中 util 注册段：

```python
# std/util
from src.std.util import FUNCTIONS as UTIL_FUNCTIONS
for name, fn in UTIL_FUNCTIONS.items():
    self.global_env.define(name, fn, exported=True)
```

替换为：

```python
# std/util (Cento 优先，Python fallback)
try:
    util_exports = self._load_cent_module("util")
    # Cento 实现的函数直接注册
    for name, fn in util_exports.items():
        self.global_env.define(name, fn, exported=True)
    # 补齐 Cento 未实现的函数（从 Python fallback）
    from src.std.util import FUNCTIONS as UTIL_FUNCTIONS
    for name, fn in UTIL_FUNCTIONS.items():
        if name not in util_exports:
            self.global_env.define(name, fn, exported=True)
except Exception as e:
    import sys
    print(f"[bootstrap] util.ct 加载失败，使用 Python fallback: {e}", file=sys.stderr)
    from src.std.util import FUNCTIONS as UTIL_FUNCTIONS
    for name, fn in UTIL_FUNCTIONS.items():
        self.global_env.define(name, fn, exported=True)
```

- [ ] **步骤 3：修改 seq 注册段为 Cento 优先 + Python fallback**

将 evaluator.py 中 seq 注册段：

```python
# std/seq
from src.std.seq import FUNCTIONS as SEQ_FUNCTIONS
for name, fn in SEQ_FUNCTIONS.items():
    self.global_env.define(name, fn, exported=True)
```

替换为：

```python
# std/seq (Cento 优先，Python fallback)
try:
    seq_exports = self._load_cent_module("seq")
    for name, fn in seq_exports.items():
        self.global_env.define(name, fn, exported=True)
    from src.std.seq import FUNCTIONS as SEQ_FUNCTIONS
    for name, fn in SEQ_FUNCTIONS.items():
        if name not in seq_exports:
            self.global_env.define(name, fn, exported=True)
except Exception as e:
    import sys
    print(f"[bootstrap] seq.ct 加载失败，使用 Python fallback: {e}", file=sys.stderr)
    from src.std.seq import FUNCTIONS as SEQ_FUNCTIONS
    for name, fn in SEQ_FUNCTIONS.items():
        self.global_env.define(name, fn, exported=True)
```

- [ ] **步骤 4：运行现有测试验证零回归**

运行：`pytest tests/test_std_util.py tests/test_std_seq.py -v`
预期：58 个测试全 PASS

- [ ] **步骤 5：运行全套测试验证零回归**

运行：`pytest`
预期：214 个测试全 PASS

- [ ] **步骤 6：Commit**

```bash
git add src/evaluator.py
git commit -m "feat(bootstrap): evaluator 实现 Cento 优先加载 + Python fallback"
```

---

### 任务 4：新增 bootstrap 专项测试

**文件：**
- 创建：`tests/test_bootstrap.py`

- [ ] **步骤 1：编写 bootstrap 测试（RED）**

```python
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
        result = eval_str("""
            (let [le5 (Complement (fn [x] (> x 5)))]
              (le5 3))
        """)
        assert result is True


class TestFallbackOnCtError:
    def test_fallback_to_python(self):
        """构造 .ct 缺失场景（通过模拟）验证 fallback 机制。
        由于 .ct 文件存在，此测试通过直接调用 _load_cent_module
        传入不存在的模块名验证异常处理。"""
        e = Evaluator()
        with pytest.raises(Exception):
            e._load_cent_module("nonexistent-module")


class TestMixedImplementation:
    def test_util_has_both_ct_and_python(self):
        """util 模块同时有 Cento（Inc）和 Python（Comp）函数，验证协同工作"""
        # Inc 来自 util.ct
        assert eval_str("(Inc 0)") == 1.0
        # Comp 来自 util.py（Python 原生，因可变参数未自举）
        result = eval_str("""
            (let [f (Comp Inc Inc)]
              (f 5))
        """)
        assert result == 7.0

    def test_seq_has_both_ct_and_python(self):
        """seq 模块同时有 Cento（Take）和 Python（Sort）函数，验证协同工作"""
        # Take 来自 seq.ct
        assert list(eval_str("(Take 2 [3 1 2])")) == [3.0, 1.0]
        # Sort 来自 seq.py（Python 原生，因依赖 Timsort）
        assert list(eval_str("(Sort [3 1 2])")) == [1.0, 2.0, 3.0]
        # 组合：先排序再取前 2 个
        assert list(eval_str("(Take 2 (Sort [3 1 2]))")) == [1.0, 2.0]
```

- [ ] **步骤 2：运行测试验证通过（GREEN）**

运行：`pytest tests/test_bootstrap.py -v`
预期：7 个测试全 PASS

- [ ] **步骤 3：运行全套测试验证零回归**

运行：`pytest`
预期：221 个测试全 PASS（214 + 7 新增）

- [ ] **步骤 4：Commit**

```bash
git add tests/test_bootstrap.py
git commit -m "test(bootstrap): 添加自举加载机制专项测试"
```

---

### 任务 5：最终验证与推送

- [ ] **步骤 1：运行完整测试套件**

运行：`pytest -v`
预期：221 个测试全 PASS

- [ ] **步骤 2：手动验证自举效果**

运行：
```bash
python -c "from src.evaluator import Evaluator; e = Evaluator(); print(type(e.global_env.lookup('Inc')))"
```
预期：输出 `<class 'src.evaluator.Fn'>`（Cento 的 Fn 对象，证明来自 .ct）

对比：
```bash
python -c "from src.evaluator import Evaluator; e = Evaluator(); print(type(e.global_env.lookup('Comp')))"
```
预期：输出 `<class 'function'>`（Python 原生 function，证明来自 .py）

- [ ] **步骤 3：推送**

```bash
git push
```

---

## 自检结果

**1. 规格覆盖度：**
- util.ct 9 个函数 → 任务 1 ✓
- seq.ct 9 个函数 → 任务 2 ✓
- _load_cent_module + evaluator 注册修改 → 任务 3 ✓
- bootstrap 测试 → 任务 4 ✓
- 最终验证 → 任务 5 ✓

**2. 占位符扫描：** 无 TODO/待定，所有代码步骤含完整代码。

**3. 类型一致性：** `_load_cent_module` 方法名在任务 3 定义并在任务 4 测试中一致使用；util_exports/seq_exports 变量名一致。
