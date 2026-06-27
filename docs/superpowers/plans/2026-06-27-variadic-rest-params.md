# Cento 可变参数（& rest）支持实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 为 Cento 语言添加 Clojure 风格的 `& rest` 可变参数支持，保持向后兼容，并扩展 2 个标准库函数自举（Const/Flatten）。

**架构：** 扩展 Lexer 识别 `&` 符号 → Parser 解析 `& rest` 语法生成 `fixed_params`+`rest_param` → Evaluator 绑定 rest 参数为 CentoList → 扩展 util.ct/seq.ct 新增 Const/Flatten 自举实现。

**技术栈：** Python（解释器）、Cento 语言（S-expression、fn/let/if/递归）、pytest

---

## 文件结构

| 文件 | 职责 | 操作 |
|------|------|------|
| `src/lexer.py` | `_is_symbol_start` 加入 `&` 字符 | 修改 |
| `src/ast_nodes.py` | FnExpr 字段改为 `fixed_params`+`rest_param` | 修改 |
| `src/parser.py` | `_parse_fn` 重构支持 `& rest` + 错误处理 | 修改 |
| `src/types.py` | `Fn.__slots__` 同步为 `fixed_params`+`rest_param` | 修改 |
| `src/evaluator.py` | `_apply_fn` + `_eval_FnExpr` 适配新参数结构 | 修改 |
| `tests/test_parser.py` | `& rest` 语法解析测试 | 修改 |
| `tests/test_evaluator.py` | rest 参数绑定与调用测试 | 修改 |
| `src/std/util.ct` | 新增 Const 自举实现 | 修改 |
| `src/std/seq.ct` | 新增 Flatten 自举实现 | 修改 |
| `tests/test_bootstrap.py` | Const/Flatten 自举验证 | 修改 |

---

### 任务 1：扩展 Lexer 识别 `&` 符号

**文件：**
- 修改：`src/lexer.py:130-132`

- [ ] **步骤 1：修改 `_is_symbol_start` 加入 `&`**

将：
```python
    @staticmethod
    def _is_symbol_start(ch: str) -> bool:
        return ch.isalpha() or ch in '+-*/=<>!?_'
```

改为：
```python
    @staticmethod
    def _is_symbol_start(ch: str) -> bool:
        return ch.isalpha() or ch in '+-*/=<>!?_&'
```

- [ ] **步骤 2：验证 `&` 被识别为 SYMBOL**

运行：
```bash
python -c "from src.lexer import Lexer; tokens = Lexer('(fn F [& rest] rest)').tokenize(); print([t.value for t in tokens if t.value])"
```
预期：输出包含 `'&'` 的符号列表

- [ ] **步骤 3：运行现有 lexer 测试验证零回归**

运行：`python -m pytest tests/test_lexer.py -v`
预期：全部 PASS

- [ ] **步骤 4：Commit**

```bash
git add src/lexer.py
git commit -m "feat(lexer): 识别 & 符号为 SYMBOL token"
```

---

### 任务 2：AST FnExpr 字段改为 fixed_params + rest_param

**文件：**
- 修改：`src/ast_nodes.py:57-62`

- [ ] **步骤 1：修改 FnExpr 定义**

将：
```python
@dataclass
class FnExpr:
    name: str | None
    params: list[str]
    body: list
```

改为：
```python
@dataclass
class FnExpr:
    name: str | None
    fixed_params: list[str]
    rest_param: str | None
    body: list
```

- [ ] **步骤 2：搜索所有引用 `.params` 的位置**

运行：
```bash
git grep -n "\.params" -- "src/*.py"
```
预期输出（需逐一更新）：
- `src/evaluator.py` 中 `Fn(name=node.name, params=node.params, ...)` 等
- `src/types.py` 中 `Fn.__slots__` 和 `__init__`

- [ ] **步骤 3：Commit（此任务不运行测试，因 Parser/Evaluator 尚未更新）**

```bash
git add src/ast_nodes.py
git commit -m "refactor(ast): FnExpr 字段改为 fixed_params + rest_param"
```

---

### 任务 3：Parser 重构 _parse_fn 支持 & rest

**文件：**
- 修改：`src/parser.py:128-137`

- [ ] **步骤 1：编写失败的测试**

在 `tests/test_parser.py` 末尾追加：
```python


class TestVariadicParams:
    def test_parse_full_rest(self):
        ast = parse_str("(fn F [& rest] rest)")
        assert ast.expressions[0].fixed_params == []
        assert ast.expressions[0].rest_param == "rest"

    def test_parse_mixed_rest(self):
        ast = parse_str("(fn F [a b & rest] (+ a b))")
        assert ast.expressions[0].fixed_params == ["a", "b"]
        assert ast.expressions[0].rest_param == "rest"

    def test_parse_no_rest_backward_compat(self):
        ast = parse_str("(fn F [a b] (+ a b))")
        assert ast.expressions[0].fixed_params == ["a", "b"]
        assert ast.expressions[0].rest_param is None

    def test_parse_error_empty_after_amp(self):
        with pytest.raises(Exception):
            parse_str("(fn F [&])")

    def test_parse_error_multiple_amp(self):
        with pytest.raises(Exception):
            parse_str("(fn F [a & & b])")

    def test_parse_error_param_after_rest(self):
        with pytest.raises(Exception):
            parse_str("(fn F [a & b c])")

    def test_parse_error_amp_at_end_no_param(self):
        with pytest.raises(Exception):
            parse_str("(fn F [a &])")
```

- [ ] **步骤 2：运行测试验证失败**

运行：`python -m pytest tests/test_parser.py::TestVariadicParams -v`
预期：全部 FAIL（`fixed_params` 属性不存在）

- [ ] **步骤 3：重构 `_parse_fn`**

将 `src/parser.py:128-137`：
```python
    def _parse_fn(self):
        self._advance()  # skip 'fn'
        name = None
        if self._peek().type == TokenType.SYMBOL and self._peek().value != "[":
            name = self._advance().value
        self._expect(TokenType.LBRACKET)
        params = []
        while self._peek().type != TokenType.RBRACKET:
            params.append(self._expect(TokenType.SYMBOL).value)
        self._expect(TokenType.RBRACKET)
        body = []
        while self._peek().type != TokenType.RPAREN:
            body.append(self._parse_expr())
        return FnExpr(name=name, params=params, body=body)
```

替换为：
```python
    def _parse_fn(self):
        self._advance()  # skip 'fn'
        name = None
        if self._peek().type == TokenType.SYMBOL and self._peek().value != "[":
            name = self._advance().value
        self._expect(TokenType.LBRACKET)
        fixed_params = []
        rest_param = None
        while self._peek().type != TokenType.RBRACKET:
            tok = self._advance()
            if tok.type != TokenType.SYMBOL:
                raise CentoError(f"Expected parameter name, got {tok.type.name} at line {tok.line}")
            if tok.value == "&":
                if rest_param is not None:
                    raise CentoError(f"Multiple & in parameter list at line {tok.line}")
                if self._peek().type != TokenType.SYMBOL or self._peek().value == "&":
                    raise CentoError(f"Expected parameter name after & at line {tok.line}")
                rest_param = self._advance().value
            else:
                if rest_param is not None:
                    raise CentoError(f"Parameter after rest parameter at line {tok.line}")
                fixed_params.append(tok.value)
        self._expect(TokenType.RBRACKET)
        body = []
        while self._peek().type != TokenType.RPAREN:
            body.append(self._parse_expr())
        return FnExpr(name=name, fixed_params=fixed_params, rest_param=rest_param, body=body)
```

- [ ] **步骤 4：运行测试验证通过**

运行：`python -m pytest tests/test_parser.py::TestVariadicParams -v`
预期：7 个测试全 PASS

- [ ] **步骤 5：Commit**

```bash
git add src/parser.py tests/test_parser.py
git commit -m "feat(parser): _parse_fn 支持 & rest 可变参数语法"
```

---

### 任务 4：Fn 类型同步 fixed_params + rest_param

**文件：**
- 修改：`src/types.py:36-45`

- [ ] **步骤 1：修改 Fn 类定义**

将：
```python
class Fn:
    __slots__ = ("name", "params", "body", "env")

    def __init__(self, name, params, body, env):
        self.name = name
        self.params = params
        self.body = body
        self.env = env
```

替换为：
```python
class Fn:
    __slots__ = ("name", "fixed_params", "rest_param", "body", "env")

    def __init__(self, name, fixed_params, rest_param, body, env):
        self.name = name
        self.fixed_params = fixed_params
        self.rest_param = rest_param
        self.body = body
        self.env = env
```

- [ ] **步骤 2：Commit**

```bash
git add src/types.py
git commit -m "refactor(types): Fn 类型同步 fixed_params + rest_param"
```

---

### 任务 5：Evaluator 适配新参数结构

**文件：**
- 修改：`src/evaluator.py:223-225`（`_eval_FnExpr`）、`src/evaluator.py:304-313`（`_apply_fn`）

- [ ] **步骤 1：编写失败的测试**

在 `tests/test_evaluator.py` 末尾追加：
```python


class TestVariadicParams:
    def test_call_full_rest(self):
        assert list(eval_str("((fn [& rest] rest) 1 2 3)")) == [1.0, 2.0, 3.0]

    def test_call_mixed_rest(self):
        result = eval_str("((fn [a & rest] rest) 1 2 3)")
        assert list(result) == [2.0, 3.0]

    def test_call_empty_rest(self):
        assert list(eval_str("((fn [& rest] rest))")) == []

    def test_call_no_rest_strict_arity(self):
        with pytest.raises(Exception):
            eval_str("((fn [a] a) 1 2)")

    def test_call_rest_returns_centolist(self):
        from src.types import CentoList
        result = eval_str("((fn [& rest] rest) 1 2 3)")
        assert isinstance(result, CentoList)

    def test_tco_with_rest(self):
        # rest 参数与 TCO 兼容
        result = eval_str("""
            (let [count (fn [n acc & rest]
                          (if (= n 0)
                            acc
                            (count (- n 1) (+ acc 1))))]
              (count 100 0))
        """)
        assert result == 100.0
```

- [ ] **步骤 2：运行测试验证失败**

运行：`python -m pytest tests/test_evaluator.py::TestVariadicParams -v`
预期：全部 FAIL（`Fn` 构造参数不匹配）

- [ ] **步骤 3：修改 `_eval_FnExpr`**

将 `src/evaluator.py` 中 `_eval_FnExpr` 方法内：
```python
        fn = Fn(name=node.name, params=node.params, body=node.body, env=env)
```

替换为：
```python
        fn = Fn(name=node.name, fixed_params=node.fixed_params, rest_param=node.rest_param, body=node.body, env=env)
```

- [ ] **步骤 4：修改 `_apply_fn`**

将 `src/evaluator.py` 中 `_apply_fn` 方法开头：
```python
    def _apply_fn(self, fn_obj, args):
        if len(args) != len(fn_obj.params):
            raise CentoError(f"Expected {len(fn_obj.params)} args, got {len(args)}")

        call_env = Environment(fn_obj.env)
        for name, val in zip(fn_obj.params, args):
            call_env.define(name, val)
```

替换为：
```python
    def _apply_fn(self, fn_obj, args):
        fixed_count = len(fn_obj.fixed_params)
        if fn_obj.rest_param is None:
            if len(args) != fixed_count:
                raise CentoError(f"Expected {fixed_count} args, got {len(args)}")
        else:
            if len(args) < fixed_count:
                raise CentoError(f"Expected at least {fixed_count} args, got {len(args)}")

        call_env = Environment(fn_obj.env)
        for name, val in zip(fn_obj.fixed_params, args[:fixed_count]):
            call_env.define(name, val)
        if fn_obj.rest_param is not None:
            from src.types import CentoList
            rest_args = CentoList(list(args[fixed_count:]))
            call_env.define(fn_obj.rest_param, rest_args)
```

- [ ] **步骤 5：运行测试验证通过**

运行：`python -m pytest tests/test_evaluator.py::TestVariadicParams -v`
预期：6 个测试全 PASS

- [ ] **步骤 6：运行全套测试验证零回归**

运行：`python -m pytest`
预期：222 个测试全 PASS（原 222 + 新增 13 = 235）

- [ ] **步骤 7：Commit**

```bash
git add src/evaluator.py tests/test_evaluator.py
git commit -m "feat(evaluator): 适配可变参数支持"
```

---

### 任务 6：扩展 util.ct 新增 Const 自举实现

**文件：**
- 修改：`src/std/util.ct`

- [ ] **步骤 1：在 util.ct 末尾追加 Const 实现**

在 `src/std/util.ct` 文件末尾追加：
```lisp

(fn Const [x]
  (fn [& rest] x))
```

- [ ] **步骤 2：在 `tests/test_bootstrap.py` 的 `TestBootstrapLoaded` 类中追加测试**

在 `TestBootstrapLoaded` 类末尾追加：
```python

    def test_const_from_ct(self):
        """验证 Const 来自 util.ct，rest 参数支持"""
        result = eval_str("""
            (let [c (Const 42)]
              (c 1 2 3))
        """)
        assert result == 42.0
```

- [ ] **步骤 3：运行 bootstrap 测试验证通过**

运行：`python -m pytest tests/test_bootstrap.py -v`
预期：所有测试 PASS（包括新增 test_const_from_ct）

- [ ] **步骤 4：Commit**

```bash
git add src/std/util.ct tests/test_bootstrap.py
git commit -m "feat(bootstrap): util.ct 新增 Const 自举实现"
```

---

### 任务 7：扩展 seq.ct 新增 Flatten 自举实现

**文件：**
- 修改：`src/std/seq.ct`

- [ ] **步骤 1：在 seq.ct 末尾追加 Flatten 实现**

在 `src/std/seq.ct` 文件末尾追加：
```lisp

(fn Flatten [xs]
  (Reduce
    (fn [acc x]
      (if (list? x)
        (Concat acc (Flatten x))
        (Concat acc [x])))
    []
    xs))
```

- [ ] **步骤 2：在 `tests/test_bootstrap.py` 的 `TestBootstrapLoaded` 类中追加测试**

在 `TestBootstrapLoaded` 类末尾追加：
```python

    def test_flatten_from_ct(self):
        """验证 Flatten 来自 seq.ct，递归 + 高阶函数"""
        result = eval_str("(Flatten [[1 2] [3] [4 [5]]])")
        assert list(result) == [1.0, 2.0, 3.0, 4.0, 5.0]
```

- [ ] **步骤 3：运行 bootstrap 测试验证通过**

运行：`python -m pytest tests/test_bootstrap.py -v`
预期：所有测试 PASS（包括新增 test_flatten_from_ct）

- [ ] **步骤 4：Commit**

```bash
git add src/std/seq.ct tests/test_bootstrap.py
git commit -m "feat(bootstrap): seq.ct 新增 Flatten 自举实现"
```

---

### 任务 8：最终验证与推送

- [ ] **步骤 1：运行完整测试套件**

运行：`python -m pytest -v`
预期：237 个测试全 PASS（原 222 + 语言能力 13 + bootstrap 2）

- [ ] **步骤 2：手动验证可变参数功能**

运行：
```bash
python -c "from src.evaluator import eval_str; print('rest:', list(eval_str('((fn [& rest] rest) 1 2 3)'))); print('mixed:', list(eval_str('((fn [a & rest] rest) 1 2 3)'))); print('Const:', eval_str('(let [c (Const 42)] (c 1 2 3))')); print('Flatten:', list(eval_str('(Flatten [[1 2] [3]])')))"
```
预期：
- `rest: [1.0, 2.0, 3.0]`
- `mixed: [2.0, 3.0]`
- `Const: 42.0`
- `Flatten: [1.0, 2.0, 3.0]`

- [ ] **步骤 3：推送**

```bash
git push
```

---

## 自检结果

**1. 规格覆盖度：**
- 语法设计 → 任务 1（lexer）+ 任务 3（parser） ✓
- AST 扩展 → 任务 2 ✓
- Evaluator 修改 → 任务 5 ✓
- 新增自举函数 Const → 任务 6 ✓
- 新增自举函数 Flatten → 任务 7 ✓
- 测试策略 → 任务 3（parser 测试）+ 任务 5（evaluator 测试）+ 任务 6/7（bootstrap 测试）✓
- 最终验证 → 任务 8 ✓

**2. 占位符扫描：** 无 TODO/待定，所有代码步骤含完整代码。

**3. 类型一致性：** `fixed_params` + `rest_param` 在任务 2（FnExpr）→ 任务 4（Fn）→ 任务 5（Evaluator）中一致使用；`CentoList` 在任务 5 和任务 7 中一致导入使用；`parse_str` 辅助函数在测试中复用，与现有 test_parser.py 一致。
