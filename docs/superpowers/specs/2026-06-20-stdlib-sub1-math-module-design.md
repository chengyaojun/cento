# 标准库扩展子项目 #1：std/math 模块设计规格

> 为 Cento 语言添加数学函数标准库模块，作为 4 子项目标准库扩展计划的第一步。

## 背景与上下文

Cento 语言当前有 5 个 std 模块（collection/string/io/fs/mutable），但缺少数学函数支持。本子项目是"先扩展后自举"策略下的首个标准库扩展工作。

### 4 子项目扩展计划

| 子项目 | 模块类别 | 状态 |
|--------|---------|------|
| **#1（本规格）** | math 数学 | 设计中 |
| #2 | sort+seq 排序与序列 | 待定 |
| #3 | string 字符串增强 | 待定 |
| #4 | 实用杂项（time/json/convert/os） | 待定 |

### 现有注册模式

- **核心内置**（小写命名）：`+` `-` `*` `/` `abs` `max` `min` `print` `count` 等，直接在 `evaluator.py` 的 `_register_builtins` 中定义
- **std 模块**（大写命名）：`Map` `Filter` `Split` `Join` 等，通过 `src/std/<module>.py` 的 `FUNCTIONS` 字典注册，在 evaluator 中循环 `define(name, fn, exported=True)`

本模块遵循 std 模块约定：大写命名、`FUNCTIONS` 字典、`exported=True` 注册。

## 设计

### 函数清单

**模块：** `src/std/math.py`（新文件）

**14 个函数 + 2 个常量：**

| 函数 | 签名 | 返回 | Python 后端 | 说明 |
|------|------|------|-------------|------|
| `Sin` | `(Sin x)` | number | `math.sin(x)` | 正弦（弧度） |
| `Cos` | `(Cos x)` | number | `math.cos(x)` | 余弦（弧度） |
| `Tan` | `(Tan x)` | number | `math.tan(x)` | 正切（弧度） |
| `Asin` | `(Asin x)` | number | `math.asin(x)` | 反正弦，x ∈ [-1, 1] |
| `Acos` | `(Acos x)` | number | `math.acos(x)` | 反余弦，x ∈ [-1, 1] |
| `Atan` | `(Atan x)` | number | `math.atan(x)` | 反正切 |
| `Exp` | `(Exp x)` | number | `math.exp(x)` | e 的 x 次方 |
| `Log` | `(Log x)` | number | `math.log(x)` | 自然对数（ln） |
| `Log10` | `(Log10 x)` | number | `math.log10(x)` | 常用对数（log10） |
| `Sqrt` | `(Sqrt x)` | number | `math.sqrt(x)` | 平方根，x ≥ 0 |
| `Pow` | `(Pow base exp)` | number | `math.pow(base, exp)` | 幂运算 |
| `Floor` | `(Floor x)` | number | `float(math.floor(x))` | 向下取整 |
| `Ceil` | `(Ceil x)` | number | `float(math.ceil(x))` | 向上取整 |
| `Round` | `(Round x)` | number | `float(round(x))` | 四舍五入（Python banker's rounding） |
| `Pi` | — | number（常量） | `math.pi` | 圆周率常量 |
| `E` | — | number（常量） | `math.e` | 自然常数 |

### 设计决策

1. **返回值统一为 float** — 与 Cento 的 number 类型（Python float）一致。`Floor`/`Ceil`/`Round` 也返回 float 而非 int（Cento 没有 int 类型区分），需用 `float()` 显式转换。

2. **错误处理自然传播** — 定义域错误（如 `(Sqrt -1)`、`(Log 0)`、`(Asin 2)`）抛 Python `ValueError`，被 `try/catch` 的 `except Exception` 捕获转为字符串。无需包装成 `CentoError`。

3. **常量是值不是函数** — `FUNCTIONS["Pi"] = math.pi`（一个 float 值），注册时 `define("Pi", 3.14159..., exported=True)` 正确工作，`define` 接受任意值。

4. **弧度制** — 三角函数输入为弧度，遵循 Python/Go 数学惯例，不提供度数版本（YAGNI）。

5. **不重复已有功能** — 不添加 `mod`（已有核心内置）、`abs`（已有）、`max`/`min`（已有）。

6. **`Pow` 两参数** — `math.pow(base, exp)`，与核心 `*` 不同，支持分数幂如 `(Pow 2 0.5)`。

### 放置位置

- **新文件：** `src/std/math.py` — 包含所有函数实现和 `FUNCTIONS` 字典
- **修改文件：** `src/evaluator.py` — 在 `_register_builtins` 的 `# std/fs` 块之后添加 `# std/math` 注册块
- **不修改：** `src/std/__init__.py`（保持原样）

### 注册方式

在 `src/evaluator.py` 的 `_register_builtins` 中，`# std/fs` 块之后添加：

```python
# std/math
from src.std.math import FUNCTIONS as MATH_FUNCTIONS
for name, fn in MATH_FUNCTIONS.items():
    self.global_env.define(name, fn, exported=True)
```

注册顺序遵循现有字母序模式：collection → mutable → string → io → fs → math。

## Python 实现

**新文件 `src/std/math.py`：**

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

# Rounding
def floor_fn(x):
    return float(math.floor(x))

def ceil_fn(x):
    return float(math.ceil(x))

def round_fn(x):
    return float(round(x))

# Constants
Pi = math.pi
E = math.e

FUNCTIONS = {
    # Trigonometric
    "Sin": sin_fn,
    "Cos": cos_fn,
    "Tan": tan_fn,
    "Asin": asin_fn,
    "Acos": acos_fn,
    "Atan": atan_fn,
    # Exponential and logarithmic
    "Exp": exp_fn,
    "Log": log_fn,
    "Log10": log10_fn,
    "Sqrt": sqrt_fn,
    "Pow": pow_fn,
    # Rounding
    "Floor": floor_fn,
    "Ceil": ceil_fn,
    "Round": round_fn,
    # Constants (values, not functions)
    "Pi": Pi,
    "E": E,
}
```

**修改 `src/evaluator.py` 的 `_register_builtins`：**

在 `# std/fs` 块之后添加：

```python
# std/math
from src.std.math import FUNCTIONS as MATH_FUNCTIONS
for name, fn in MATH_FUNCTIONS.items():
    self.global_env.define(name, fn, exported=True)
```

## 测试策略

### 单元测试 — 新文件 `tests/test_std_math.py`

按函数类别组织测试类：

- **TestTrigonometric：** `Sin`/`Cos`/`Tan`/`Asin`/`Acos`/`Atan` 的典型值验证（0、π/2、π/4 等）
- **TestExponentialLog：** `Exp`/`Log`/`Log10`/`Sqrt`/`Pow` 的正确性
- **TestRounding：** `Floor`/`Ceil`/`Round` 的正负数行为，验证返回 float 类型
- **TestConstants：** `Pi`/`E` 值正确注册
- **TestDomainErrors：** 定义域错误抛异常，且能被 `try/catch` 捕获

**关键测试决策：**
1. 用 `pytest.approx` 做浮点数比较
2. 测试常量直接 `eval_str("Pi")` 验证值注册
3. 测试 `Floor`/`Ceil`/`Round` 返回 float（`assert == 3.0` 而非 `== 3`）
4. 测试错误传播：`try/catch` 捕获 `ValueError`

### 集成测试 — 添加到 `tests/test_integration.py`

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

### 验证命令

```bash
pytest tests/test_std_math.py tests/test_integration.py -v
```

## 范围边界

**本子项目包含：**
- 新建 `src/std/math.py`（14 函数 + 2 常量）
- 修改 `src/evaluator.py`（注册块）
- 新建 `tests/test_std_math.py`（单元测试）
- 修改 `tests/test_integration.py`（1 个集成测试）

**本子项目不包含：**
- 双曲函数（`Sinh`/`Cosh`/`Tanh`）
- 特殊函数（`Gamma`/`Lgamma`）
- `Atan2`/`Hypot`/`Cbrt`/`Trunc`/`Copysign`
- 度数版本三角函数
- 自举工作（推迟到 4 子项目扩展完成后）
- 其他 3 个标准库扩展子项目（sort+seq、string 增强、实用杂项）

## 后续步骤

本子项目完成后，进入子项目 #2（sort+seq 排序与序列），独立设计/计划/实现周期。
