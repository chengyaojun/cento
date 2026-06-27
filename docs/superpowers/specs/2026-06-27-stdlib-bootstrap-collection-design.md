# 标准库自举扩展 - collection 模块设计规格

> 用 Cento 语言实现 collection 模块中的 5 个列表操作函数，延续标准库自举工作。

## 背景与目标

### 当前状态
- 已完成 util.ct（9 函数）和 seq.ct（8 函数）的自举，建立 Cento 优先 + Python fallback 加载机制
- `_load_cent_module` 加载机制已验证可行，支持子 evaluator + collection 依赖注入
- collection 模块当前 11 个函数全部用 Python 实现

### 目标
1. 用 Cento 语言重新实现 collection 模块中 5 个列表操作函数
2. 复用现有 `_load_cent_module` 加载机制，无新增基础设施
3. 零回归：现有 220 个测试全绿
4. 验证高阶函数（Map/Filter/Reduce）的自举能力

### 非目标
- 不自举 Concat/Merge（可变参数）
- 不自举 Assoc/Dissoc/Keys/Values（map 字面量键必须为关键字字面量，无法动态构建）
- 不扩展 first/rest 支持 CentoMap（收益不足，保持内置函数简洁）
- 不扩展 map 字面量语法（范围过大，违反 YAGNI）

## 架构与加载流程

### 文件布局
```
src/std/
  collection.py  # 保留为 Python fallback（6 个函数：Concat/Merge/Assoc/Dissoc/Keys/Values）
  collection.ct  # 新增 Cento 实现（5 个函数：Map/Filter/Reduce/Each/Contains）
```

### 加载流程
复用 util/seq 已建立的机制：
1. evaluator 的 collection 注册段调用 `_load_cent_module("collection")`
2. 成功 → Cento 实现注册到 global_env
3. Python fallback 补齐未自举的 6 个函数
4. 失败 → 全部用 Python fallback

### collection.ct 依赖
- 内置：`first`/`rest`/`empty?`/`nil`
- collection 原生函数：`Concat`（用于构造列表，Python 版 concat_fn 接收可变参数）

**关键点**：collection.ct 自身依赖 collection.py 的 Concat，因此 `_load_cent_module` 加载 collection.ct 时，子 evaluator 需注册 collection.py 的 Concat 作为依赖。

## 函数清单与实现策略

### 可自举函数（5 个）

| 函数 | Cento 实现 |
|------|-----------|
| `Map` | `(fn Map [f xs] (if (empty? xs) [] (Concat [(f (first xs))] (Map f (rest xs)))))` |
| `Filter` | `(fn Filter [pred xs] (if (empty? xs) [] (if (pred (first xs)) (Concat [(first xs)] (Filter pred (rest xs))) (Filter pred (rest xs)))))` |
| `Reduce` | `(fn Reduce [f init xs] (if (empty? xs) init (Reduce f (f init (first xs)) (rest xs))))` |
| `Each` | `(fn Each-helper [f xs] (if (empty? xs) nil (f (first xs)) (Each-helper f (rest xs))))` — 函数体多表达式顺序执行 |
| `Contains` | `(fn Contains [xs val] (if (empty? xs) false (if (= (first xs) val) true (Contains (rest xs) val))))` |

**说明**：
- `Each` 需返回 nil，Cento 支持 `nil` 字面量
- `Each` 利用函数体多表达式顺序执行（FnExpr.body 是 list，按顺序 eval，返回最后一个）
- 所有递归依赖 TCO 支持（已验证）

### 保留原生（6 个）
- `Concat` - 可变参数 `*lists`
- `Merge` - 可变参数 `*maps`
- `Assoc` - 需动态构建 map（map 字面量键必须为关键字字面量）
- `Dissoc` - 同上
- `Keys` - 需 first/rest 支持 CentoMap（当前仅支持 CentoList）
- `Values` - 同上

## 测试策略

### 复用现有测试
- `tests/test_std_collection.py` - 验证 collection 自举后行为不变
- 现有测试无需修改，自动验证 Cento 实现的正确性

### 新增 bootstrap 测试
在 `tests/test_bootstrap.py` 添加 `TestCollectionBootstrap` 类：
- `test_collection_ct_functions_loaded` - 验证 Map/Filter/Reduce/Each/Contains 已注册
- `test_mixed_implementation` - collection 同时有 Cento（Map）和原生（Concat）函数协同工作

### 验证检查点
1. 修改 evaluator 后，现有 220 个测试全绿（零回归）
2. 新增 bootstrap 测试全绿
3. 手动验证：`type(Map)` 应为 `Fn`（Cento 实现），`type(Concat)` 应为 `function`（Python fallback）

## 实现顺序

1. 创建 `src/std/collection.ct` - 5 个函数
2. 修改 `src/evaluator.py` - collection 注册段改为 Cento 优先 + Python fallback，并在 `_load_cent_module` 中为 collection.ct 注册 Concat 依赖
3. 更新 `tests/test_bootstrap.py` - 添加 collection 相关测试
4. 运行全套测试验证
5. 推送

## 边界情况

- **Each 返回值**：Cento 实现返回 nil（与 Python 版 `return None` 一致）
- **空列表**：Map/Filter/Reduce/Each/Contains 对空列表的处理与 Python 版一致
- **类型一致性**：Cento 实现返回 CentoList（通过 Concat 构造）
- **TCO 深度**：Reduce/Filter 等递归依赖 TCO，已验证支持
