# 子项目 #1：增强 Cento 语言能力（自举前置）

> 为 Cento 完整自举的第 1 个子项目：添加编写解释器（lexer/parser/evaluator）严格必需的语言原语。

## 背景与上下文

Cento 是一门以学习与娱乐为目的的函数式编程语言，采用 S-expression 语法、树遍历解释器实现，当前完全用 Python 实现。

**完整自举**的目标是让 Cento 用 Cento 自身实现（lexer/parser/evaluator 都用 Cento 编写），Python 仅作为最小宿主/引导器。这是一个大型项目，已分解为 6 个子项目：

| # | 子项目 | 依赖 | 里程碑 |
|---|--------|------|--------|
| 1 | 增强 Cento 语言能力 | 无 | Cento 能表达解释器逻辑 |
| 2 | 标准库自举（`std/*.ct` 替换 `std/*.py`） | #1 | Python 表面积缩减到原语内核 |
| 3 | Lexer in Cento | #1 | Cento 源码 → tokens |
| 4 | Parser in Cento | #3 | tokens → AST |
| 5 | Evaluator in Cento | #4 | AST → 值 |
| 6 | Bootstrap driver | #2-5 | Python 解释器运行 Cento 解释器 |

本规格仅覆盖**子项目 #1**。

## 设计哲学

**极简：只加必需的。** 不添加 `cond`/`case`/模式匹配/宏系统/整数类型等"让代码更好看"的特性。解释器代码用嵌套 `if` 表达分发逻辑，虽然冗长但能工作。每个被添加的原语都必须是用现有能力无法合理实现的基础操作。

## 需求分析

### 各解释器组件的能力需求

**Lexer 需要：**
- 逐字符访问字符串
- 提取子串
- 构造控制字符（换行符等，因 Cento 字符串字面量不支持转义序列）
- 字符分类（数字/字母/空白）
- 字符串转数字

**Parser 需要：**
- 列表/Map 操作（已有：`first` `rest` `get` `Assoc` `Concat` 等）
- 嵌套 `if` 分发（已有）

**Evaluator 需要：**
- 用 `Mutable-map` 做环境（已有）
- **动态参数函数调用**（缺失：当求值函数调用节点时，参数列表长度是动态的，现有函数调用语法无法把列表展开为参数）
- 嵌套 `if` 类型分发（已有）

### 关键约束

**Cento 字符串字面量不支持转义序列。** 当前 Python lexer 的 `_read_string` 直接读取引号之间的原始字符，不处理 `\n` `\t` 等转义。因此 Cento 源码中无法直接表示换行字符。这迫使添加 `from-code` 原语来构造控制字符。

## 增强原语清单

在全局核心环境（自动可用，无需 import）中添加以下 8 个原语：

| 函数 | 签名 | 返回 | 用途 |
|------|------|------|------|
| `char-at` | `(char-at s i)` | 1-char string | 访问字符串第 i 个字符 |
| `substring` | `(substring s start end?)` | string | 提取子串，end 可选（缺省到末尾） |
| `from-code` | `(from-code n)` | 1-char string | 码点 → 字符（构造 `\n` `\t` 等） |
| `digit?` | `(digit? ch)` | bool | ASCII 数字判断（仅 `0-9`） |
| `alpha?` | `(alpha? ch)` | bool | ASCII 字母判断（仅 `a-z A-Z`） |
| `space?` | `(space? ch)` | bool | 空白字符判断（空格/制表/换行/回车） |
| `parse-number` | `(parse-number s)` | number | 字符串 → 数字（失败抛 CentoError） |
| `apply` | `(apply fn args-list)` | any | 用列表参数调用函数（动态元数调用） |

### 命名约定

全部小写，跟随核心内置约定（`print` `count` `first` `get` 等），而非 std 模块导出约定（`Map` `Filter` `Read-file`）。因为这些是语言核心能力，不是可选库。

## 放置位置与注册方式

### 字符串/字符原语（7 个）→ `src/std/string.py`

添加到现有 `FUNCTIONS` 字典，与 `Split` `Join` `Trim` 等一起注册。通过 `_register_builtins` 中的 `STRING_FUNCTIONS` 循环自动注册到全局环境，与现有字符串函数保持一致的注册路径。

### `apply` → `src/evaluator.py` `_register_builtins`

直接在核心内置区注册（与 `+` `print` `count` 等同级），因为它需要捕获 `self` 以调用 `_apply`：

```python
self.global_env.define("apply",
    lambda fn, args: self._apply(fn, list(args)))
```

### 不创建独立内核模块

虽然完整自举愿景下最终需要一个清晰的"最小内核"边界，但子项目 #1 遵循极简哲学——不引入新的架构层。内核边界的显式化推迟到子项目 #2（标准库自举）时处理。

## 各原语的 Python 实现

### `src/std/string.py` 新增函数

需在文件顶部新增导入：

```python
from src.errors import CentoError
```

```python
def char_at_fn(s, i):
    return s[int(i)]

def substring_fn(s, start, end=None):
    if end is None:
        return s[int(start):]
    return s[int(start):int(end)]

def from_code_fn(n):
    return chr(int(n))

def digit_q_fn(ch):
    return len(ch) == 1 and ch in "0123456789"

def alpha_q_fn(ch):
    return len(ch) == 1 and ch.isalpha() and ch.isascii()

def space_q_fn(ch):
    return len(ch) == 1 and ch.isspace() and ch.isascii()

def parse_number_fn(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        raise CentoError(f"Cannot parse number: {s}")
```

注册到 `FUNCTIONS` 字典：

```python
"char-at": char_at_fn,
"substring": substring_fn,
"from-code": from_code_fn,
"digit?": digit_q_fn,
"alpha?": alpha_q_fn,
"space?": space_q_fn,
"parse-number": parse_number_fn,
```

### `src/evaluator.py` 新增注册

在 `_register_builtins` 方法中添加：

```python
# Apply (dynamic arity call)
self.global_env.define("apply",
    lambda fn, args: self._apply(fn, list(args)))
```

### 关键实现决策

1. **`char-at` 不做边界检查** — 越界时抛 Python `IndexError`，被 `try/catch` 捕获转为字符串。Lexer 应在调用前用 `(>= i (count s))` 检查边界。

2. **`substring` 用 Python 切片** — 自动处理越界（clamp 到字符串范围），`s[100:200]` 返回 `""`，对 lexer 友好。

3. **字符分类限定 ASCII** — `digit?` 用显式字符串 `"0123456789"` 避免子串误判（`"12" in "0123456789"` 在 Python 中是 `True`，所以加 `len(ch) == 1` 守卫）。`alpha?`/`space?` 用 `isascii()` 限定 ASCII 范围。

4. **`parse-number` 包装错误** — 失败时抛 `CentoError` 而非裸 `ValueError`，错误信息清晰。

5. **`apply` 通过 `_apply`** — 复用求值器的函数调用逻辑，同时支持 `Fn` 对象和 Python callable。`args` 是 `CentoList`（list 子类），`list(args)` 转换为 Python list 后传给 `_apply`。

## 测试策略

### 单元测试

**`tests/test_std.py`（7 个字符串原语）：**

| 原语 | 测试用例 |
|------|----------|
| `char-at` | 首字符、尾字符、空字符串（应抛错） |
| `substring` | 双参数（到末尾）、三参数、越界 clamp、start > end |
| `from-code` | 大写字母（65 → "A"）、换行符（10 → "\n"） |
| `digit?` | 正例（"5"）、反例（"a"）、空字符串、多字符串（均 false） |
| `alpha?` | 正例（"a" "Z"）、反例（"1"）、空字符串、多字符串 |
| `space?` | 正例（" " "\t" "\n"）、反例（"a"）、空字符串 |
| `parse-number` | 整数（"42"）、浮点（"3.14"）、非法输入（验证抛 `CentoError`） |

**`tests/test_evaluator.py`（`apply`）：**

- `(apply + [1 2 3])` → `6`
- `(apply (fn [x y] (* x y)) [3 4])` → `12`
- `(apply (fn [] 42) [])` → `42`（零参数）

### 集成测试

**`tests/test_integration.py` 新增"原语协作"测试：**

用 Cento 源码写一个最小 tokenizer 片段，验证原语组合使用：

```lisp
(let [s "42"
      n (count s)]
  (let [tokenize-loop
        (fn [i acc]
          (if (>= i n)
            acc
            (let [ch (char-at s i)]
              (if (digit? ch)
                (tokenize-loop (+ i 1)
                  (Concat acc [{:type :digit :value ch}]))
                (error "unexpected char")))))]
    (tokenize-loop 0 [])))
; => [{:type :digit :value "4"} {:type :digit :value "2"}]
```

此测试同时验证 `char-at`、`digit?`、`count`、`Concat`、`error`、闭包递归协作——是子项目 #3（完整 lexer）的微缩预演。

### 验证命令

```bash
pytest
```

### 不做的事

- 不写完整 lexer（那是子项目 #3）
- 不写 `examples/` 演示脚本（极简哲学，测试已足够验证）
- 不测试性能（学习项目，O(n²) 可接受）

## 成功标准

1. 8 个原语全部实现并注册到全局环境
2. 所有单元测试通过
3. 集成测试（最小 tokenizer 片段）通过
4. 现有测试套件全部通过（无回归）
5. 原语可在 Cento 源码中直接调用（无需 import）

## 范围外

以下内容明确不在本子项目范围内：

- 完整 lexer/parser/evaluator 的 Cento 实现（子项目 #3-5）
- 标准库自举（子项目 #2）
- 内核边界显式化（子项目 #2）
- `cond`/`case`/模式匹配/宏系统等语言增强
- 字符串转义序列支持
- 整数类型
- 性能优化
