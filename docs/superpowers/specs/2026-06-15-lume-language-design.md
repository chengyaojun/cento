# Lume 语言设计规格

> 一个用于个人学习与娱乐的函数式语言，去除 OOP/class 系统，依赖标准库扩展能力，强调函数式与数据驱动。

## 核心设计原则

1. **极简核心** — 语言核心只包含 S-expression 语法、函数调用、let 绑定、fn 函数、if 条件
2. **无面向对象系统** — 完全禁止 class、object method、inheritance、this/self 模型
3. **函数即一切** — 函数是一等公民，所有行为通过函数调用实现
4. **数据驱动** — 只有三种核心数据结构：number/string/bool、list `[]`、map `{}`
5. **标准库驱动能力** — 语言能力不靠语法扩展，而靠 stdlib

## 实现决策

- **实现语言**：Python
- **执行模型**：树遍历解释器
- **模块系统**：Go 风格（基于路径的导入、命名规则导出）
- **不可变性**：Haskell 风格纯不可变，stdlib 提供可变引用作为逃生舱
- **错误处理**：Lisp 风格（error 信号 + try/catch/finally）
- **交互模式**：支持 REPL

---

## 1. 词法与语法

### Token 类型

| 类型 | 示例 |
|------|------|
| LPAREN / RPAREN | `(` `)` |
| LBRACKET / RBRACKET | `[` `]` |
| LBRACE / RBRACE | `{` `}` |
| NUMBER | `42` `3.14` |
| STRING | `"hello"` |
| BOOL | `true` `false` |
| SYMBOL | `foo` `+` `print` `my-fn` |
| KEYWORD | `:name` `:age` |

### 语法规则

```
program      = expr*
expr         = atom | list | map | call | let | fn | if
atom         = NUMBER | STRING | BOOL | SYMBOL | KEYWORD
list         = "[" expr* "]"
map          = "{" (KEYWORD expr)* "}"
call         = "(" expr expr* ")"
let          = "(" "let" "[" (SYMBOL expr)* "]" expr+ ")"
fn           = "(" "fn" SYMBOL? "[" SYMBOL* "]" expr+ ")"
if           = "(" "if" expr expr expr? ")"
```

### 括号语义

- `()` — 函数调用
- `[]` — list 字面量
- `{}` — map 字面量

### 注释

`;` 单行注释

### 符号

允许 `+` `-` `*` `/` `>` `<` `=` `>=` `<=` 等操作符符号

### 示例

```lisp
; 绑定
(let [x 10 y 20]
  (+ x y))

; 函数定义
(fn add [a b]
  (+ a b))

; 条件
(if (> x 0)
  (print "positive")
  (print "non-positive"))

; list 字面量
[1 2 3 4 5]

; map 字面量
{:name "Lume" :version 1 :stable true}
```

---

## 2. 求值与类型系统

### 核心数据类型

| 类型 | 字面量 | 内部表示 |
|------|--------|----------|
| Number | `42` `3.14` | Python `float`（统一浮点） |
| String | `"hello"` | Python `str` |
| Bool | `true` `false` | Python `bool` |
| List | `[1 2 3]` | Python `list`（Lume 层面不可变） |
| Map | `{:a 1}` | Python `dict`（Lume 层面不可变） |
| Keyword | `:name` | `Keyword("name")` 对象 |
| Symbol | `foo` | `Symbol("foo")` 对象 |
| Fn | `(fn ...)` | `Fn` 对象（闭包） |
| Nil | `nil` | 空值 |

### 求值规则

```
eval(Number)    → Number
eval(String)    → String
eval(Bool)      → Bool
eval(Nil)       → Nil
eval(Keyword)   → Keyword
eval(List)      → List（逐元素求值）
eval(Map)       → Map（逐值求值）
eval(Symbol)    → 从环境中查找绑定
eval(Call)      → 求值操作符，应用到求值后的参数
eval(Let)       → 在扩展环境中求值 body
eval(Fn)        → 创建闭包（捕获当前环境）
eval(If)        → 求值条件，分支求值
```

### 不可变语义

- 一切绑定不可变，没有 `mut`，没有 `set!`
- 所有数据结构操作返回新值，不修改原值
- "修改"通过创建新值实现：

```lisp
; list "修改"
(let [xs [1 2 3]]
  (let [ys (list-push xs 4)]    ; ys = [1 2 3 4]，xs 不变
    (count xs)))                  ; => 3

; map "修改"
(let [m {:name "Lume" :version 1}]
  (let [m2 (map-assoc m :version 2)]  ; m2 = {:name "Lume" :version 2}
    (get m :version)))                   ; => 1，m 不变
```

- 需要累加/状态变化时，用递归代替循环：

```lisp
(fn sum [xs]
  (if (empty? xs)
    0
    (+ (first xs) (sum (rest xs)))))
```

- 尾调用优化（TCO）保证递归不爆栈：

```lisp
(fn loop-sum [xs acc]
  (if (empty? xs)
    acc
    (loop-sum (rest xs) (+ acc (first xs)))))

(loop-sum [1 2 3] 0)  ; => 6
```

- 可变性通过 stdlib 提供（见第 5 节）

### 闭包

```lisp
(let [make-adder
      (fn [x]
        (fn [y] (+ x y)))]
  (let [add5 (make-adder 5)]
    (add5 3)))  ; => 8
```

函数捕获定义时的环境，形成闭包。

### 递归

命名 `fn` 的名称在自身作用域内可见，支持自递归：

```lisp
(fn factorial [n]
  (if (<= n 1)
    1
    (* n (factorial (- n 1)))))
```

---

## 3. 模块系统（Go 风格）

### 导入语法

```lisp
(import "std/collection")
(import "std/io" [print read-line])
(import "mylib/math" [add :as plus])
```

- `import` 是特殊形式，不是函数
- 第一个参数是模块路径（字符串），基于文件系统解析
- 可选第二个参数指定导入的符号列表
- `:as` 支持别名

### 模块文件结构

```
project/
├── main.lm              ; 入口文件
├── mylib/
│   ├── math.lm          ; 模块 mylib/math
│   └── utils.lm         ; 模块 mylib/utils
└── std/                 ; 标准库
    ├── collection.lm
    ├── io.lm
    ├── string.lm
    └── fs.lm
```

### 导出规则

- 以大写字母开头的 `fn` 和 `let` 绑定自动导出
- 小写开头的绑定仅在模块内部可见

```lisp
; std/math.lm

; 导出（大写开头）
(fn Add [a b] (+ a b))
(let Pi 3.14159)

; 内部（小写开头，不导出）
(fn helper [x] (* x x))
```

使用时：

```lisp
(import "std/math" [Add Pi])

(Add 1 2)    ; => 3
Pi            ; => 3.14159
; (helper 5) ; 错误：helper 未导出
```

### 模块解析规则

1. 以 `std/` 开头 → 从标准库目录查找
2. 以 `./` 或 `../` 开头 → 相对于当前文件查找
3. 其他 → 从项目根目录查找
4. 模块只加载一次（缓存），避免重复求值

### 模块初始化

模块顶层表达式按导入顺序执行，每个模块只初始化一次。

---

## 4. 错误处理（Lisp 风格）

### 错误信号

```lisp
(error "division by zero")
(error "invalid argument" {:value x :expected "positive number"})
```

### try/catch/finally

```lisp
(try
  expr                    ; 尝试执行的表达式
  (catch [msg] expr)      ; 捕获错误，msg 为错误信息
  (finally expr))         ; 无论是否出错都执行（可选）
```

示例：

```lisp
(fn safe-divide [a b]
  (if (= b 0)
    (error "division by zero")
    (/ a b)))

(let [result
      (try
        (safe-divide 10 0)
        (catch [msg]
          (print "Error:" msg)
          nil))]
  result)  ; => nil，打印 "Error: division by zero"
```

### 结构化错误

错误值可以是字符串或 map：

```lisp
; 简单错误
(error "file not found")

; 结构化错误
(error {:type :io-error
        :message "file not found"
        :path "/tmp/data.lm"})

; catch 中检查类型
(try
  (read-file path)
  (catch [err]
    (if (= (get err :type) :io-error)
      (print "IO failed:" (get err :message))
      (error err))))  ; 重新抛出未知错误
```

### 设计要点

- `error` 是 stdlib 函数，不是语言关键字
- `try`/`catch`/`finally` 是语言特殊形式
- 错误值可以是任意类型（字符串或 map）
- 没有 Java 风格的异常层级
- `catch` 中可以用 `error` 重新抛出

---

## 5. 标准库

### 模块划分

| 模块 | 路径 | 职责 |
|------|------|------|
| 核心 | `std/core` | 自动导入，基础操作符和类型函数 |
| 集合 | `std/collection` | list/map 操作 |
| 字符串 | `std/string` | 字符串处理 |
| I/O | `std/io` | 输入输出 |
| 文件系统 | `std/fs` | 文件读写、路径操作 |
| 可变类型 | `std/mutable` | ref/array/mutable-map |

### std/core（自动导入）

**算术：** `+` `-` `*` `/` `mod` `abs` `max` `min`

**比较：** `=` `!=` `>` `<` `>=` `<=`

**逻辑：** `and` `or` `not`

**类型：** `type` `number?` `string?` `bool?` `list?` `map?` `fn?` `nil?` `keyword?`

**通用：** `print` `println` `str` `count` `empty?` `first` `rest` `get` `eq?`

```lisp
(type 42)          ; => "number"
(type "hello")     ; => "string"
(type [1 2])       ; => "list"
(str "a" "b" "c")  ; => "abc"
(count [1 2 3])    ; => 3
(first [1 2 3])    ; => 1
(rest [1 2 3])     ; => [2 3]
(get {:a 1} :a)    ; => 1
```

### std/collection

```lisp
(import "std/collection" [Map Filter Reduce Each Concat Contains])

(Map (fn [x] (* x 2)) [1 2 3])         ; => [2 4 6]
(Filter (fn [x] (> x 2)) [1 2 3 4])    ; => [3 4]
(Reduce + 0 [1 2 3])                    ; => 6
(Each println [1 2 3])                  ; 打印每个元素
(Concat [1 2] [3 4])                    ; => [1 2 3 4]
(Contains [1 2 3] 2)                    ; => true

; map 操作
(Assoc {:a 1} :b 2)                     ; => {:a 1 :b 2}
(Dissoc {:a 1 :b 2} :a)                ; => {:b 2}
(Keys {:a 1 :b 2})                      ; => [:a :b]
(Values {:a 1 :b 2})                    ; => [1 2]
(Merge {:a 1} {:b 2})                   ; => {:a 1 :b 2}
```

### std/string

```lisp
(import "std/string" [Split Join Trim Upper Lower Replace Has-prefix Has-suffix])

(Split "a,b,c" ",")              ; => ["a" "b" "c"]
(Join ["a" "b" "c"] ",")         ; => "a,b,c"
(Trim "  hello  ")               ; => "hello"
(Upper "hello")                  ; => "HELLO"
(Lower "HELLO")                  ; => "hello"
(Replace "hello" "l" "r")        ; => "herro"
(Has-prefix "hello" "he")        ; => true
(Has-suffix "hello" "lo")        ; => true
```

### std/io

```lisp
(import "std/io" [Read-line Read-file Write-file])

(Read-line)                       ; 从 stdin 读取一行
(Read-file "data.txt")            ; 读取文件内容为字符串
(Write-file "out.txt" "content")  ; 写入文件
```

### std/fs

```lisp
(import "std/fs" [Exists? Is-dir? List-dir Mkdir Rmdir])

(Exists? "data.txt")     ; => true
(Is-dir? "src")          ; => true
(List-dir ".")           ; => ["main.lm" "mylib"]
(Mkdir "output")         ; 创建目录
(Rmdir "output")         ; 删除目录
```

### std/mutable

```lisp
(import "std/mutable" [Ref Ref-get Ref-set! Array Array-get Array-set! Mutable-map Mutable-map-get Mutable-map-set!])

; Ref
(let [r (Ref 0)]
  (Ref-set! r 42)
  (Ref-get r))                    ; => 42

; Array
(let [arr (Array 3)]
  (Array-set! arr 0 10)
  (Array-get arr 0))              ; => 10

; MutableMap
(let [m (Mutable-map)]
  (Mutable-map-set! m :name "Lume")
  (Mutable-map-get m :name))      ; => "Lume"
```

---

## 6. 解释器架构

### 整体流程

```
源代码 (.lm)
    │
    ▼
┌─────────┐
│  Lexer  │  字符流 → Token 流
└────┬────┘
     │
     ▼
┌──────────┐
│  Parser  │  Token 流 → AST
└────┬─────┘
     │
     ▼
┌───────────┐
│ Evaluator │  AST → 值（树遍历求值）
└───────────┘
```

### 项目结构

```
lume/
├── __init__.py
├── __main__.py          ; CLI 入口 (python -m lume)
├── lexer.py             ; 词法分析
├── parser.py            ; 语法分析 → AST
├── ast_nodes.py         ; AST 节点定义
├── evaluator.py         ; 求值器
├── environment.py       ; 环境/作用域
├── modules.py           ; 模块加载与缓存
├── types.py             ; Lume 值类型 (Keyword, Symbol, Fn, Ref 等)
├── errors.py            ; 错误类型定义
├── repl.py              ; REPL 实现
└── std/                 ; 标准库 (Lume 源码)
    ├── core.lm
    ├── collection.lm
    ├── string.lm
    ├── io.lm
    ├── fs.lm
    └── mutable.lm
```

### 核心类设计

**Environment（环境）：**
- 链式作用域：每个环境持有 `parent` 引用
- `let` 创建子环境
- `fn` 捕获定义时的环境（闭包）

**Evaluator（求值器）：**
- `eval(node, env)` 分发到各节点类型的求值方法
- 内置操作符（`+` `-` `*` 等）注册在全局环境中
- `try/catch` 通过 Python 异常机制实现

**Modules（模块系统）：**
- 维护模块缓存 `dict[path, module_env]`
- 解析路径 → 读取文件 → 词法分析 → 语法分析 → 求值 → 返回导出符号
- 只加载一次，后续 import 直接返回缓存

### CLI 用法

```bash
python -m lume              ; 启动 REPL
python -m lume run main.lm  ; 执行文件
python -m lume run main.lm arg1 arg2  ; 带参数执行
```

### TCO 实现

求值器检测尾位置的递归调用，用循环替代递归栈。对 `if` 的尾位置分支和 `let` 的尾位置 body 进行尾调用优化。
