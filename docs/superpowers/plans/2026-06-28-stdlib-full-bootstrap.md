# 标准库彻底自举实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 删除 `src/std/` 下所有 `.py` 文件，纯逻辑函数移入 `.ct` 自举，宿主能力（math/io/fs/mutable/Concat/Apply/string 原语）移入 `evaluator.py`。

**架构：** `.ct` 文件自举 40 个纯逻辑函数（新增 `string.ct` 15 个 + `util.ct` 新增 Comp）；`evaluator.py` 的 `_register_builtins` 注册 48 个宿主原语（含新增 `to-code`）；`_load_cent_module` 重构为共享当前 env 绑定，脱离 `.py` 依赖。

**技术栈：** Python 3.12+ / pytest / Cento Lisp

**规格文档：** `docs/superpowers/specs/2026-06-28-stdlib-full-bootstrap-design.md`

---

## 文件结构

| 文件 | 职责 | 操作 |
|------|------|------|
| `src/evaluator.py` | 宿主原语注册 + `_load_cent_module` 加载器 | 修改 |
| `src/std/string.ct` | 15 个 string 纯逻辑函数自举 | 新建 |
| `src/std/util.ct` | 新增 Comp 函数 | 修改 |
| `tests/test_evaluator.py` | to-code 原语测试 | 修改 |
| `tests/test_bootstrap.py` | string.ct 来源验证 + 修正过时测试 | 修改 |
| `src/std/collection.py` | 已自举 + 宿主移入后删除 | 删除 |
| `src/std/seq.py` | 已全部自举，删除 | 删除 |
| `src/std/util.py` | 已自举 + 宿主移入后删除 | 删除 |
| `src/std/math.py` | 宿主移入后删除 | 删除 |
| `src/std/string.py` | 自举 + 宿主移入后删除 | 删除 |
| `src/std/mutable.py` | 宿主移入后删除 | 删除 |
| `src/std/io.py` | 宿主移入后删除 | 删除 |
| `src/std/fs.py` | 宿主移入后删除 | 删除 |

---

## 任务 1：新增 to-code 原语

**文件：**
- 修改：`src/evaluator.py`（`_register_builtins` 方法，约第 55 行附近）
- 测试：`tests/test_evaluator.py`（末尾追加）

- [ ] **步骤 1：编写失败的测试**

在 `tests/test_evaluator.py` 末尾追加：

```python
class TestToCode:
    def test_to_code_uppercase(self):
        assert eval_str('(to-code "A")') == 65.0

    def test_to_code_lowercase(self):
        assert eval_str('(to-code "a")') == 97.0

    def test_to_code_digit(self):
        assert eval_str('(to-code "0")') == 48.0

    def test_from_to_code_roundtrip(self):
        assert eval_str('(from-code (to-code "x"))') == "x"

    def test_to_from_code_roundtrip(self):
        assert eval_str('(to-code (from-code 97))') == 97.0
```

- [ ] **步骤 2：运行测试验证失败**

运行：`python -m pytest tests/test_evaluator.py::TestToCode -v`
预期：FAIL，报错 "Undefined symbol: to-code"

- [ ] **步骤 3：实现 to-code 原语**

在 `src/evaluator.py` 的 `_register_builtins` 方法中，找到 `self.global_env.define("from-code", ...)` 所在的 string 原语区块（若不存在则在 Error 注册后添加），新增：

```python
self.global_env.define("to-code", lambda ch: float(ord(ch[0])))
```

注：若 `from-code` 尚未在 `_register_builtins` 中（当前在 string.py），先临时添加 `from-code` 注册以使 roundtrip 测试通过：

```python
self.global_env.define("from-code", lambda n: chr(int(n)))
self.global_env.define("to-code", lambda ch: float(ord(ch[0])))
```

- [ ] **步骤 4：运行测试验证通过**

运行：`python -m pytest tests/test_evaluator.py::TestToCode -v`
预期：PASS（5 个测试）

- [ ] **步骤 5：运行全套测试确认无回归**

运行：`python -m pytest --tb=short -q`
预期：274 passed（269 + 5 新增）

- [ ] **步骤 6：Commit**

```bash
git add src/evaluator.py tests/test_evaluator.py
git commit -m "feat(bootstrap): 新增 to-code 原语（与 from-code 对称）"
```

---

## 任务 2：重构 _load_cent_module 脱离 .py 依赖

**文件：**
- 修改：`src/evaluator.py`（`_load_cent_module` 方法，约第 137-175 行）

- [ ] **步骤 1：阅读当前 _load_cent_module 实现**

运行：用 Read 工具查看 `src/evaluator.py` 第 137-180 行，确认当前从 `src/std/collection.py` 和 `src/std/math.py` 导入 FUNCTIONS。

- [ ] **步骤 2：重构 _load_cent_module**

将 `src/evaluator.py` 中 `_load_cent_module` 方法替换为：

```python
def _load_cent_module(self, module_name):
    """加载 Cento 源文件实现的标准库模块。
    返回 {name: callable} 字典。失败时抛异常由调用方处理。
    子 evaluator 共享当前 global_env 的所有绑定（脱离 .py 依赖）。
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

    # 子 evaluator 共享当前 env 的所有原语（不再从 .py 导入）
    sub_evaluator = Evaluator(skip_std=True)
    for name, val in self.global_env.bindings.items():
        sub_evaluator.global_env.define(name, val)

    prior_bindings = set(sub_evaluator.global_env.bindings.keys())
    for expr in ast.expressions:
        sub_evaluator.evaluate(expr)

    exports = {}
    for name, value in sub_evaluator.global_env.bindings.items():
        if name and name[0].isupper() and name not in prior_bindings:
            exports[name] = value
    return exports
```

- [ ] **步骤 3：运行现有 .ct 加载测试验证**

运行：`python -m pytest tests/test_bootstrap.py -v`
预期：PASS（所有现有自举测试通过，说明 seq.ct/util.ct/collection.ct 加载正常）

- [ ] **步骤 4：运行全套测试确认无回归**

运行：`python -m pytest --tb=short -q`
预期：274 passed

- [ ] **步骤 5：Commit**

```bash
git add src/evaluator.py
git commit -m "refactor(bootstrap): _load_cent_module 共享当前 env 绑定，脱离 .py 依赖"
```

---

## 任务 3：创建 string.ct 自举（15 个函数）

**文件：**
- 创建：`src/std/string.ct`
- 测试：`tests/test_bootstrap.py`（追加 TestStringBootstrap 类）

- [ ] **步骤 1：编写来源验证测试（先验证当前 string 函数来自 Python）**

在 `tests/test_bootstrap.py` 末尾追加：

```python
class TestStringBootstrap:
    """string.ct 自举来源验证"""

    def test_string_ct_functions_from_ct(self):
        """验证 string 纯逻辑函数来自 .ct（Fn 类型）"""
        from src.types import Fn
        e = Evaluator()
        for name in ["Has-prefix", "Has-suffix", "Substr", "Index-of",
                     "Includes", "Reverse-str", "Repeat", "Join", "Split",
                     "Split-lines", "Trim", "Upper", "Lower", "Replace", "Len"]:
            assert isinstance(e.global_env.lookup(name), Fn), \
                f"{name} 应来自 string.ct（Fn 类型），实际为 {type(e.global_env.lookup(name))}"

    def test_string_primitives_from_python(self):
        """验证 string 原语来自 evaluator（Python callable，非 Fn）"""
        from src.types import Fn
        e = Evaluator()
        for name in ["char-at", "substring", "from-code", "to-code",
                     "digit?", "alpha?", "space?", "parse-number"]:
            val = e.global_env.lookup(name)
            assert not isinstance(val, Fn), f"{name} 应为 Python callable"
            assert callable(val), f"{name} 应为 callable"

    def test_to_code_available(self):
        """验证 to-code 原语已注册"""
        assert eval_str('(to-code "A")') == 65.0
```

- [ ] **步骤 2：运行测试验证失败**

运行：`python -m pytest tests/test_bootstrap.py::TestStringBootstrap -v`
预期：FAIL（string.ct 不存在，Has-prefix 等仍来自 string.py 的 Python 函数，非 Fn 类型）

- [ ] **步骤 3：创建 string.ct 文件**

创建 `src/std/string.ct`：

```lisp
; string.ct - 字符串操作自举实现（15 个函数）
; 依赖原语：char-at, substring, from-code, to-code, digit?, alpha?, space?,
;           parse-number, count, Concat, str, >=, <=, >, <, +, -, =, !=, and, or

; 1. Len - 复用 count 原语
(fn Len [s] (count s))

; 2. Has-prefix - 逐字符比较前缀
(fn Has-prefix-helper [s prefix i]
  (if (>= i (count prefix))
    true
    (if (!= (char-at s i) (char-at prefix i))
      false
      (Has-prefix-helper s prefix (+ i 1)))))

(fn Has-prefix [s prefix]
  (if (> (count prefix) (count s))
    false
    (Has-prefix-helper s prefix 0)))

; 3. Has-suffix - 基于 substring + Has-prefix
(fn Has-suffix [s suffix]
  (let [s-len (count s)
        suf-len (count suffix)
        offset (- s-len suf-len)]
    (if (< offset 0)
      false
      (Has-prefix (substring s offset) suffix 0))))

; 4. Substr - 复用 substring 原语
(fn Substr [s start end] (substring s start end))

; 5. Index-of - 子串搜索
(fn Index-of-helper [s sub i n sub-len]
  (if (> (+ i sub-len) n)
    -1.0
    (if (Has-prefix (substring s i) sub)
      (float i)
      (Index-of-helper s sub (+ i 1) n sub-len))))

(fn Index-of [s sub]
  (Index-of-helper s sub 0 (count s) (count sub)))

; 6. Includes - 基于 Index-of
(fn Includes [s sub] (!= (Index-of s sub) -1.0))

; 7. Reverse-str - 累加器式逆序
(fn Reverse-str-helper [s i acc]
  (if (< i 0)
    acc
    (Reverse-str-helper s (- i 1) (Concat [acc] [(char-at s i)]))))

(fn Reverse-str [s]
  (Reverse-str-helper s (- (count s) 1) ""))

; 8. Repeat - 累加器式重复
(fn Repeat-helper [s n acc]
  (if (<= n 0)
    acc
    (Repeat-helper s (- n 1) (Concat [acc] [s]))))

(fn Repeat [s n] (Repeat-helper s n ""))

; 9. Join - 用 Reduce 拼接
(fn Join [lst sep]
  (Reduce (fn [acc x]
            (if (= acc "")
              (str x)
              (Concat [acc] [sep] [(str x)])))
          "" lst))

; 10. Split - 逐字符检测分隔符
(fn Split-helper [s sep i start acc]
  (let [n (count s)
        sep-len (count sep)]
    (if (> (+ i sep-len) n)
      (Concat acc [(substring s start)])
      (if (Has-prefix (substring s i) sep)
        (Split-helper s sep (+ i sep-len) (+ i sep-len)
                      (Concat acc [(substring s start i)]))
        (Split-helper s sep (+ i 1) start acc)))))

(fn Split [s sep]
  (if (= sep "")
    [s]
    (Split-helper s sep 0 0 [])))

; 11. Split-lines - 检测换行符
(fn Split-lines-helper [s i start acc]
  (if (>= i (count s))
    (Concat acc [(substring s start)])
    (if (= (char-at s i) "\n")
      (Split-lines-helper s (+ i 1) (+ i 1)
                          (Concat acc [(substring s start i)]))
      (Split-lines-helper s (+ i 1) start acc))))

(fn Split-lines [s] (Split-lines-helper s 0 0 []))

; 12. Trim - 裁剪前导后缀空白
(fn Trim-left [s i]
  (if (>= i (count s))
    s
    (if (space? (char-at s i))
      (Trim-left s (+ i 1))
      (substring s i))))

(fn Trim-right [s i]
  (if (< i 0)
    s
    (if (space? (char-at s i))
      (Trim-right s (- i 1))
      (substring s 0 (+ i 1)))))

(fn Trim [s]
  (let [left-trimmed (Trim-left s 0)]
    (Trim-right left-trimmed (- (count left-trimmed) 1))))

; 13. Upper - ASCII 大写转换（a-z → A-Z）
(fn Upper-char [ch]
  (if (and (>= ch "a") (<= ch "z"))
    (from-code (- (to-code ch) 32))
    ch))

(fn Upper-helper [s i n acc]
  (if (>= i n)
    acc
    (Upper-helper s (+ i 1) n (Concat [acc] [(Upper-char (char-at s i))]))))

(fn Upper [s]
  (Upper-helper s 0 (count s) ""))

; 14. Lower - ASCII 小写转换（A-Z → a-z）
(fn Lower-char [ch]
  (if (and (>= ch "A") (<= ch "Z"))
    (from-code (+ (to-code ch) 32))
    ch))

(fn Lower-helper [s i n acc]
  (if (>= i n)
    acc
    (Lower-helper s (+ i 1) n (Concat [acc] [(Lower-char (char-at s i))]))))

(fn Lower [s]
  (Lower-helper s 0 (count s) ""))

; 15. Replace - 子串搜索 + 替换
(fn Replace-helper [s old new start acc]
  (let [remaining (substring s start)
        idx (Index-of remaining old)]
    (if (= idx -1.0)
      (Concat [acc] [remaining])
      (let [abs-idx (+ start idx)
            new-acc (Concat [acc] [(substring s start abs-idx)] [new])]
        (Replace-helper s old new (+ abs-idx (count old)) new-acc)))))

(fn Replace [s old new]
  (if (= old "")
    s
    (Replace-helper s old new 0 "")))
```

- [ ] **步骤 4：在 evaluator 中注册 string.ct 加载**

在 `src/evaluator.py` 的 `_register_builtins` 方法中，在 seq/util 加载区块之前（或之后）添加 string.ct 加载。找到 `# std/seq (Cento 优先，Python fallback)` 注释，在其前添加：

```python
            # std/string（Cento 自举，原语已注册）
            try:
                string_exports = self._load_cent_module("string")
                for name, fn in string_exports.items():
                    self.global_env.define(name, fn, exported=True)
            except Exception as e:
                import sys
                print(f"[bootstrap] string.ct 加载失败: {e}", file=sys.stderr)
                raise
```

同时确保 string 原语已注册（若任务 1 未注册 from-code/to-code 等，在此补充）。在 `_register_builtins` 的 Error 注册后添加 string 原语区块：

```python
            # string 原语（宿主层，供 string.ct 依赖）
            self.global_env.define("char-at", lambda s, i: s[int(i)])
            def _substring(s, start, end=None):
                return s[int(start):] if end is None else s[int(start):int(end)]
            self.global_env.define("substring", _substring)
            self.global_env.define("from-code", lambda n: chr(int(n)))
            self.global_env.define("to-code", lambda ch: float(ord(ch[0])))
            self.global_env.define("digit?", lambda ch: len(ch) == 1 and ch in "0123456789")
            self.global_env.define("alpha?", lambda ch: len(ch) == 1 and ch.isalpha() and ch.isascii())
            self.global_env.define("space?", lambda ch: len(ch) == 1 and ch.isspace() and ch.isascii())
            def _parse_number(s):
                try:
                    return float(s)
                except (ValueError, TypeError):
                    raise CentoError(f"Cannot parse number: {s}")
            self.global_env.define("parse-number", _parse_number)
```

注：原语注册必须在 string.ct 加载之前执行。

- [ ] **步骤 5：运行 string 来源验证测试**

运行：`python -m pytest tests/test_bootstrap.py::TestStringBootstrap -v`
预期：PASS（15 个函数来自 Fn，8 个原语来自 Python）

- [ ] **步骤 6：运行 string 行为测试验证一致性**

运行：`python -m pytest tests/test_std_string.py tests/test_std.py -v`
预期：PASS（所有现有 string 测试通过，说明 .ct 实现行为一致）

- [ ] **步骤 7：删除 string.py**

删除 `src/std/string.py`。

- [ ] **步骤 8：运行全套测试确认无回归**

运行：`python -m pytest --tb=short -q`
预期：277 passed（274 + 3 新增来源验证）

- [ ] **步骤 9：Commit**

```bash
git add src/std/string.ct src/evaluator.py tests/test_bootstrap.py
git rm src/std/string.py
git commit -m "feat(bootstrap): string.ct 自举 15 个函数，删除 string.py"
```

---

## 任务 4：util.ct 新增 Comp，删除 util.py

**文件：**
- 修改：`src/std/util.ct`（追加 Comp）
- 修改：`src/evaluator.py`（注册 Apply，移除 util.py fallback）
- 删除：`src/std/util.py`
- 测试：`tests/test_bootstrap.py`（修正 TestMixedImplementation）

- [ ] **步骤 1：在 util.ct 追加 Comp**

在 `src/std/util.ct` 末尾追加：

```lisp
; Comp - 函数组合 (Comp f g h) => x -> f(g(h(x)))
; 依赖 Reverse（来自 seq.ct，_load_cent_module 共享 env 时可用）
(fn Comp-helper [fns x]
  (if (empty? fns)
    x
    (Comp-helper (rest fns) ((first fns) x))))

(fn Comp [& fns]
  (fn [x] (Comp-helper (Reverse fns) x)))
```

- [ ] **步骤 2：在 evaluator 注册 Apply 别名**

在 `src/evaluator.py` 的 `_register_builtins` 中，找到 `apply` 注册行，在其后添加 Apply 别名：

```python
        self.global_env.define("apply", lambda fn, args: self._apply(fn, list(args)))
        self.global_env.define("Apply", lambda fn, args: self._apply(fn, list(args)))
```

- [ ] **步骤 3：移除 util.py fallback 逻辑**

在 `src/evaluator.py` 的 `_register_builtins` 中，找到 `# std/util (Cento 优先，Python fallback)` 区块，替换为纯 .ct 加载（删除 try/except 和 util.py 导入）：

```python
            # std/util（Cento 自举）
            util_exports = self._load_cent_module("util")
            for name, fn in util_exports.items():
                self.global_env.define(name, fn, exported=True)
```

- [ ] **步骤 4：修正 test_bootstrap.py 过时测试**

在 `tests/test_bootstrap.py` 的 `TestMixedImplementation` 类中，`test_util_has_both_ct_and_python` 测试描述已过时（Comp 现来自 util.ct）。修改为：

```python
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
```

同样修正 `test_seq_has_both_ct_and_python`（Sort 现来自 seq.ct）：

```python
    def test_seq_has_both_ct_and_python(self):
        """seq 模块：Take 和 Sort 均来自 seq.ct，验证协同工作"""
        # Take 来自 seq.ct
        assert list(eval_str("(Take 2 [3 1 2])")) == [3.0, 1.0]
        # Sort 来自 seq.ct（已自举，归并排序）
        assert list(eval_str("(Sort [3 1 2])")) == [1.0, 2.0, 3.0]
        # 组合：先排序再取前 2 个
        assert list(eval_str("(Take 2 (Sort [3 1 2]))")) == [1.0, 2.0]
```

- [ ] **步骤 5：删除 util.py**

删除 `src/std/util.py`。

- [ ] **步骤 6：运行测试验证**

运行：`python -m pytest tests/test_bootstrap.py tests/test_std.py -v`
预期：PASS

- [ ] **步骤 7：运行全套测试确认无回归**

运行：`python -m pytest --tb=short -q`
预期：277 passed

- [ ] **步骤 8：Commit**

```bash
git add src/std/util.ct src/evaluator.py tests/test_bootstrap.py
git rm src/std/util.py
git commit -m "feat(bootstrap): util.ct 新增 Comp，删除 util.py"
```

---

## 任务 5：collection 宿主移入 evaluator，删除 collection.py

**文件：**
- 修改：`src/evaluator.py`（注册 Concat/Assoc/Dissoc/Keys/Values/Merge）
- 删除：`src/std/collection.py`

- [ ] **步骤 1：在 evaluator 注册 collection 宿主函数**

在 `src/evaluator.py` 的 `_register_builtins` 中，找到 `# std/collection` 区块，替换为宿主注册（保留 collection.ct 加载，但 Concat/Assoc 等从 .py 移入）：

```python
            # collection 宿主函数（无法自举：需 CentoMap 构造）
            from src.types import CentoList, CentoMap
            def _concat(*lists):
                result = []
                for lst in lists:
                    result.extend(lst)
                return CentoList(result)
            self.global_env.define("Concat", _concat)
            def _assoc(m, k, v):
                new_m = CentoMap(dict(m))
                new_m[k] = v
                return new_m
            self.global_env.define("Assoc", _assoc)
            def _dissoc(m, k):
                new_m = CentoMap(dict(m))
                new_m.pop(k, None)
                return new_m
            self.global_env.define("Dissoc", _dissoc)
            self.global_env.define("Keys", lambda m: CentoList(list(m.keys())))
            self.global_env.define("Values", lambda m: CentoList(list(m.values())))
            def _merge(*maps):
                result = {}
                for m in maps:
                    result.update(m)
                return CentoMap(result)
            self.global_env.define("Merge", _merge)
            # collection.ct 自举（Map/Filter/Reduce/Each/Contains）
            collection_exports = self._load_cent_module("collection")
            for name, fn in collection_exports.items():
                self.global_env.define(name, fn, exported=True)
```

注：宿主函数必须先于 collection.ct 加载注册，因为 collection.ct 依赖 Concat。

- [ ] **步骤 2：删除 collection.py**

删除 `src/std/collection.py`。

- [ ] **步骤 3：运行测试验证**

运行：`python -m pytest tests/test_std.py tests/test_bootstrap.py -v`
预期：PASS

- [ ] **步骤 4：运行全套测试确认无回归**

运行：`python -m pytest --tb=short -q`
预期：277 passed

- [ ] **步骤 5：Commit**

```bash
git add src/evaluator.py
git rm src/std/collection.py
git commit -m "feat(bootstrap): collection 宿主移入 evaluator，删除 collection.py"
```

---

## 任务 6：math 宿主移入 evaluator，删除 math.py

**文件：**
- 修改：`src/evaluator.py`（注册 16 个 math 函数 + 常量）
- 删除：`src/std/math.py`

- [ ] **步骤 1：在 evaluator 注册 math 宿主函数**

在 `src/evaluator.py` 的 `_register_builtins` 中，找到 `# std/math` 区块，替换为：

```python
            # math 宿主（需 Python math 库）
            import math as _math
            self.global_env.define("Sin", lambda x: _math.sin(x))
            self.global_env.define("Cos", lambda x: _math.cos(x))
            self.global_env.define("Tan", lambda x: _math.tan(x))
            self.global_env.define("Asin", lambda x: _math.asin(x))
            self.global_env.define("Acos", lambda x: _math.acos(x))
            self.global_env.define("Atan", lambda x: _math.atan(x))
            self.global_env.define("Exp", lambda x: _math.exp(x))
            self.global_env.define("Log", lambda x: _math.log(x))
            self.global_env.define("Log10", lambda x: _math.log10(x))
            self.global_env.define("Sqrt", lambda x: _math.sqrt(x))
            self.global_env.define("Pow", lambda base, exp: _math.pow(base, exp))
            self.global_env.define("Floor", lambda x: float(_math.floor(x)))
            self.global_env.define("Ceil", lambda x: float(_math.ceil(x)))
            self.global_env.define("Round", lambda x: float(round(x)))
            self.global_env.define("Pi", _math.pi)
            self.global_env.define("E", _math.e)
```

- [ ] **步骤 2：删除 math.py**

删除 `src/std/math.py`。

- [ ] **步骤 3：运行测试验证**

运行：`python -m pytest tests/test_std.py tests/test_integration.py -v`
预期：PASS

- [ ] **步骤 4：运行全套测试确认无回归**

运行：`python -m pytest --tb=short -q`
预期：277 passed

- [ ] **步骤 5：Commit**

```bash
git add src/evaluator.py
git rm src/std/math.py
git commit -m "feat(bootstrap): math 宿主移入 evaluator，删除 math.py"
```

---

## 任务 7：io/fs/mutable 宿主移入 evaluator，删除对应 .py

**文件：**
- 修改：`src/evaluator.py`（注册 io 3 个 + fs 5 个 + mutable 9 个）
- 删除：`src/std/io.py`、`src/std/fs.py`、`src/std/mutable.py`

- [ ] **步骤 1：在 evaluator 注册 io/fs/mutable 宿主函数**

在 `src/evaluator.py` 的 `_register_builtins` 中，找到 `# std/mutable`、`# std/io`、`# std/fs` 区块，替换为：

```python
            # io 宿主（需 OS I/O）
            import sys as _sys
            def _read_line():
                return _sys.stdin.readline().rstrip("\n")
            def _read_file(path):
                with open(path, "r", encoding="utf-8") as f:
                    return f.read()
            def _write_file(path, content):
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                return None
            self.global_env.define("Read-line", _read_line)
            self.global_env.define("Read-file", _read_file)
            self.global_env.define("Write-file", _write_file)

            # fs 宿主（需 OS 调用）
            import os as _os
            import shutil as _shutil
            self.global_env.define("Exists?", lambda p: _os.path.exists(p))
            self.global_env.define("Is-dir?", lambda p: _os.path.isdir(p))
            def _list_dir(p):
                return CentoList(_os.listdir(p))
            self.global_env.define("List-dir", _list_dir)
            def _mkdir(p):
                _os.makedirs(p, exist_ok=True)
                return None
            self.global_env.define("Mkdir", _mkdir)
            def _rmdir(p):
                if _os.path.isdir(p):
                    _shutil.rmtree(p)
                else:
                    _os.remove(p)
                return None
            self.global_env.define("Rmdir", _rmdir)

            # mutable 宿主（需可变数据结构类型）
            from src.types import Ref, CentoArray, MutableMap
            self.global_env.define("Ref", lambda v: Ref(v))
            self.global_env.define("Ref-get", lambda r: r.value)
            def _ref_set(r, v):
                r.value = v
                return v
            self.global_env.define("Ref-set!", _ref_set)
            self.global_env.define("Array", lambda size: CentoArray(int(size)))
            self.global_env.define("Array-get", lambda arr, i: arr.data[int(i)])
            def _array_set(arr, i, v):
                arr.data[int(i)] = v
                return v
            self.global_env.define("Array-set!", _array_set)
            self.global_env.define("Mutable-map", lambda: MutableMap())
            self.global_env.define("Mutable-map-get", lambda m, k: m.data.get(k))
            def _mutable_map_set(m, k, v):
                m.data[k] = v
                return v
            self.global_env.define("Mutable-map-set!", _mutable_map_set)
```

- [ ] **步骤 2：删除 io.py、fs.py、mutable.py**

删除 `src/std/io.py`、`src/std/fs.py`、`src/std/mutable.py`。

- [ ] **步骤 3：运行测试验证**

运行：`python -m pytest --tb=short -q`
预期：277 passed

- [ ] **步骤 4：Commit**

```bash
git add src/evaluator.py
git rm src/std/io.py src/std/fs.py src/std/mutable.py
git commit -m "feat(bootstrap): io/fs/mutable 宿主移入 evaluator，删除对应 .py"
```

---

## 任务 8：删除 seq.py，清理 fallback 逻辑

**文件：**
- 修改：`src/evaluator.py`（移除 seq.py fallback，简化 seq 加载）
- 删除：`src/std/seq.py`

- [ ] **步骤 1：简化 seq 加载逻辑**

在 `src/evaluator.py` 的 `_register_builtins` 中，找到 `# std/seq (Cento 优先，Python fallback)` 区块，替换为纯 .ct 加载：

```python
            # std/seq（Cento 自举）
            seq_exports = self._load_cent_module("seq")
            for name, fn in seq_exports.items():
                self.global_env.define(name, fn, exported=True)
```

- [ ] **步骤 2：删除 seq.py**

删除 `src/std/seq.py`。

- [ ] **步骤 3：运行测试验证**

运行：`python -m pytest --tb=short -q`
预期：277 passed

- [ ] **步骤 4：验证无 fallback 日志**

运行：`python -c "from src.evaluator import Evaluator; Evaluator()" 2>&1`
预期：无输出（无 "[bootstrap] xxx.ct 加载失败" 日志）

- [ ] **步骤 5：验证 std 目录无 .py 文件**

运行：`ls src/std/`
预期：只有 `__init__.py`、`collection.ct`、`seq.ct`、`util.ct`、`string.ct`

- [ ] **步骤 6：Commit**

```bash
git add src/evaluator.py
git rm src/std/seq.py
git commit -m "feat(bootstrap): 删除 seq.py，移除 Python fallback 逻辑"
```

---

## 任务 9：最终验证与推送

- [ ] **步骤 1：运行全套测试**

运行：`python -m pytest --tb=short -q`
预期：277 passed

- [ ] **步骤 2：验证成功标准**

运行以下命令逐一验证：

```bash
# 1. std 目录无 .py（除 __init__.py）
ls src/std/
# 预期：__init__.py collection.ct seq.ct string.ct util.ct

# 2. 来源验证（纯逻辑函数为 Fn）
python -c "
from src.evaluator import Evaluator
from src.types import Fn
e = Evaluator()
ct_funcs = ['Has-prefix', 'Join', 'Upper', 'Inc', 'Comp', 'Map', 'Sort', 'Take']
for name in ct_funcs:
    assert isinstance(e.global_env.lookup(name), Fn), f'{name} 应为 Fn'
py_funcs = ['Sin', 'Sqrt', 'Concat', 'Apply', 'char-at', 'to-code', 'Read-file', 'Ref']
for name in py_funcs:
    assert not isinstance(e.global_env.lookup(name), Fn), f'{name} 应为 Python callable'
print('来源验证通过')
"
```

- [ ] **步骤 3：推送到远程**

```bash
git push
```

- [ ] **步骤 4：最终 Commit（如有未提交变更）**

若上述步骤均已 commit，此步骤可跳过。否则：

```bash
git add -A
git commit -m "chore(bootstrap): 标准库彻底自举完成"
git push
```

---

## 自检结果

### 规格覆盖度
- ✅ string.ct 15 个函数 → 任务 3
- ✅ util.ct Comp → 任务 4
- ✅ to-code 原语 → 任务 1
- ✅ _load_cent_module 重构 → 任务 2
- ✅ collection 宿主移入 → 任务 5
- ✅ math 宿主移入 → 任务 6
- ✅ io/fs/mutable 宿主移入 → 任务 7
- ✅ seq.py 删除 + fallback 清理 → 任务 8
- ✅ 最终验证 → 任务 9
- ✅ 来源验证测试 → 任务 3 步骤 1

### 占位符扫描
- 无 "TODO"、"待定" 等
- 所有代码步骤均含完整代码

### 类型一致性
- `to-code` 在任务 1 定义，任务 3 string.ct 使用，签名一致
- `Concat` 在任务 5 注册，任务 3 string.ct 已依赖（string.ct 加载时 Concat 已从 collection.py 提供，任务 5 后从 evaluator 提供，行为一致）
- `Apply` 在任务 4 注册，与已有 `apply` 行为一致

### 潜在问题
- **任务 3 依赖顺序**：string.ct 加载时需要 `Concat`（来自 collection.py）和 `Reduce`（来自 collection.ct）。任务 3 执行时 collection.py 仍存在，Concat 可用。任务 5 删除 collection.py 时 Concat 已移入 evaluator，无断裂。
- **任务 3 与任务 5 顺序**：任务 3 在任务 5 之前执行，确保 string.ct 加载时 collection.py 的 Concat 仍可用。任务 5 删除 collection.py 前 Concat 已移入 evaluator。
