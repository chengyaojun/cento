# 标准库自举扩展 - collection 模块实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 用 Cento 语言实现 collection 模块中 5 个列表操作函数（Map/Filter/Reduce/Each/Contains），复用现有 Cento 优先 + Python fallback 加载机制。

**架构：** 新增 `src/std/collection.ct` 文件实现 5 个函数；修改 evaluator 的 collection 注册段为 Cento 优先 + Python fallback；`_load_cent_module` 中为 collection.ct 注册 Concat 依赖；新增 bootstrap 测试验证加载机制。

**技术栈：** Cento 语言（S-expression、let/fn/if/递归/TCO、nil 字面量）、Python（解释器、fallback）、pytest

---

## 文件结构

| 文件 | 职责 | 操作 |
|------|------|------|
| `src/std/collection.ct` | Cento 实现 5 个列表操作函数 | 新建 |
| `src/evaluator.py` | collection 注册段改为 Cento 优先 + Python fallback；`_load_cent_module` 增加 collection 依赖处理 | 修改 |
| `tests/test_bootstrap.py` | 添加 collection 自举验证测试 | 修改 |
| `src/std/collection.py` | Python fallback（保留 6 个不可自举函数） | 保留 |
| `tests/test_std_collection.py` | 复用现有测试验证 Cento 实现 | 保留 |

---

### 任务 1：创建 collection.ct

**文件：**
- 创建：`src/std/collection.ct`

- [ ] **步骤 1：编写 collection.ct**

```lisp
; collection.ct - Cento 自举实现（5 个列表操作函数）
; 依赖：first, rest, empty?, nil, Concat（原生注册）

(fn Map [f xs]
  (if (empty? xs)
    []
    (Concat [(f (first xs))] (Map f (rest xs)))))

(fn Filter [pred xs]
  (if (empty? xs)
    []
    (if (pred (first xs))
      (Concat [(first xs)] (Filter pred (rest xs)))
      (Filter pred (rest xs)))))

(fn Reduce [f init xs]
  (if (empty? xs)
    init
    (Reduce f (f init (first xs)) (rest xs))))

(fn Each-helper [f xs]
  (if (empty? xs)
    nil
    (f (first xs))
    (Each-helper f (rest xs))))

(fn Each [f xs]
  (Each-helper f xs))

(fn Contains [xs val]
  (if (empty? xs)
    false
    (if (= (first xs) val)
      true
      (Contains (rest xs) val))))
```

- [ ] **步骤 2：验证 .ct 文件可独立执行**

运行：
```bash
python -c "from src.lexer import Lexer; from src.parser import Parser; from src.evaluator import Evaluator; from src.types import CentoList; from src.std.collection import concat_fn; src = open('src/std/collection.ct', encoding='utf-8').read(); ast = Parser(Lexer(src).tokenize()).parse(); e = Evaluator(skip_std=True); e.global_env.define('Concat', concat_fn, exported=True); [e.evaluate(x) for x in ast.expressions]; print(e.global_env.lookup('Map')(lambda x: x+1, CentoList([1.0, 2.0, 3.0])))"
```
预期：输出 `[2.0, 3.0, 4.0]`

- [ ] **步骤 3：Commit**

```bash
git add src/std/collection.ct
git commit -m "feat(bootstrap): 添加 collection.ct 自举实现"
```

---

### 任务 2：修改 evaluator - collection 注册段 + 依赖处理

**文件：**
- 修改：`src/evaluator.py`

- [ ] **步骤 1：定位 collection 注册段**

运行：`grep -n "std/collection" src/evaluator.py`
预期输出：
```
61:            # std/collection
            from src.std.collection import FUNCTIONS as COLLECTION_FUNCTIONS

            for name, fn in COLLECTION_FUNCTIONS.items():
                self.global_env.define(name, fn, exported=True)
```

- [ ] **步骤 2：替换 collection 注册段为 Cento 优先 + Python fallback**

将原段：
```python
            # std/collection
            from src.std.collection import FUNCTIONS as COLLECTION_FUNCTIONS

            for name, fn in COLLECTION_FUNCTIONS.items():
                self.global_env.define(name, fn, exported=True)
```

替换为：
```python
            # std/collection (Cento 优先，Python fallback)
            try:
                collection_exports = self._load_cent_module("collection")
                for name, fn in collection_exports.items():
                    self.global_env.define(name, fn, exported=True)
                from src.std.collection import FUNCTIONS as COLLECTION_FUNCTIONS
                for name, fn in COLLECTION_FUNCTIONS.items():
                    if name not in collection_exports:
                        self.global_env.define(name, fn, exported=True)
            except Exception as e:
                import sys
                print(
                    f"[bootstrap] collection.ct 加载失败，使用 Python fallback: {e}",
                    file=sys.stderr,
                )
                from src.std.collection import FUNCTIONS as COLLECTION_FUNCTIONS
                for name, fn in COLLECTION_FUNCTIONS.items():
                    self.global_env.define(name, fn, exported=True)
```

- [ ] **步骤 3：修改 _load_cent_module 为 collection.ct 注册 Concat 依赖**

定位 `_load_cent_module` 方法中以下代码段：
```python
        # 使用独立 evaluator 避免污染当前 global_env
        # skip_std=True 避免递归加载 std 模块，手动注册 collection 依赖
        sub_evaluator = Evaluator(skip_std=True)
        from src.std.collection import FUNCTIONS as COLLECTION_FUNCTIONS
        for name, fn in COLLECTION_FUNCTIONS.items():
            sub_evaluator.global_env.define(name, fn, exported=True)
        # 记录 .ct 加载前的绑定，后续只收集新增的
        prior_bindings = set(sub_evaluator.global_env.bindings.keys())
```

替换为：
```python
        # 使用独立 evaluator 避免污染当前 global_env
        # skip_std=True 避免递归加载 std 模块，手动注册 collection 依赖
        sub_evaluator = Evaluator(skip_std=True)
        from src.std.collection import FUNCTIONS as COLLECTION_FUNCTIONS
        for name, fn in COLLECTION_FUNCTIONS.items():
            sub_evaluator.global_env.define(name, fn, exported=True)
        # collection.ct 自身依赖 Concat（原生 concat_fn），其余 .ct 不需要额外依赖
        # prior_bindings 用于排除上述注册的依赖，只收集 .ct 新增的导出
        prior_bindings = set(sub_evaluator.global_env.bindings.keys())
```

- [ ] **步骤 4：运行现有 collection 测试验证零回归**

运行：`pytest tests/test_std_collection.py -v`
预期：所有现有测试 PASS

- [ ] **步骤 5：运行全套测试验证零回归**

运行：`pytest`
预期：220 个测试全 PASS

- [ ] **步骤 6：Commit**

```bash
git add src/evaluator.py
git commit -m "feat(bootstrap): evaluator collection 注册段改为 Cento 优先 + Python fallback"
```

---

### 任务 3：新增 bootstrap 测试 - collection 自举验证

**文件：**
- 修改：`tests/test_bootstrap.py`

- [ ] **步骤 1：在 tests/test_bootstrap.py 末尾追加 collection 测试类**

```python


class TestCollectionBootstrap:
    def test_collection_ct_functions_loaded(self):
        """验证 collection.ct 中的函数已注册到 global_env"""
        e = Evaluator()
        # Map 来自 collection.ct
        assert e.global_env.lookup("Map") is not None
        assert list(eval_str("(Map (fn [x] (+ x 1)) [1 2 3])")) == [2.0, 3.0, 4.0]

    def test_mixed_implementation(self):
        """collection 同时有 Cento（Map）和 Python（Concat）函数，验证协同工作"""
        # Map 来自 collection.ct
        assert list(eval_str("(Map (fn [x] (* x 2)) [1 2 3])")) == [2.0, 4.0, 6.0]
        # Concat 来自 collection.py（Python 原生，因可变参数未自举）
        assert list(eval_str("(Concat [1 2] [3 4])")) == [1.0, 2.0, 3.0, 4.0]
        # 组合：Map + Concat
        assert list(eval_str("(Concat (Map (fn [x] (+ x 1)) [1 2]) [10])")) == [2.0, 3.0, 10.0]
```

- [ ] **步骤 2：运行 bootstrap 测试验证通过**

运行：`pytest tests/test_bootstrap.py -v`
预期：8 个测试全 PASS（原 6 + 新增 2）

- [ ] **步骤 3：运行全套测试验证零回归**

运行：`pytest`
预期：222 个测试全 PASS（220 + 2 新增）

- [ ] **步骤 4：Commit**

```bash
git add tests/test_bootstrap.py
git commit -m "test(bootstrap): 添加 collection 自举验证测试"
```

---

### 任务 4：最终验证与推送

- [ ] **步骤 1：运行完整测试套件**

运行：`pytest -v`
预期：222 个测试全 PASS

- [ ] **步骤 2：手动验证自举效果**

运行：
```bash
python -c "from src.evaluator import Evaluator; e = Evaluator(); print('Map:', type(e.global_env.lookup('Map')).__name__); print('Filter:', type(e.global_env.lookup('Filter')).__name__); print('Concat:', type(e.global_env.lookup('Concat')).__name__); print('Keys:', type(e.global_env.lookup('Keys')).__name__)"
```
预期：
- `Map: Fn`（Cento 实现）
- `Filter: Fn`（Cento 实现）
- `Concat: function`（Python 原生 fallback）
- `Keys: function`（Python 原生 fallback）

- [ ] **步骤 3：推送**

```bash
git push
```

---

## 自检结果

**1. 规格覆盖度：**
- collection.ct 5 个函数 → 任务 1 ✓
- evaluator collection 注册段 + 依赖处理 → 任务 2 ✓
- bootstrap 测试 → 任务 3 ✓
- 最终验证 → 任务 4 ✓

**2. 占位符扫描：** 无 TODO/待定，所有代码步骤含完整代码。

**3. 类型一致性：** `_load_cent_module` 中 prior_bindings 变量名与现有实现一致；collection_exports 变量名在任务 2 定义并一致使用；TestCollectionBootstrap 类名与现有 TestBootstrapLoaded/TestMixedImplementation 命名风格一致。
