# Cento 可变参数（& rest）支持设计规格

> 为 Cento 语言添加 Clojure 风格的可变参数支持，解锁更多标准库函数的自举。

## 背景与目标

### 当前状态
- 已完成 22/37 标准库函数自举（util 9/13、seq 8/13、collection 5/11）
- 11 个函数保留 Python 原生，主因是不支持可变参数
- `_load_cent_module` 加载机制已稳定，支持 Cento 优先 + Python fallback

### 目标
1. 扩展 Cento 语法支持 `& rest` 可变参数
2. 保持完全向后兼容：现有 `(fn F [a b] ...)` 行为不变
3. 验证至少 2 个新函数可自举（Const、Flatten）
4. 零回归：现有 222 个测试全绿

### 非目标
- 不支持 `Apply` 展开（需独立机制，超出范围）
- 不支持 map 字面量动态键（需 parser/evaluator 大改）
- 不实现 Sort-by/Concat/Merge/Assoc/Dissoc/Keys/Values 自举（仍受其他限制）

## 语法设计

### 语法形式
```lisp
(fn Comp [& fns] ...)           ; 全 rest
(fn F [a b & rest] ...)          ; 固定 + rest
(fn F [a b] ...)                  ; 无 rest（现有形式不变）
```

### 规则
- `&` 必须出现在参数列表末尾，其后只能有一个参数名 + `]`
- rest 参数在函数体内绑定为 `CentoList`
- 无 rest 时保持严格参数数量校验（现有行为）

### 错误形式
- `[&]` → "Expected parameter name after &"
- `[a & b c]` → "Parameter after rest parameter"
- `[a & & b]` → "Multiple & in parameter list"
- `[a &]` → "Expected parameter name after &"

## AST 扩展

### FnExpr 结构变更
```python
@dataclass
class FnExpr:
    name: str | None
    fixed_params: list[str]    # 固定参数名
    rest_param: str | None     # rest 参数名（None 表示无 rest）
    body: list
```

**向后兼容**：现有 `params: list[str]` 字段移除，所有引用处更新为 `fixed_params` + `rest_param`。

### Fn 类型同步
```python
class Fn:
    __slots__ = ("name", "fixed_params", "rest_param", "body", "env")
```

## 实现策略

### Lexer 修改
将 `&` 加入 `_is_symbol_start` 允许字符，使其识别为 SYMBOL token。

```python
@staticmethod
def _is_symbol_start(ch: str) -> bool:
    return ch.isalpha() or ch in '+-*/=<>!?_&'
```

**注意**：`_is_symbol_char` 不需加 `&`，因为 `&` 只作为独立符号出现（不需支持 `a&b` 这样的符号）。

### Parser 修改
`_parse_fn` 方法重构：
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

### Evaluator 修改
`_apply_fn` 方法适配新参数结构：
```python
def _apply_fn(self, fn_obj, args):
    fixed_count = len(fn_obj.fixed_params)
    if len(args) < fixed_count:
        raise CentoError(f"Expected at least {fixed_count} args, got {len(args)}")
    if fn_obj.rest_param is None and len(args) != fixed_count:
        raise CentoError(f"Expected {fixed_count} args, got {len(args)}")

    call_env = Environment(fn_obj.env)
    for name, val in zip(fn_obj.fixed_params, args[:fixed_count]):
        call_env.define(name, val)
    if fn_obj.rest_param is not None:
        rest_args = CentoList(list(args[fixed_count:]))
        call_env.define(fn_obj.rest_param, rest_args)

    # TCO trampoline（不变）
    ...
```

### Fn.__call__ 适配
`Fn.__call__` 已调用 `_apply_fn`，无需修改。

### 现有代码引用更新
- `_eval_FnExpr` 中 `Fn(name=node.name, params=node.params, ...)` → `Fn(name=node.name, fixed_params=node.fixed_params, rest_param=node.rest_param, ...)`
- `Fn.__init__` 同步更新参数名

## 新增自举函数

### Const（util.ct）
```lisp
(fn Const [x]
  (fn [& rest] x))
```

### Flatten（seq.ct）
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

**依赖**：
- `Reduce`（已自举，collection.ct）
- `list?`（内置谓词）
- `Concat`（原生，collection.py）
- TCO 支持（已验证）

### 保留原生的函数（9 个）
- `Comp`（依赖 Apply 展开）
- `Apply`（需将列表展开为调用参数的机制）
- `Concat`（底层需 list 追加，自举会循环依赖）
- `Merge`/`Assoc`/`Dissoc`/`Keys`/`Values`（需 map 动态构建）
- `Sort-by`/`Sort-by-desc`（依赖排序算法）

## 测试策略

### 语言能力测试
在 `tests/test_parser.py` 添加：
- `test_parse_full_rest`：`(fn F [& rest] ...)` 解析正确
- `test_parse_mixed_rest`：`(fn F [a b & rest] ...)` 解析正确
- `test_parse_no_rest`：`(fn F [a b] ...)` 向后兼容
- `test_parse_error_empty_after_amp`：`[&]` 报错
- `test_parse_error_multiple_amp`：`[a & & b]` 报错
- `test_parse_error_param_after_rest`：`[a & b c]` 报错

在 `tests/test_evaluator.py` 添加：
- `test_call_full_rest`：`(let [f (fn [& rest] rest)] (f 1 2 3))` 返回 `[1 2 3]`
- `test_call_mixed_rest`：`(let [f (fn [a & rest] rest)] (f 1 2 3))` 返回 `[2 3]`
- `test_call_empty_rest`：`(let [f (fn [& rest] rest)] (f))` 返回 `[]`
- `test_call_no_rest_strict_arity`：`(fn [a] ...)` 调用参数不足报错
- `test_tco_with_rest`：rest 参数与 TCO 兼容

### 复用现有测试
- 现有 222 个测试验证零回归

### Bootstrap 测试
在 `tests/test_bootstrap.py` 添加：
- `test_const_from_ct`：Const 来自 util.ct，`(let [c (Const 42)] (c 1 2 3))` 返回 42
- `test_flatten_from_ct`：Flatten 来自 seq.ct，`(Flatten [[1 2] [3]])` 返回 `[1 2 3]`

### 验证检查点
1. 语言能力测试全绿
2. 现有 222 个测试零回归
3. 新增 bootstrap 测试全绿
4. 手动验证：`(fn [& rest] rest)` 调用返回列表

## 实现顺序

1. Lexer：`&` 加入 `_is_symbol_start`
2. AST：FnExpr 字段改为 `fixed_params` + `rest_param`
3. Parser：`_parse_fn` 重构 + 错误处理
4. types.py：`Fn.__slots__` 同步
5. Evaluator：`_apply_fn` + `_eval_FnExpr` 适配
6. 语言能力测试（parser + evaluator）
7. 运行全套测试验证零回归
8. 扩展 util.ct（Const）+ seq.ct（Flatten）
9. Bootstrap 测试
10. 最终验证 + 推送

## 风险与缓解

### 风险 1：现有代码引用 `params` 字段
- 影响：所有使用 `fn_obj.params` 的地方会报 AttributeError
- 缓解：全局搜索 `\.params` 引用，逐一更新为 `fixed_params` + `rest_param`

### 风险 2：TCO 兼容性
- 影响：rest 参数绑定可能影响 TCO trampoline 流程
- 缓解：TCO 检查的是 CallExpr 结构而非参数数量，rest 绑定在 `call_env` 创建后完成，不影响后续 TCO 判断

### 风险 3：错误信息一致性
- 影响：参数数量错误的报错信息需区分有 rest 和无 rest
- 缓解：有 rest 报 "Expected at least N args"，无 rest 报 "Expected N args"
