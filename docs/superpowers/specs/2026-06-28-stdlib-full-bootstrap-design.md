# 标准库彻底自举设计

**日期**: 2026-06-28
**状态**: 已批准
**目标**: 删除 `src/std/` 下所有 `.py` 文件，将函数分为两类：`.ct` 自举（纯逻辑）+ `evaluator.py` 宿主原语（需要 Python 能力）。

## 背景与动机

当前 `src/std/` 目录包含 8 个 `.py` 文件和 3 个 `.ct` 文件。`.ct` 文件是 Cento 自举实现，`.py` 文件是 Python 原生实现。部分模块（seq、util、collection）已有 `.ct` 自举，但 `.py` 文件仍作为 fallback 保留。

本设计的目标是彻底完成自举，移除所有 `.py` 文件，让 Cento 标准库的纯逻辑部分完全由 Cento 语言实现，宿主能力集中到 `evaluator.py`。

## 约束

### 来自 project_memory 的硬约束
- `Apply` 和 `Concat` 无法在 Cento 中完全实现（参数展开和列表构造限制）
- 核心原语用小写命名（`char-at`, `digit?` 等）
- Std 模块函数用大写命名（`Sin`, `Pi`, `Has-prefix` 等）
- `parse-number` 失败时抛 `CentoError`
- 字符分类原语（`digit?`, `alpha?`, `space?`）限于 ASCII

### 语言能力约束
- Cento 没有"从动态键值对构造 CentoMap"的原语（只有 `{:k v}` 字面量，键必须是编译时常量）
- 因此 `Assoc`/`Dissoc`/`Keys`/`Values`/`Merge` 无法自举，必须移入 evaluator
- `math` 函数需要 Python `math` 库（三角函数、对数等）
- `io`/`fs` 需要 OS 系统调用
- `mutable` 需要可变数据结构类型（`Ref`/`CentoArray`/`MutableMap`）

## 架构

### 最终文件结构
```
src/
├── evaluator.py          # 宿主原语注册（47 个函数）
├── std/
│   ├── collection.ct     # 5 个（Map/Filter/Reduce/Each/Contains）
│   ├── seq.ct            # 13 个（已完整自举）
│   ├── util.ct           # 11 个（新增 Comp）
│   └── string.ct         # 15 个（新增文件）
```

### 函数分布（共 ~87 个函数）

| 位置 | 函数数 | 说明 |
|------|--------|------|
| `.ct` 自举 | 40 | collection 5 + seq 13 + util 11 + string 15 - 4 重叠¹ = 40 |
| evaluator 宿主 | 48 | math 16 + io 3 + fs 5 + mutable 9 + collection 6 + Apply 1 + string 原语 7 + to-code 1 = 48 |

¹ string 的 `Len` 与已有 `count` 原语功能相同，`Len` 在 `.ct` 中定义为 `(fn Len [s] (count s))`，复用原语不重复计数。`Apply` 与已有 `apply` 原语功能相同，但作为大写别名单独注册。

## 详细设计

### 1. string.ct（新增，15 个函数）

依赖原语（移入 evaluator）：`char-at`, `substring`, `from-code`, `to-code`（新增）, `digit?`, `alpha?`, `space?`, `parse-number`, `count`（已有）, `Concat`（已有）, `str`（已有）

#### 函数清单

1. **Len** - 复用 count 原语
2. **Has-prefix** - 逐字符比较前缀
3. **Has-suffix** - 基于 substring + Has-prefix
4. **Substr** - 复用 substring 原语
5. **Index-of** - 子串搜索（逐位置检测前缀匹配）
6. **Includes** - 基于 Index-of
7. **Reverse-str** - 累加器式逆序
8. **Repeat** - 累加器式重复
9. **Join** - 用 Reduce 拼接
10. **Split** - 逐字符检测分隔符
11. **Split-lines** - 检测换行符
12. **Trim** - 裁剪前导后缀空白（Trim-left + Trim-right）
13. **Upper** - ASCII 大写转换（a-z → A-Z，用 to-code/from-code）
14. **Lower** - ASCII 小写转换（A-Z → a-z）
15. **Replace** - 子串搜索 + 替换（循环 Index-of + substring）

#### 关键实现细节

**Upper/Lower 实现**：
```lisp
(fn Upper-char [ch]
  (if (and (>= ch "a") (<= ch "z"))
    (from-code (- (to-code ch) 32))
    ch))
(fn Upper [s]
  (Upper-helper s 0 (count s) ""))
```
需要新增 `to-code` 原语（`ord()`），与 `from-code` 对称。

**Replace 实现**：
```lisp
(fn Replace-helper [s old new start acc]
  (let [idx (Index-of (substring s start) old)]
    (if (= idx -1.0)
      (Concat [acc (substring s start)])
      (let [abs-idx (+ start idx)
            new-acc (Concat [acc (substring s start abs-idx) new])]
        (Replace-helper s old new (+ abs-idx (count old)) new-acc)))))
(fn Replace [s old new]
  (if (= old "")
    s
    (Replace-helper s old new 0 "")))
```

### 2. util.ct 新增（1 个函数）

**Comp** - 函数组合 `(Comp f g h) => x -> f(g(h(x)))`
```lisp
(fn Comp-helper [fns x]
  (if (empty? fns)
    x
    (Comp-helper (rest fns) ((first fns) x))))
(fn Comp [& fns]
  (fn [x] (Comp-helper (Reverse fns) x)))
```

**依赖问题**：`Comp` 依赖 `Reverse`（在 seq.ct 中）。解决方案：`_load_cent_module` 重构后，子 evaluator 共享当前 env 的所有绑定（包括已注册的 seq 函数），因此 `Reverse` 可用。

### 3. collection.ct

无新增。已有 5 个函数（Map/Filter/Reduce/Each/Contains）保持不变。

Assoc/Dissoc/Keys/Values/Merge/Concat 移入 evaluator（无法自举，需要 CentoMap 构造能力）。

## evaluator 宿主原语设计

### 新增原语（1 个）
```python
self.global_env.define("to-code", lambda ch: float(ord(ch[0])))
```

### 按模块分组注册（47 个函数）

#### math 宿主（16 个）
```python
import math
self.global_env.define("Sin", lambda x: math.sin(x))
self.global_env.define("Cos", lambda x: math.cos(x))
# Tan, Asin, Acos, Atan, Exp, Log, Log10, Sqrt, Pow, Floor, Ceil, Round
self.global_env.define("Pi", math.pi)  # 常量
self.global_env.define("E", math.e)    # 常量
```

#### io 宿主（3 个）
```python
import sys
def _read_line(): return sys.stdin.readline().rstrip("\n")
def _read_file(path):
    with open(path, "r", encoding="utf-8") as f: return f.read()
def _write_file(path, content):
    with open(path, "w", encoding="utf-8") as f: f.write(content)
    return None
```

#### fs 宿主（5 个）
```python
import os, shutil
self.global_env.define("Exists?", lambda p: os.path.exists(p))
self.global_env.define("Is-dir?", lambda p: os.path.isdir(p))
def _list_dir(p): return CentoList(os.listdir(p))
def _mkdir(p): os.makedirs(p, exist_ok=True); return None
def _rmdir(p):
    if os.path.isdir(p): shutil.rmtree(p)
    else: os.remove(p)
    return None
```

#### mutable 宿主（9 个）
```python
from src.types import Ref, CentoArray, MutableMap
self.global_env.define("Ref", lambda v: Ref(v))
self.global_env.define("Ref-get", lambda r: r.value)
def _ref_set(r, v): r.value = v; return v
self.global_env.define("Ref-set!", _ref_set)
self.global_env.define("Array", lambda size: CentoArray(int(size)))
self.global_env.define("Array-get", lambda arr, i: arr.data[int(i)])
def _array_set(arr, i, v): arr.data[int(i)] = v; return v
self.global_env.define("Array-set!", _array_set)
self.global_env.define("Mutable-map", lambda: MutableMap())
self.global_env.define("Mutable-map-get", lambda m, k: m.data.get(k))
def _mutable_map_set(m, k, v): m.data[k] = v; return v
self.global_env.define("Mutable-map-set!", _mutable_map_set)
```

#### collection 宿主（6 个，需 CentoMap 构造）
```python
def _assoc(m, k, v):
    new_m = CentoMap(dict(m)); new_m[k] = v; return new_m
def _dissoc(m, k):
    new_m = CentoMap(dict(m)); new_m.pop(k, None); return new_m
def _keys(m): return CentoList(list(m.keys()))
def _values(m): return CentoList(list(m.values()))
def _merge(*maps):
    result = {}
    for m in maps: result.update(m)
    return CentoMap(result)
def _concat(*lists):
    result = []
    for lst in lists: result.extend(lst)
    return CentoList(result)
```

#### util 宿主（1 个）
```python
# Apply 与已有 apply 原语功能相同，注册为别名
self.global_env.define("Apply", lambda fn, args: self._apply(fn, list(args)))
```

#### string 原语宿主（7 个 + to-code 1 个 = 8 个）
```python
self.global_env.define("char-at", lambda s, i: s[int(i)])
def _substring(s, start, end=None):
    return s[int(start):] if end is None else s[int(start):int(end)]
self.global_env.define("substring", _substring)
self.global_env.define("from-code", lambda n: chr(int(n)))
self.global_env.define("to-code", lambda ch: float(ord(ch[0])))
self.global_env.define("digit?", lambda ch: len(ch) == 1 and ch in "0123456789")
def _alpha_q(ch): return len(ch) == 1 and ch.isalpha() and ch.isascii()
self.global_env.define("alpha?", _alpha_q)
def _space_q(ch): return len(ch) == 1 and ch.isspace() and ch.isascii()
self.global_env.define("space?", _space_q)
def _parse_number(s):
    try: return float(s)
    except (ValueError, TypeError): raise CentoError(f"Cannot parse number: {s}")
self.global_env.define("parse-number", _parse_number)
```

### _load_cent_module 重构

**关键改动**：不再从 `.py` 文件导入依赖，改为共享当前 `global_env` 的所有绑定：

```python
def _load_cent_module(self, module_name):
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

    # 子 evaluator 共享当前 env 的所有原语（不再依赖 .py）
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

**_register_builtins 简化**：删除所有 `try/except` Python fallback 逻辑，直接加载 `.ct`（失败则抛异常，不再回退）。

## 测试策略

### 测试分类

| 类别 | 测试文件 | 内容 |
|------|---------|------|
| 现有测试保持绿 | test_std_*.py, test_integration.py | 所有现有测试必须通过（验证行为一致性） |
| 来源验证 | test_bootstrap.py | 验证函数来自 .ct 而非 Python fallback |
| to-code 原语测试 | test_evaluator.py | 新增 to-code/from-code 对称性测试 |

### 关键测试点

**1. 来源验证（确保非 Python fallback）**：
```python
def test_string_functions_from_ct(self):
    from src.types import Fn
    e = Evaluator()
    assert isinstance(e.global_env.lookup("Has-prefix"), Fn)
    assert isinstance(e.global_env.lookup("Join"), Fn)
    assert isinstance(e.global_env.lookup("Upper"), Fn)
    assert not isinstance(e.global_env.lookup("char-at"), Fn)
    assert callable(e.global_env.lookup("char-at"))
```

**2. to-code 原语测试**：
```python
def test_to_code_basic(self):
    assert eval_str('(to-code "A")') == 65.0
    assert eval_str('(to-code "a")') == 97.0
def test_from_to_code_roundtrip(self):
    assert eval_str('(from-code (to-code "x"))') == "x"
```

**3. Upper/Lower 自举验证**：
```python
def test_upper_lowercase(self):
    assert eval_str('(Upper "hello")') == "HELLO"
    assert eval_str('(Lower "WORLD")') == "world"
def test_upper_non_alpha_passthrough(self):
    assert eval_str('(Upper "123!@")') == "123!@"
```

### 回归风险与缓解

| 风险 | 缓解 |
|------|------|
| Upper/Lower 用 char-at 循环实现，性能差 | 可接受，自举优先于性能 |
| Replace 实现复杂，边界情况多 | 现有 test_std_string.py 已有覆盖，补充边界测试 |
| Split 对多字符分隔符的处理 | 测试用例覆盖单字符和多字符分隔符 |
| _load_cent_module 重构破坏现有 .ct 加载 | 阶段 1 后立即验证 seq.ct/util.ct 加载 |

## 迁移与删除计划

### 文件变更清单

| 操作 | 文件 | 说明 |
|------|------|------|
| 新建 | src/std/string.ct | 15 个 string 函数自举实现 |
| 修改 | src/std/util.ct | 新增 Comp 函数 |
| 修改 | src/evaluator.py | 注册 47 个宿主原语 + to-code；_load_cent_module 重构 |
| 修改 | tests/test_evaluator.py | 新增 to-code 测试 |
| 修改 | tests/test_bootstrap.py | 新增 string.ct 来源验证测试 |
| 删除 | src/std/collection.py | 5 个已自举，6 个移入 evaluator |
| 删除 | src/std/seq.py | 13 个全部已自举 |
| 删除 | src/std/util.py | 10 个已自举，3 个移入 evaluator |
| 删除 | src/std/math.py | 16 个移入 evaluator |
| 删除 | src/std/string.py | 15 个自举，7 个移入 evaluator |
| 删除 | src/std/mutable.py | 9 个移入 evaluator |
| 删除 | src/std/io.py | 3 个移入 evaluator |
| 删除 | src/std/fs.py | 5 个移入 evaluator |

### 执行顺序（TDD）

**阶段 1：基础设施**
1. evaluator 新增 `to-code` 原语 + 测试
2. `_load_cent_module` 重构（脱离 .py 依赖）
3. 验证现有 seq.ct/util.ct/collection.ct 加载正常

**阶段 2：string.ct 自举**
4. 创建 string.ct，实现 15 个函数
5. evaluator 移入 7 个 string 原语 + to-code
6. 运行 test_std_string.py 验证行为一致
7. 删除 string.py
8. 运行全套测试

**阶段 3：util.ct 扩展**
9. util.ct 新增 Comp
10. evaluator 移入 Apply
11. 删除 util.py
12. 运行全套测试

**阶段 4：collection 宿主移入**
13. evaluator 移入 Concat/Assoc/Dissoc/Keys/Values/Merge
14. 删除 collection.py
15. 运行全套测试

**阶段 5：math/io/fs/mutable 宿主移入**
16. evaluator 移入 math 16 个，删除 math.py
17. evaluator 移入 io 3 个，删除 io.py
18. evaluator 移入 fs 5 个，删除 fs.py
19. evaluator 移入 mutable 9 个，删除 mutable.py
20. 运行全套测试

**阶段 6：清理与验证**
21. 删除 seq.py（已全部自举）
22. 验证 _load_cent_module 无 fallback 日志
23. 运行全套测试
24. commit

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| evaluator.py 膨胀（~150 行新增） | 可接受，比 8 个 .py 文件更集中 |
| _load_cent_module 重构破坏 .ct 加载 | 阶段 1 后立即验证，保留回退能力 |
| string.ct 递归深度（长字符串） | 依赖现有 TCO 优化，测试用例覆盖 |
| Upper/Lower/Replace 性能 | 自举优先于性能，可接受 |
| 删除 .py 后无法回退 | Git 版本控制可回退 |

## 成功标准

1. `src/std/` 下无 `.py` 文件（只有 `__init__.py`）
2. 全套测试通过（269+ 测试）
3. string/util/collection/seq 的纯逻辑函数来源为 `Fn`（Cento 函数）
4. math/io/fs/mutable/Concat/Apply/char-at 等来源为 Python callable
5. `_load_cent_module` 无 Python fallback 日志
