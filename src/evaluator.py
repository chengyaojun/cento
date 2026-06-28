from src.ast_nodes import *
from src.environment import Environment
from src.errors import CentoError
from src.types import CentoList, CentoMap, Fn, Keyword, Symbol


class Evaluator:
    def __init__(self, skip_std=False):
        self.global_env = Environment()
        self.module_loader = None
        self._register_builtins(skip_std=skip_std)

    def _register_builtins(self, skip_std=False):
        # Arithmetic
        self.global_env.define("+", lambda *args: sum(args))
        self.global_env.define("-", lambda a, b=None: -a if b is None else a - b)
        self.global_env.define("*", lambda *args: _product(args))
        self.global_env.define("/", lambda a, b: a / b)
        self.global_env.define("mod", lambda a, b: a % b)
        self.global_env.define("abs", lambda x: abs(x))
        self.global_env.define("max", lambda a, b: max(a, b))
        self.global_env.define("min", lambda a, b: min(a, b))
        # Comparison
        self.global_env.define("=", lambda a, b: a == b)
        self.global_env.define("!=", lambda a, b: a != b)
        self.global_env.define(">", lambda a, b: a > b)
        self.global_env.define("<", lambda a, b: a < b)
        self.global_env.define(">=", lambda a, b: a >= b)
        self.global_env.define("<=", lambda a, b: a <= b)
        # Logic
        self.global_env.define("and", lambda a, b: a and b)
        self.global_env.define("or", lambda a, b: a or b)
        self.global_env.define("not", lambda a: not a)
        # Type
        self.global_env.define("type", _cento_type)
        self.global_env.define("number?", lambda x: isinstance(x, (int, float)))
        self.global_env.define("string?", lambda x: isinstance(x, str))
        self.global_env.define("bool?", lambda x: isinstance(x, bool))
        self.global_env.define("list?", lambda x: isinstance(x, CentoList))
        self.global_env.define("map?", lambda x: isinstance(x, CentoMap))
        self.global_env.define("fn?", lambda x: isinstance(x, Fn) or callable(x))
        self.global_env.define("nil?", lambda x: x is None)
        self.global_env.define("keyword?", lambda x: isinstance(x, Keyword))
        # General
        self.global_env.define("print", lambda *args: _print_fn(*args))
        self.global_env.define("println", lambda *args: _println_fn(*args))
        self.global_env.define("str", _str_fn)
        self.global_env.define("count", _count_fn)
        self.global_env.define("empty?", _empty_fn)
        self.global_env.define("first", _first_fn)
        self.global_env.define("rest", _rest_fn)
        self.global_env.define("get", _get_fn)
        self.global_env.define("eq?", lambda a, b: a == b)
        # Apply (dynamic arity call)
        self.global_env.define("apply", lambda fn, args: self._apply(fn, list(args)))
        self.global_env.define("Apply", lambda fn, args: self._apply(fn, list(args)))
        # Error
        self.global_env.define("error", _error_fn)
        # String 原语（与 from-code 对称，供 string.ct 依赖）
        self.global_env.define("from-code", lambda n: chr(int(n)))
        self.global_env.define("to-code", lambda ch: float(ord(ch[0])))
        self.global_env.define("char-at", lambda s, i: s[int(i)])

        def _substring(s, start, end=None):
            return s[int(start) :] if end is None else s[int(start) : int(end)]

        self.global_env.define("substring", _substring)
        self.global_env.define("digit?", lambda ch: len(ch) == 1 and ch in "0123456789")
        self.global_env.define(
            "alpha?", lambda ch: len(ch) == 1 and ch.isalpha() and ch.isascii()
        )
        self.global_env.define(
            "space?", lambda ch: len(ch) == 1 and ch.isspace() and ch.isascii()
        )

        def _parse_number(s):
            try:
                return float(s)
            except (ValueError, TypeError):
                raise CentoError(f"Cannot parse number: {s}")

        self.global_env.define("parse-number", _parse_number)
        self.global_env.define("Parse-number", _parse_number)
        if not skip_std:
            # std/mutable（宿主：需可变数据结构类型）
            from src.types import CentoArray, MutableMap, Ref

            self.global_env.define("Ref", lambda v: Ref(v), exported=True)
            self.global_env.define("Ref-get", lambda r: r.value, exported=True)

            def _ref_set(r, value):
                r.value = value
                return value

            self.global_env.define("Ref-set!", _ref_set, exported=True)
            self.global_env.define(
                "Array", lambda size: CentoArray(int(size)), exported=True
            )
            self.global_env.define(
                "Array-get", lambda arr, i: arr.data[int(i)], exported=True
            )

            def _array_set(arr, i, value):
                arr.data[int(i)] = value
                return value

            self.global_env.define("Array-set!", _array_set, exported=True)
            self.global_env.define("Mutable-map", lambda: MutableMap(), exported=True)
            self.global_env.define(
                "Mutable-map-get", lambda m, k: m.data.get(k), exported=True
            )

            def _mutable_map_set(m, k, value):
                m.data[k] = value
                return value

            self.global_env.define("Mutable-map-set!", _mutable_map_set, exported=True)

            # std/collection 宿主函数（无法自举：需 CentoMap 构造）
            def _concat(*lists):
                result = []
                for lst in lists:
                    result.extend(lst)
                return CentoList(result)

            self.global_env.define("Concat", _concat)

            def _assoc(m, key, val):
                new_m = CentoMap(dict(m))
                new_m[key] = val
                return new_m

            self.global_env.define("Assoc", _assoc)

            def _dissoc(m, key):
                new_m = CentoMap(dict(m))
                new_m.pop(key, None)
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
            # std/string（Cento 自举，原语已注册）
            string_exports = self._load_cent_module("string")
            for name, fn in string_exports.items():
                self.global_env.define(name, fn, exported=True)
            # std/io（宿主：需 OS I/O）
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

            self.global_env.define("Read-line", _read_line, exported=True)
            self.global_env.define("Read-file", _read_file, exported=True)
            self.global_env.define("Write-file", _write_file, exported=True)
            # std/fs（宿主：需 OS 调用）
            import os as _os

            def _list_dir(p):
                return CentoList(_os.listdir(p))

            def _mkdir(p):
                _os.makedirs(p, exist_ok=True)
                return None

            def _rmdir(p):
                import shutil as _shutil

                if _os.path.isdir(p):
                    _shutil.rmtree(p)
                else:
                    _os.remove(p)
                return None

            self.global_env.define(
                "Exists?", lambda p: _os.path.exists(p), exported=True
            )
            self.global_env.define(
                "Is-dir?", lambda p: _os.path.isdir(p), exported=True
            )
            self.global_env.define("List-dir", _list_dir, exported=True)
            self.global_env.define("Mkdir", _mkdir, exported=True)
            self.global_env.define("Rmdir", _rmdir, exported=True)
            # std/math（宿主：需 Python math 库）
            import math as _math

            self.global_env.define("Sin", lambda x: _math.sin(x), exported=True)
            self.global_env.define("Cos", lambda x: _math.cos(x), exported=True)
            self.global_env.define("Tan", lambda x: _math.tan(x), exported=True)
            self.global_env.define("Asin", lambda x: _math.asin(x), exported=True)
            self.global_env.define("Acos", lambda x: _math.acos(x), exported=True)
            self.global_env.define("Atan", lambda x: _math.atan(x), exported=True)
            self.global_env.define("Exp", lambda x: _math.exp(x), exported=True)
            self.global_env.define("Log", lambda x: _math.log(x), exported=True)
            self.global_env.define("Log10", lambda x: _math.log10(x), exported=True)
            self.global_env.define("Sqrt", lambda x: _math.sqrt(x), exported=True)
            self.global_env.define(
                "Pow", lambda base, exp: _math.pow(base, exp), exported=True
            )
            self.global_env.define(
                "Floor", lambda x: float(_math.floor(x)), exported=True
            )
            self.global_env.define(
                "Ceil", lambda x: float(_math.ceil(x)), exported=True
            )
            self.global_env.define("Round", lambda x: float(round(x)), exported=True)
            self.global_env.define("Pi", _math.pi, exported=True)
            self.global_env.define("E", _math.e, exported=True)
            # std/seq（Cento 自举）
            seq_exports = self._load_cent_module("seq")
            for name, fn in seq_exports.items():
                self.global_env.define(name, fn, exported=True)
            # std/util（Cento 自举）
            util_exports = self._load_cent_module("util")
            for name, fn in util_exports.items():
                self.global_env.define(name, fn, exported=True)

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

    def evaluate(self, node, env=None):
        if env is None:
            env = self.global_env
        return self._eval(node, env)

    def _eval(self, node, env):
        method = f"_eval_{type(node).__name__}"
        handler = getattr(self, method, None)
        if handler is None:
            raise CentoError(f"Cannot evaluate: {type(node).__name__}")
        return handler(node, env)

    def _eval_NumberLiteral(self, node, env):
        return node.value

    def _eval_StringLiteral(self, node, env):
        return node.value

    def _eval_BoolLiteral(self, node, env):
        return node.value

    def _eval_NilLiteral(self, node, env):
        return None

    def _eval_KeywordLiteral(self, node, env):
        return Keyword(node.name)

    def _eval_SymbolRef(self, node, env):
        return env.lookup(node.name)

    def _eval_ListLiteral(self, node, env):
        return CentoList([self._eval(el, env) for el in node.elements])

    def _eval_MapLiteral(self, node, env):
        d = {}
        for key_node, val_node in node.pairs:
            key = self._eval(key_node, env)
            val = self._eval(val_node, env)
            d[key] = val
        return CentoMap(d)

    def _eval_CallExpr(self, node, env):
        callee = self._eval(node.callee, env)
        args = [self._eval(arg, env) for arg in node.args]
        return self._apply(callee, args)

    def _eval_LetExpr(self, node, env):
        child = Environment(env)
        for name, value_expr in node.bindings:
            val = self._eval(value_expr, child)
            child.define(name, val)
        result = None
        for expr in node.body:
            result = self._eval(expr, child)
        return result

    def _eval_FnExpr(self, node, env):
        fn = Fn(
            name=node.name,
            fixed_params=node.fixed_params,
            rest_param=node.rest_param,
            body=node.body,
            env=env,
        )
        if node.name:
            fn_env = Environment(env)
            fn_env.define(node.name, fn)
            fn.env = fn_env
            env.define(node.name, fn)
        return fn

    def _eval_IfExpr(self, node, env):
        cond = self._eval(node.condition, env)
        if _is_truthy(cond):
            return self._eval(node.then_branch, env)
        elif node.else_branch is not None:
            return self._eval(node.else_branch, env)
        return None

    def _eval_CondExpr(self, node, env):
        for test_expr, result_expr in node.clauses:
            if _is_truthy(self._eval(test_expr, env)):
                return self._eval(result_expr, env)
        return None

    def _eval_ImportExpr(self, node, env):
        if not hasattr(self, "module_loader") or self.module_loader is None:
            raise CentoError("Module system not available")

        module_path = node.path
        if module_path.startswith("std/"):
            module_name = module_path[4:]
            exports = self.module_loader.load_native_std(module_name)
        else:
            exports = self.module_loader.load(module_path)

        if not exports:
            raise CentoError(f"Module not found: {module_path}")

        if node.symbols:
            for name, alias in node.symbols:
                if name not in exports:
                    raise CentoError(f"Symbol {name} not exported from {module_path}")
                bind_name = alias if alias else name
                env.define(bind_name, exports[name])
        else:
            for name, val in exports.items():
                env.define(name, val)

        return None

    def _eval_TryExpr(self, node, env):
        try:
            result = None
            for expr in node.body:
                result = self._eval(expr, env)
            return result
        except CentoError as e:
            if node.catch_param is not None and node.catch_body is not None:
                catch_env = Environment(env)
                error_val = e.data if e.data else e.message
                catch_env.define(node.catch_param, error_val)
                result = None
                for expr in node.catch_body:
                    result = self._eval(expr, catch_env)
                return result
            raise
        except Exception as e:
            if node.catch_param is not None and node.catch_body is not None:
                catch_env = Environment(env)
                catch_env.define(node.catch_param, str(e))
                result = None
                for expr in node.catch_body:
                    result = self._eval(expr, catch_env)
                return result
            raise
        finally:
            if node.finally_body is not None:
                for expr in node.finally_body:
                    self._eval(expr, env)

    def _apply(self, callee, args):
        if isinstance(callee, Fn):
            return self._apply_fn(callee, args)
        elif callable(callee):
            return callee(*args)
        else:
            raise CentoError(f"{callee!r} is not callable")

    def _apply_fn(self, fn_obj, args):
        fixed_count = len(fn_obj.fixed_params)
        if fn_obj.rest_param is None:
            if len(args) != fixed_count:
                raise CentoError(f"Expected {fixed_count} args, got {len(args)}")
        else:
            if len(args) < fixed_count:
                raise CentoError(
                    f"Expected at least {fixed_count} args, got {len(args)}"
                )

        call_env = Environment(fn_obj.env)
        for name, val in zip(fn_obj.fixed_params, args[:fixed_count]):
            call_env.define(name, val)
        if fn_obj.rest_param is not None:
            rest_args = CentoList(list(args[fixed_count:]))
            call_env.define(fn_obj.rest_param, rest_args)

        # TCO trampoline
        result = None
        body = fn_obj.body
        current_env = call_env

        while True:
            for i, expr in enumerate(body):
                is_tail = i == len(body) - 1
                if is_tail and isinstance(expr, CallExpr):
                    callee = self._eval(expr.callee, current_env)
                    if isinstance(callee, Fn):
                        args_vals = [self._eval(a, current_env) for a in expr.args]
                        callee_fixed = len(callee.fixed_params)
                        if callee.rest_param is None:
                            if len(args_vals) != callee_fixed:
                                raise CentoError(
                                    f"Expected {callee_fixed} args, got {len(args_vals)}"
                                )
                        elif len(args_vals) < callee_fixed:
                            raise CentoError(
                                f"Expected at least {callee_fixed} args, got {len(args_vals)}"
                            )
                        new_env = Environment(callee.env)
                        for pname, val in zip(
                            callee.fixed_params, args_vals[:callee_fixed]
                        ):
                            new_env.define(pname, val)
                        if callee.rest_param is not None:
                            new_env.define(
                                callee.rest_param,
                                CentoList(list(args_vals[callee_fixed:])),
                            )
                        body = callee.body
                        current_env = new_env
                        break  # restart while loop
                    else:
                        result = self._apply(
                            callee, [self._eval(a, current_env) for a in expr.args]
                        )
                        return result
                elif is_tail and isinstance(expr, IfExpr):
                    cond = self._eval(expr.condition, current_env)
                    if _is_truthy(cond):
                        if isinstance(expr.then_branch, (CallExpr, IfExpr)):
                            body = [expr.then_branch]
                            break  # restart while loop
                        result = self._eval(expr.then_branch, current_env)
                        return result
                    elif expr.else_branch is not None:
                        if isinstance(expr.else_branch, (CallExpr, IfExpr)):
                            body = [expr.else_branch]
                            break  # restart while loop
                        result = self._eval(expr.else_branch, current_env)
                        return result
                    return None
                else:
                    result = self._eval(expr, current_env)
            else:
                return result


def _product(args):
    result = 1.0
    for a in args:
        result *= a
    return result


def _is_truthy(val):
    if val is None:
        return False
    if isinstance(val, bool):
        return val
    return True


def _cento_type(val):
    if isinstance(val, bool):
        return "bool"
    if isinstance(val, (int, float)):
        return "number"
    if isinstance(val, str):
        return "string"
    if isinstance(val, CentoList):
        return "list"
    if isinstance(val, CentoMap):
        return "map"
    if isinstance(val, Fn) or callable(val):
        return "fn"
    if isinstance(val, Keyword):
        return "keyword"
    if val is None:
        return "nil"
    return "unknown"


def _print_fn(*args):
    parts = [_format_val(a) for a in args]
    print(" ".join(parts), end="")
    return None


def _println_fn(*args):
    parts = [_format_val(a) for a in args]
    print(" ".join(parts))
    return None


def _format_val(val):
    if isinstance(val, bool):
        return "true" if val else "false"
    if val is None:
        return "nil"
    if isinstance(val, float) and val == int(val):
        return str(int(val))
    if isinstance(val, CentoList):
        return "[" + " ".join(_format_val(v) for v in val) + "]"
    if isinstance(val, CentoMap):
        pairs = []
        for k, v in val.items():
            pairs.append(f"{_format_val(k)} {_format_val(v)}")
        return "{" + " ".join(pairs) + "}"
    if isinstance(val, Keyword):
        return f":{val.name}"
    if isinstance(val, Fn):
        return repr(val)
    return str(val)


def _str_fn(*args):
    return "".join(_format_val(a) for a in args)


def _count_fn(val):
    if isinstance(val, (CentoList, CentoMap, str)):
        return float(len(val))
    raise CentoError(f"count not supported for {type(val).__name__}")


def _empty_fn(val):
    if isinstance(val, (CentoList, CentoMap, str)):
        return len(val) == 0
    raise CentoError(f"empty? not supported for {type(val).__name__}")


def _first_fn(val):
    if isinstance(val, CentoList) and len(val) > 0:
        return val[0]
    return None


def _rest_fn(val):
    if isinstance(val, CentoList) and len(val) > 0:
        return CentoList(val[1:])
    return CentoList([])


def _get_fn(coll, key, default=None):
    if isinstance(coll, CentoMap):
        return coll.get(key, default)
    if isinstance(coll, CentoList):
        return coll[int(key)] if 0 <= int(key) < len(coll) else default
    return default


def _error_fn(msg, data=None):
    raise CentoError(msg, data=data)


def eval_str(code: str):
    from src.lexer import Lexer
    from src.parser import Parser

    tokens = Lexer(code).tokenize()
    ast = Parser(tokens).parse()
    ev = Evaluator()
    result = None
    for expr in ast.expressions:
        result = ev.evaluate(expr)
    return result
