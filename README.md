# Cento

> A functional language for learning and fun.

Cento 是一门以学习与娱乐为目的的函数式编程语言，采用 S-expression 语法、树遍历解释器实现，去除 OOP/class 系统，强调函数式与数据驱动。语言核心极简，能力通过标准库扩展。

## 特性

- **极简核心**：S-expression 语法、`let` 绑定、`fn` 函数、`if` 条件
- **无面向对象系统**：完全禁止 class、object method、inheritance、this/self 模型
- **函数即一切**：函数是一等公民，支持闭包与高阶函数
- **数据驱动**：核心数据结构只有 number / string / bool / list / map / keyword / nil
- **不可变语义**：所有数据结构操作返回新值，可变性通过 `std/mutable` 作为逃生舱
- **Go 风格模块系统**：基于路径导入，大写开头的绑定自动导出
- **Lisp 风格错误处理**：`error` 信号 + `try` / `catch` / `finally`
- **交互式 REPL**：支持多行输入与括号平衡

## 安装

要求 Python ≥ 3.10。

```bash
# 在项目根目录下安装（可执行命令 cento）
pip install -e .
```

## 快速开始

### 运行脚本

```bash
cento run examples/hello.ct
```

### 启动 REPL

```bash
cento
```

REPL 中输入 `(exit)` 退出。

### Hello World

```lisp
(let [name "World"]
  (println (str "Hello, " name "!")))
```

### Fibonacci

```lisp
(fn fib [n]
  (if (<= n 1)
    n
    (+ (fib (- n 1)) (fib (- n 2)))))

(println (str "fib(10) = " (fib 10)))   ; => fib(10) = 55
```

### 高阶函数

```lisp
(let [nums [1 2 3 4 5]]
  (let [doubled (Map (fn [x] (* x 2)) nums)]
    (println (str "doubled: " doubled)))) ; => doubled: [2 4 6 8 10]
```

## 语法概览

### 字面量

| 类型 | 示例 |
|------|------|
| Number | `42` `3.14` |
| String | `"hello"` |
| Bool | `true` `false` |
| Nil | `nil` |
| Keyword | `:name` `:age` |
| List | `[1 2 3]` |
| Map | `{:name "Cento" :version 1}` |

### 括号语义

- `()` — 函数调用 / 特殊形式
- `[]` — list 字面量 / 绑定参数列表
- `{}` — map 字面量

### 注释

`;` 单行注释。

### 特殊形式

```lisp
; let 绑定
(let [x 10 y 20]
  (+ x y))

; fn 函数（可命名以支持自递归）
(fn add [a b] (+ a b))
(fn factorial [n]
  (if (<= n 1) 1 (* n (factorial (- n 1)))))

; if 条件
(if (> x 0) "positive" "non-positive")

; import 模块
(import "std/collection")
(import "std/io" [Read-line Read-file])
(import "mylib/math" [Add :as plus])

; try / catch / finally
(try
  (some-risky-call)
  (catch [msg] (println "Error:" msg))
  (finally (println "done")))
```

## 标准库

标准库以 Python 原生实现，自动注册到全局环境，可直接调用（无需 import）。

### 核心内置

**算术：** `+` `-` `*` `/` `mod` `abs` `max` `min`
**比较：** `=` `!=` `>` `<` `>=` `<=`
**逻辑：** `and` `or` `not`
**类型：** `type` `number?` `string?` `bool?` `list?` `map?` `fn?` `nil?` `keyword?`
**通用：** `print` `println` `str` `count` `empty?` `first` `rest` `get` `eq?` `error`

### std/collection

`Map` `Filter` `Reduce` `Each` `Concat` `Contains` `Assoc` `Dissoc` `Keys` `Values` `Merge`

```lisp
(Map (fn [x] (* x 2)) [1 2 3])       ; => [2 4 6]
(Filter (fn [x] (> x 2)) [1 2 3 4])  ; => [3 4]
(Reduce + 0 [1 2 3])                  ; => 6
(Assoc {:a 1} :b 2)                   ; => {:a 1 :b 2}
(Keys {:a 1 :b 2})                    ; => [:a :b]
```

### std/string

`Split` `Join` `Trim` `Upper` `Lower` `Replace` `Has-prefix` `Has-suffix`

```lisp
(Split "a,b,c" ",")      ; => ["a" "b" "c"]
(Join ["a" "b"] "-")     ; => "a-b"
(Upper "hello")          ; => "HELLO"
```

### std/io

`Read-line` `Read-file` `Write-file`

```lisp
(Write-file "out.txt" "hello")
(Read-file "out.txt")    ; => "hello"
```

### std/fs

`Exists?` `Is-dir?` `List-dir` `Mkdir` `Rmdir`

```lisp
(Exists? "out.txt")      ; => true
(List-dir ".")           ; => ["out.txt" ...]
```

### std/mutable

`Ref` `Ref-get` `Ref-set!` `Array` `Array-get` `Array-set!` `Mutable-map` `Mutable-map-get` `Mutable-map-set!`

```lisp
(let [r (Ref 0)]
  (Ref-set! r 42)
  (Ref-get r))           ; => 42

(let [m (Mutable-map)]
  (Mutable-map-set! m :name "Cento")
  (Mutable-map-get m :name)) ; => "Cento"
```

## 模块系统

模块系统采用 Go 风格，基于文件系统路径解析：

- 以 `std/` 开头 → 从标准库目录查找
- 其他 → 从当前文件所在目录查找
- 模块只加载一次（缓存）

### 导出规则

- 以大写字母开头的 `fn` 和 `let` 绑定自动导出
- 小写开头的绑定仅在模块内部可见

```lisp
; mylib/math.ct

; 导出（大写开头）
(fn Add [a b] (+ a b))
(let Pi 3.14159)

; 内部（小写开头，不导出）
(fn helper [x] (* x x))
```

使用：

```lisp
(import "mylib/math" [Add Pi])
(Add 1 2)   ; => 3
Pi          ; => 3.14159
```

## 项目结构

```
cento/
├── src/
│   ├── __main__.py        # CLI 入口（cento run / REPL）
│   ├── lexer.py           # 词法分析器
│   ├── parser.py          # 语法分析器
│   ├── ast_nodes.py       # AST 节点定义
│   ├── evaluator.py       # 树遍历求值器
│   ├── environment.py     # 词法环境
│   ├── types.py           # 内置类型（Keyword/Fn/CentoList/CentoMap/Ref...）
│   ├── errors.py          # 错误类型
│   ├── modules.py         # 模块加载器
│   ├── repl.py            # 交互式 REPL
│   └── std/               # 标准库（Python 原生实现）
│       ├── collection.py
│       ├── string.py
│       ├── io.py
│       ├── fs.py
│       └── mutable.py
├── tests/                 # 单元测试与集成测试
├── examples/              # 示例脚本
├── docs/                  # 设计文档
└── pyproject.toml
```

## 测试

```bash
pytest
```

测试覆盖 lexer、parser、evaluator、environment、modules、types、std 与集成场景。

## 设计文档

详细语言设计规格见 [docs/superpowers/specs/2026-06-15-lume-language-design.md](docs/superpowers/specs/2026-06-15-lume-language-design.md)。

## 许可

本项目用于个人学习与娱乐。
