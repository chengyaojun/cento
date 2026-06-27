# 标准库自举设计规格

> 用 Cento 语言自身实现部分标准库函数，验证自举机制可行，建立 Cento 优先 + Python fallback 的加载策略。

## 背景与目标

### 当前状态
- Cento 标准库全部用 Python 实现，分布在 8 个模块（math/string/collection/seq/util/io/fs/mutable）
- `ModuleLoader` 已支持加载 `.ct` 源文件（`std/xxx` → `src/std/xxx.ct`），大写开头自动导出
- Cento 语言能力充分：支持 `let`/`fn`/`if`/递归/TCO/闭包/高阶函数

### 目标
1. 用 Cento 语言重新实现 util 和 seq 模块中的纯逻辑函数
2. 建立 Cento 优先 + Python fallback 的加载机制
3. 零回归：现有 214 个测试全绿
4. 验证自举机制可行，为后续扩展到其他模块奠定基础

### 非目标
- 不自举 math（依赖 Python `math` 模块的底层 C 实现）
- 不自举 io/fs（依赖 Python 文件系统 API）
- 不自举 string 的底层操作（依赖 Python 字符串方法）
- 不重写排序算法（Sort 系列保留原生 Timsort）

## 架构与加载流程

### 文件布局
```
src/std/
  util.py        # 保留为 Python fallback（4 个函数：Comp/Apply/Const/Parse-number）
  util.ct        # 新增 Cento 实现（9 个函数）
  seq.py         # 保留为 Python fallback（4 个函数：Sort/Sort-desc/Sort-by/Sort-by-desc）
  seq.ct         # 新增 Cento 实现（9 个函数）
```

### 加载流程
```
_register_builtins 中 util/seq 注册段：
  1. 调用 _load_cent_module("util")
  2. _load_cent_module:
     a. 查找 src/std/util.ct 是否存在
     b. 存在 → Lexer + Parser + Evaluator 执行，收集大写开头的绑定
     c. 返回 {name: callable} 字典
     d. 不存在或执行失败 → 抛异常
  3. 成功 → 用 Cento 实现注册到 global_env
  4. 失败 → fallback: import src.std.util, 使用 FUNCTIONS 字典
  5. 补齐：Cento 实现中缺失的函数用 Python 补齐
     （例如 util.ct 无 Comp，则从 util.py 取 Comp 注册）
```

### 错误处理
- .ct 文件语法错误 → 捕获异常，打印 stderr 警告，fallback 到 Python
- .ct 文件中函数名缺失 → Python 补齐
- 不阻断解释器启动（保证始终可用）

## 函数清单与实现策略

### util.ct（9 个函数自举）

| 函数 | Cento 实现 |
|------|-----------|
| `Identity` | `(fn Identity [x] x)` |
| `Inc` | `(fn Inc [x] (+ x 1))` |
| `Dec` | `(fn Dec [x] (- x 1))` |
| `Even?` | `(fn Even? [x] (= (mod x 2) 0))` |
| `Odd?` | `(fn Odd? [x] (!= (mod x 2) 0))` |
| `Zero?` | `(fn Zero? [x] (= x 0))` |
| `Pos?` | `(fn Pos? [x] (> x 0))` |
| `Neg?` | `(fn Neg? [x] (< x 0))` |
| `Complement` | `(fn Complement [f] (fn [x] (not (f x))))` |

**保留原生（4 个）**：
- `Comp` - 需可变参数支持
- `Apply` - 需 spread 支持
- `Const` - 需可变参数支持
- `Parse-number` - 依赖 Python `float()`

### seq.ct（9 个函数自举）

| 函数 | Cento 实现策略 |
|------|---------------|
| `Take` | 递归取前 n 个 |
| `Drop` | 递归跳过前 n 个 |
| `Nth` | 递归到第 n 个，越界抛 error |
| `Last` | 递归到末尾 |
| `Range` | 递归生成序列（支持 start/end/step） |
| `Distinct` | 递归 + Contains 去重 |
| `Flatten` | 递归展平，用 `list?` 谓词判断嵌套 |
| `Zip` | 递归配对 |
| `Reverse` | 递归反转 |

**保留原生（4 个）**：
- `Sort` - 依赖 Python Timsort
- `Sort-desc` - 依赖 Python Timsort
- `Sort-by` - 依赖 Python Timsort + key 函数
- `Sort-by-desc` - 依赖 Python Timsort + key 函数

## 测试策略

### 复用现有测试
- `tests/test_std_util.py`（27 个测试）- 验证 util 自举后行为不变
- `tests/test_std_seq.py`（31 个测试）- 验证 seq 自举后行为不变
- 现有测试无需修改，自动验证 Cento 实现的正确性

### 新增 bootstrap 专项测试
`tests/test_bootstrap.py`：
- `test_util_ct_loaded` - 验证 util.ct 成功加载，Inc 等函数来自 Cento
- `test_seq_ct_loaded` - 验证 seq.ct 成功加载，Take 等函数来自 Cento
- `test_fallback_on_error` - 构造 .ct 语法错误场景，验证 fallback 到 Python
- `test_mixed_implementation` - util 模块同时有 Cento（Inc）和原生（Comp）函数，验证协同工作

### 验证检查点
1. 修改 evaluator 后，现有 214 个测试全绿（零回归）
2. 新增 bootstrap 测试全绿
3. 手动验证：`(type Inc)` 或类似方式确认函数来自 Cento 实现

## 实现顺序

1. 创建 `src/std/util.ct` - 9 个函数
2. 创建 `src/std/seq.ct` - 9 个函数
3. 修改 `src/evaluator.py` - 新增 `_load_cent_module` + 修改 util/seq 注册段
4. 新增 `tests/test_bootstrap.py`
5. 运行全套测试验证

## 边界情况

- **递归深度**：`Take`/`Drop`/`Range` 等递归实现依赖 TCO，已验证 Cento 支持
- **类型一致性**：Cento 实现返回 `float`（与 Python 版一致）
- **空列表处理**：`Last []` 和 `Nth [] 0` 应抛 error，与 Python 版一致
- **混合实现**：util 模块同时存在 Cento（Inc）和 Python（Comp）函数，需确保两者都能在 global_env 中正确注册
