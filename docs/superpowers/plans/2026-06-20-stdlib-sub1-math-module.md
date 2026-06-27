# std/math 模块实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为 Cento 语言添加 std/math 标准库模块，提供 14 个数学函数和 2 个常量。

**架构：** 新建 `src/std/math.py` 文件，包含函数实现和 `FUNCTIONS` 字典；修改 `src/evaluator.py` 注册模块；新建 `tests/test_std_math.py` 单元测试；修改 `tests/test_integration.py` 添加集成测试。遵循现有 std 模块注册模式（大写命名、`FUNCTIONS` 字典、`exported=True`）。

**技术栈：** Python `math` 标准库、pytest 测试框架

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `src/std/math.py` | 创建 | 14 个数学函数实现 + 2 个常量 + `FUNCTIONS` 字典 |
| `src/evaluator.py` | 修改 | 在 `_register_builtins` 中添加 `# std/math` 注册块 |
| `tests/test_std_math.py` | 创建 | 单元测试（按函数类别组织测试类） |
| `tests/test_integration.py` | 修改 | 添加 1 个集成测试（勾股定理） |

---

### 任务 1：创建 math 模块骨架与三角函数

**文件：**
- 创建：`src/std/math.py`
- 创建：`tests/test_std_math.py`

- [ ] **步骤 1：编写失败的测试**

创建 `tests/test_std_math.py`：

```python
import math
import pytest
from src.evaluator import eval_str


class TestTrigonometric:
    def test_sin(self):
        assert eval_str("(Sin 0)") == pytest.approx(0.0)
        assert eval_str("(Sin 1.5707963267948966)") == pytest.approx(1.0)  # pi/2

    def test_cos(self):
        assert eval_str("(Cos 0)") == pytest.approx(1.0)
        assert eval_str("(Cos 3.141592653589793)") == pytest.approx(-1.0)  # pi

    def test_tan(self):
        assert eval_str("(Tan 0)") == pytest.approx(0.0)

    def test_asin_acos_atan(self):
        assert eval_str("(Asin 1)") == pytest.approx(math.pi / 2)
        assert eval_str("(Acos 1)") == pytest.approx(0.0)
        assert eval_str("(Atan 1)") == pytest.approx(math.pi / 4)
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_std_math.py -v`
预期：FAIL，报错 `CentoError: Sin not defined`（函数尚未注册）

- [ ] **步骤 3：创建 math 模块文件并实现三角函数**

创建 `src/std/math.py`：

```python
"""Cento standard math library - mathematical functions and constants."""

import math

# Trigonometric functions
def sin_fn(x):
    return math.sin(x)

def cos_fn(x):
    return math.cos(x)

def tan_fn(x):
    return math.tan(x)

def asin_fn(x):
    return math.asin(x)

def acos_fn(x):
    return math.acos(x)

def atan_fn(x):
    return math.atan(x)

FUNCTIONS = {
    # Trigonometric
    "Sin": sin_fn,
    "Cos": cos_fn,
    "Tan": tan_fn,
    "Asin": asin_fn,
    "Acos": acos_fn,
    "Atan": atan_fn,
}
```

- [ ] **步骤 4：在 evaluator 中注册 math 模块**

修改 `src/evaluator.py`，在 `_register_builtins` 方法中找到 `# std/fs` 块之后，添加：

```python
        # std/math
        from src.std.math import FUNCTIONS as MATH_FUNCTIONS
        for name, fn in MATH_FUNCTIONS.items():
            self.global_env.define(name, fn, exported=True)
```

- [ ] **步骤 5：运行测试验证通过**

运行：`pytest tests/test_std_math.py -v`
预期：PASS（4 个测试通过）

- [ ] **步骤 6：Commit**

```bash
git add src/std/math.py src/evaluator.py tests/test_std_math.py
git commit -m "feat(math): 添加三角函数 Sin/Cos/Tan/Asin/Acos/Atan"
```

---

### 任务 2：添加指数对数函数

**文件：**
- 修改：`src/std/math.py`
- 修改：`tests/test_std_math.py`

- [ ] **步骤 1：编写失败的测试**

在 `tests/test_std_math.py` 末尾追加：

```python
class TestExponentialLog:
    def test_exp(self):
        assert eval_str("(Exp 0)") == pytest.approx(1.0)
        assert eval_str("(Exp 1)") == pytest.approx(math.e)

    def test_log(self):
        assert eval_str("(Log 1)") == pytest.approx(0.0)  # ln(1) = 0
        assert eval_str("(Log 2.718281828459045)") == pytest.approx(1.0)  # ln(e)

    def test_log10(self):
        assert eval_str("(Log10 100)") == pytest.approx(2.0)
        assert eval_str("(Log10 1000)") == pytest.approx(3.0)

    def test_sqrt(self):
        assert eval_str("(Sqrt 4)") == pytest.approx(2.0)
        assert eval_str("(Sqrt 2)") == pytest.approx(math.sqrt(2))

    def test_pow(self):
        assert eval_str("(Pow 2 3)") == pytest.approx(8.0)
        assert eval_str("(Pow 9 0.5)") == pytest.approx(3.0)
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_std_math.py::TestExponentialLog -v`
预期：FAIL，报错 `CentoError: Exp not defined`

- [ ] **步骤 3：实现指数对数函数**

在 `src/std/math.py` 的三角函数定义之后、`FUNCTIONS` 字典之前添加：

```python
# Exponential and logarithmic
def exp_fn(x):
    return math.exp(x)

def log_fn(x):
    return math.log(x)  # natural logarithm

def log10_fn(x):
    return math.log10(x)

def sqrt_fn(x):
    return math.sqrt(x)

def pow_fn(base, exp):
    return math.pow(base, exp)
```

在 `FUNCTIONS` 字典中，在 `# Trigonometric` 块之后添加：

```python
    # Exponential and logarithmic
    "Exp": exp_fn,
    "Log": log_fn,
    "Log10": log10_fn,
    "Sqrt": sqrt_fn,
    "Pow": pow_fn,
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_std_math.py::TestExponentialLog -v`
预期：PASS（5 个测试通过）

- [ ] **步骤 5：Commit**

```bash
git add src/std/math.py tests/test_std_math.py
git commit -m "feat(math): 添加指数对数函数 Exp/Log/Log10/Sqrt/Pow"
```

---

### 任务 3：添加取整函数

**文件：**
- 修改：`src/std/math.py`
- 修改：`tests/test_std_math.py`

- [ ] **步骤 1：编写失败的测试**

在 `tests/test_std_math.py` 末尾追加：

```python
class TestRounding:
    def test_floor(self):
        assert eval_str("(Floor 3.7)") == 3.0
        assert eval_str("(Floor -1.5)") == -2.0

    def test_ceil(self):
        assert eval_str("(Ceil 3.2)") == 4.0
        assert eval_str("(Ceil -1.5)") == -1.0

    def test_round(self):
        assert eval_str("(Round 3.4)") == 3.0
        assert eval_str("(Round 3.5)") == 4.0
        assert eval_str("(Round 2.5)") == 2.0  # Python banker's rounding

    def test_floor_returns_float(self):
        result = eval_str("(Floor 3.7)")
        assert isinstance(result, float)

    def test_ceil_returns_float(self):
        result = eval_str("(Ceil 3.2)")
        assert isinstance(result, float)
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_std_math.py::TestRounding -v`
预期：FAIL，报错 `CentoError: Floor not defined`

- [ ] **步骤 3：实现取整函数**

在 `src/std/math.py` 的指数对数函数之后、`FUNCTIONS` 字典之前添加：

```python
# Rounding
def floor_fn(x):
    return float(math.floor(x))

def ceil_fn(x):
    return float(math.ceil(x))

def round_fn(x):
    return float(round(x))
```

在 `FUNCTIONS` 字典中，在 `# Exponential and logarithmic` 块之后添加：

```python
    # Rounding
    "Floor": floor_fn,
    "Ceil": ceil_fn,
    "Round": round_fn,
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_std_math.py::TestRounding -v`
预期：PASS（4 个测试通过）

- [ ] **步骤 5：Commit**

```bash
git add src/std/math.py tests/test_std_math.py
git commit -m "feat(math): 添加取整函数 Floor/Ceil/Round"
```

---

### 任务 4：添加常量与错误处理测试

**文件：**
- 修改：`src/std/math.py`
- 修改：`tests/test_std_math.py`

- [ ] **步骤 1：编写失败的测试**

在 `tests/test_std_math.py` 末尾追加：

```python
class TestConstants:
    def test_pi(self):
        assert eval_str("Pi") == pytest.approx(math.pi)

    def test_e(self):
        assert eval_str("E") == pytest.approx(math.e)


class TestDomainErrors:
    def test_sqrt_negative(self):
        with pytest.raises(Exception):
            eval_str("(Sqrt -1)")

    def test_log_zero(self):
        with pytest.raises(Exception):
            eval_str("(Log 0)")

    def test_asin_out_of_range(self):
        with pytest.raises(Exception):
            eval_str("(Asin 2)")

    def test_error_caught_by_try(self):
        result = eval_str('''
            (try
              (Sqrt -1)
              (catch [msg] (str "caught: " msg)))
        ''')
        assert "caught" in result
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_std_math.py::TestConstants tests/test_std_math.py::TestDomainErrors -v`
预期：FAIL，`TestConstants` 报错 `CentoError: Pi not defined`；`TestDomainErrors` 中的错误处理测试可能通过（因为未注册的函数也会抛异常）

- [ ] **步骤 3：添加常量到 math 模块**

在 `src/std/math.py` 的取整函数之后、`FUNCTIONS` 字典之前添加：

```python
# Constants
Pi = math.pi
E = math.e
```

在 `FUNCTIONS` 字典中，在 `# Rounding` 块之后添加：

```python
    # Constants (values, not functions)
    "Pi": Pi,
    "E": E,
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_std_math.py::TestConstants tests/test_std_math.py::TestDomainErrors -v`
预期：PASS（5 个测试通过）

- [ ] **步骤 5：Commit**

```bash
git add src/std/math.py tests/test_std_math.py
git commit -m "feat(math): 添加常量 Pi/E 和错误处理测试"
```

---

### 任务 5：添加集成测试

**文件：**
- 修改：`tests/test_integration.py`

- [ ] **步骤 1：编写集成测试**

先读取 `tests/test_integration.py` 确认顶部导入包含 `pytest`，若无则添加。

在 `tests/test_integration.py` 末尾追加：

```python
def test_math_combination():
    """验证数学函数组合使用：计算勾股定理。"""
    result = eval_str('''
        (let [a 3.0
              b 4.0]
          (Sqrt (+ (Pow a 2) (Pow b 2))))
    ''')
    # 3² + 4² = 9 + 16 = 25, √25 = 5
    assert result == pytest.approx(5.0)
```

- [ ] **步骤 2：运行测试验证通过**

运行：`pytest tests/test_integration.py::test_math_combination -v`
预期：PASS（所有函数已在前序任务实现）

- [ ] **步骤 3：Commit**

```bash
git add tests/test_integration.py
git commit -m "test(integration): 添加 math 模块勾股定理集成测试"
```

---

### 任务 6：最终验证

**文件：** 无修改

- [ ] **步骤 1：运行完整测试套件**

运行：`pytest -v`
预期：全部通过（原有 129 个 + 新增约 18 个 = 约 147 个测试，0 失败）

- [ ] **步骤 2：验证无回归**

确认原有测试全部通过，无回归。

- [ ] **步骤 3：最终 Commit（如有）**

如果之前的 commit 因沙箱问题未持久化，统一提交：

```bash
git add src/std/math.py src/evaluator.py tests/test_std_math.py tests/test_integration.py
git commit -m "feat(math): 完成 std/math 模块实现"
```

---

## 自检清单

### 规格覆盖度

| 规格需求 | 对应任务 |
|----------|---------|
| 三角函数 Sin/Cos/Tan/Asin/Acos/Atan | 任务 1 |
| 指数对数 Exp/Log/Log10/Sqrt/Pow | 任务 2 |
| 取整 Floor/Ceil/Round | 任务 3 |
| 常量 Pi/E | 任务 4 |
| 错误处理测试 | 任务 4 |
| 集成测试（勾股定理） | 任务 5 |
| 最终验证 | 任务 6 |

### 占位符扫描

无 TODO/待定。所有步骤包含完整代码。

### 类型一致性

- `FUNCTIONS` 字典在任务 1 创建，任务 2-4 逐步扩展
- 函数命名一致：`sin_fn`/`cos_fn`/`exp_fn`/`floor_fn` 等
- 常量命名一致：`Pi`/`E`（值，非函数）
- 注册方式一致：所有任务通过 evaluator 的 `for name, fn in MATH_FUNCTIONS.items()` 循环注册
