# 自举子项目 #1：增强 Cento 语言能力 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为 Cento 添加 8 个编写解释器严格必需的原语（char-at, substring, from-code, digit?, alpha?, space?, parse-number, apply），使 Cento 能表达 lexer/parser/evaluator 逻辑。

**架构：** 7 个字符串/字符原语添加到 `src/std/string.py` 的 `FUNCTIONS` 字典（通过现有注册路径自动注入全局环境）；`apply` 添加到 `src/evaluator.py` 的 `_register_builtins`（需捕获 `self` 以调用 `_apply`）。测试遵循现有 `eval_str` 模式。

**技术栈：** Python 3.10+, pytest, Cento 现有解释器架构

**规格：** [docs/superpowers/specs/2026-06-20-bootstrap-sub1-language-enhancements-design.md](../specs/2026-06-20-bootstrap-sub1-language-enhancements-design.md)

---

## 文件结构

| 文件 | 职责 | 变更类型 |
|------|------|----------|
| `src/std/string.py` | 添加 7 个字符串/字符原语函数 + CentoError 导入 + 注册到 FUNCTIONS | 修改 |
| `src/evaluator.py` | 在 `_register_builtins` 中注册 `apply` | 修改 |
| `tests/test_std.py` | 添加 7 个字符串原语的单元测试 + 导入 pytest/CentoError | 修改 |
| `tests/test_evaluator.py` | 添加 `apply` 的单元测试 | 修改 |
| `tests/test_integration.py` | 添加"原语协作"集成测试（最小 tokenizer） | 修改 |

**测试模式约定（遵循现有代码）：**
- 使用 `eval_str('(cento code)')` 调用，返回 Python 值
- 列表断言：`list(result) == [expected]`
- Map 断言：`result[Keyword("key")] == expected`
- 错误断言：`with pytest.raises(CentoError, match="...")`
- 布尔断言：`assert result is True` / `assert result is False`

---

### 任务 1：添加 `char-at` 和 `substring` 原语

**文件：**
- 修改：`src/std/string.py`（添加函数 + 注册）
- 测试：`tests/test_std.py`（添加测试）

- [ ] **步骤 1：编写失败的测试**

在 `tests/test_std.py` 末尾追加：

```python
def test_string_char_at():
    assert eval_str('(char-at "hello" 0)') == "h"
    assert eval_str('(char-at "hello" 4)') == "o"

def test_string_substring_two_args():
    assert eval_str('(substring "hello" 2)') == "llo"

def test_string_substring_three_args():
    assert eval_str('(substring "hello" 1 3)') == "el"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_std.py::test_string_char_at tests/test_std.py::test_string_substring_two_args tests/test_std.py::test_string_substring_three_args -v`
预期：FAIL，报错 "char-at 未定义" 或类似

- [ ] **步骤 3：编写实现代码**

在 `src/std/string.py` 中，在 `merge_fn` 函数之后、`FUNCTIONS` 字典之前添加：

```python
def char_at_fn(s, i):
    return s[int(i)]

def substring_fn(s, start, end=None):
    if end is None:
        return s[int(start):]
    return s[int(start):int(end)]
```

在 `FUNCTIONS` 字典中追加两个条目（在 `"Merge": merge_fn,` 之后）：

```python
    "char-at": char_at_fn,
    "substring": substring_fn,
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_std.py::test_string_char_at tests/test_std.py::test_string_substring_two_args tests/test_std.py::test_string_substring_three_args -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add src/std/string.py tests/test_std.py
git commit -m "feat(string): 添加 char-at 和 substring 原语"
```

---

### 任务 2：添加 `from-code` 原语

**文件：**
- 修改：`src/std/string.py`
- 测试：`tests/test_std.py`

- [ ] **步骤 1：编写失败的测试**

在 `tests/test_std.py` 末尾追加：

```python
def test_string_from_code():
    assert eval_str('(from-code 65)') == "A"
    assert eval_str('(from-code 10)') == "\n"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_std.py::test_string_from_code -v`
预期：FAIL

- [ ] **步骤 3：编写实现代码**

在 `src/std/string.py` 的 `substring_fn` 之后添加：

```python
def from_code_fn(n):
    return chr(int(n))
```

在 `FUNCTIONS` 字典中追加：

```python
    "from-code": from_code_fn,
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_std.py::test_string_from_code -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add src/std/string.py tests/test_std.py
git commit -m "feat(string): 添加 from-code 原语"
```

---

### 任务 3：添加 `digit?`、`alpha?`、`space?` 原语

**文件：**
- 修改：`src/std/string.py`
- 测试：`tests/test_std.py`

- [ ] **步骤 1：编写失败的测试**

在 `tests/test_std.py` 末尾追加：

```python
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
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_std.py::test_string_digit_q tests/test_std.py::test_string_alpha_q tests/test_std.py::test_string_space_q tests/test_std.py::test_string_space_q_control_chars -v`
预期：FAIL

- [ ] **步骤 3：编写实现代码**

在 `src/std/string.py` 的 `from_code_fn` 之后添加：

```python
def digit_q_fn(ch):
    return len(ch) == 1 and ch in "0123456789"

def alpha_q_fn(ch):
    return len(ch) == 1 and ch.isalpha() and ch.isascii()

def space_q_fn(ch):
    return len(ch) == 1 and ch.isspace() and ch.isascii()
```

在 `FUNCTIONS` 字典中追加：

```python
    "digit?": digit_q_fn,
    "alpha?": alpha_q_fn,
    "space?": space_q_fn,
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_std.py::test_string_digit_q tests/test_std.py::test_string_alpha_q tests/test_std.py::test_string_space_q tests/test_std.py::test_string_space_q_control_chars -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add src/std/string.py tests/test_std.py
git commit -m "feat(string): 添加 digit? alpha? space? 字符分类原语"
```

---

### 任务 4：添加 `parse-number` 原语

**文件：**
- 修改：`src/std/string.py`（含新增 CentoError 导入）
- 测试：`tests/test_std.py`（含新增 pytest/CentoError 导入）

- [ ] **步骤 1：编写失败的测试**

在 `tests/test_std.py` 顶部修改导入（替换第 2 行 `from src.evaluator import eval_str`）：

```python
# tests/test_std.py
import pytest
from src.evaluator import eval_str
from src.errors import CentoError
```

在文件末尾追加测试：

```python
def test_string_parse_number_int():
    assert eval_str('(parse-number "42")') == 42.0

def test_string_parse_number_float():
    assert eval_str('(parse-number "3.14")') == 3.14

def test_string_parse_number_error():
    with pytest.raises(CentoError, match="Cannot parse number"):
        eval_str('(parse-number "abc")')
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_std.py::test_string_parse_number_int tests/test_std.py::test_string_parse_number_float tests/test_std.py::test_string_parse_number_error -v`
预期：FAIL

- [ ] **步骤 3：编写实现代码**

在 `src/std/string.py` 顶部修改导入（在 `from src.types import CentoList, CentoMap, Keyword` 之后新增一行）：

```python
from src.errors import CentoError
```

在 `space_q_fn` 之后添加：

```python
def parse_number_fn(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        raise CentoError(f"Cannot parse number: {s}")
```

在 `FUNCTIONS` 字典中追加：

```python
    "parse-number": parse_number_fn,
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_std.py::test_string_parse_number_int tests/test_std.py::test_string_parse_number_float tests/test_std.py::test_string_parse_number_error -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add src/std/string.py tests/test_std.py
git commit -m "feat(string): 添加 parse-number 原语"
```

---

### 任务 5：添加 `apply` 原语

**文件：**
- 修改：`src/evaluator.py`（在 `_register_builtins` 中注册）
- 测试：`tests/test_evaluator.py`

- [ ] **步骤 1：编写失败的测试**

在 `tests/test_evaluator.py` 末尾追加：

```python
def test_apply_with_builtin():
    assert eval_str('(apply + [1 2 3])') == 6.0

def test_apply_with_fn():
    assert eval_str('(apply (fn [x y] (* x y)) [3 4])') == 12.0

def test_apply_with_no_args():
    assert eval_str('(apply (fn [] 42) [])') == 42.0
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_evaluator.py::test_apply_with_builtin tests/test_evaluator.py::test_apply_with_fn tests/test_evaluator.py::test_apply_with_no_args -v`
预期：FAIL

- [ ] **步骤 3：编写实现代码**

在 `src/evaluator.py` 的 `_register_builtins` 方法中，在 `self.global_env.define("error", _error_fn)` 这一行之前添加：

```python
        # Apply (dynamic arity call)
        self.global_env.define("apply",
            lambda fn, args: self._apply(fn, list(args)))
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_evaluator.py::test_apply_with_builtin tests/test_evaluator.py::test_apply_with_fn tests/test_evaluator.py::test_apply_with_no_args -v`
预期：PASS

- [ ] **步骤 5：Commit**

```bash
git add src/evaluator.py tests/test_evaluator.py
git commit -m "feat(core): 添加 apply 原语支持动态元数函数调用"
```

---

### 任务 6：添加集成测试（最小 tokenizer）

**文件：**
- 测试：`tests/test_integration.py`

- [ ] **步骤 1：编写测试**

在 `tests/test_integration.py` 末尾追加：

```python
def test_primitives_tokenizer():
    """验证原语协作：用 char-at/digit?/count/Concat/error 写最小 tokenizer。"""
    code = '''
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
    '''
    result = eval_str(code)
    assert len(result) == 2
    assert result[0][Keyword("type")] == Keyword("digit")
    assert result[0][Keyword("value")] == "4"
    assert result[1][Keyword("type")] == Keyword("digit")
    assert result[1][Keyword("value")] == "2"
```

- [ ] **步骤 2：运行测试验证通过**

运行：`pytest tests/test_integration.py::test_primitives_tokenizer -v`
预期：PASS（所有原语已在前序任务实现）

- [ ] **步骤 3：Commit**

```bash
git add tests/test_integration.py
git commit -m "test(integration): 添加原语协作最小 tokenizer 测试"
```

---

### 任务 7：最终验证

**文件：** 无修改

- [ ] **步骤 1：运行完整测试套件**

运行：`pytest -v`
预期：所有测试 PASS，无回归

- [ ] **步骤 2：验证原语无需 import 即可用**

运行：`pytest tests/test_std.py tests/test_evaluator.py -v`
预期：PASS（确认 8 个原语已注册到全局环境）

- [ ] **步骤 3：如有未提交变更则提交**

运行：`git status`
预期：clean（如不 clean，提交剩余变更）

---

## 自检结果

**1. 规格覆盖度：**

| 规格需求 | 对应任务 |
|----------|----------|
| `char-at` 原语 | 任务 1 |
| `substring` 原语 | 任务 1 |
| `from-code` 原语 | 任务 2 |
| `digit?` 原语 | 任务 3 |
| `alpha?` 原语 | 任务 3 |
| `space?` 原语 | 任务 3 |
| `parse-number` 原语 | 任务 4 |
| `apply` 原语 | 任务 5 |
| 字符串原语放 `src/std/string.py` | 任务 1-4 |
| `apply` 放 `src/evaluator.py` | 任务 5 |
| 单元测试 | 任务 1-5 |
| 集成测试（最小 tokenizer） | 任务 6 |
| 验证命令 `pytest` | 任务 7 |
| 成功标准：8 原语实现 + 测试通过 + 无回归 | 任务 7 |

无遗漏。

**2. 占位符扫描：** 无 TODO/待定/模糊描述。每个步骤都有完整代码。✓

**3. 类型一致性：**
- `char_at_fn(s, i)` — 任务 1 定义，无后续引用
- `substring_fn(s, start, end=None)` — 任务 1 定义，签名与规格一致
- `from_code_fn(n)` — 任务 2 定义，测试中 `(from-code 65)` 调用一致
- `digit_q_fn(ch)` / `alpha_q_fn(ch)` / `space_q_fn(ch)` — 任务 3 定义，测试中 `(digit? "5")` 调用一致
- `parse_number_fn(s)` — 任务 4 定义，测试中 `(parse-number "42")` 调用一致
- `apply` 注册为 `lambda fn, args: self._apply(fn, list(args))` — 任务 5 定义，测试中 `(apply + [1 2 3])` 调用一致
- FUNCTIONS 字典键名全部小写连字符（`char-at` `parse-number`），与规格命名约定一致 ✓

无类型不一致。
