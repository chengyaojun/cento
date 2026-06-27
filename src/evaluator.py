from src.ast_nodes import *
from src.types import Keyword, Symbol, Fn, CentoList, CentoMap
from src.environment import Environment
from src.errors import CentoError


class Evaluator:
    def __init__(self):
        self.global_env = Environment()
        self.module_loader = None
        self._register_builtins()

    def _register_builtins(self):
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
        self.global_env.define("apply",
            lambda fn, args: self._apply(fn, list(args)))
        # Error
        self.global_env.define("error", _error_fn)
        # std/mutable
        from src.std.mutable import FUNCTIONS as MUTABLE_FUNCTIONS
        for name, fn in MUTABLE_FUNCTIONS.items():
            self.global_env.define(name, fn, exported=True)
        # std/collection
        from src.std.collection import FUNCTIONS as COLLECTION_FUNCTIONS
        for name, fn in COLLECTION_FUNCTIONS.items():
            self.global_env.define(name, fn, exported=True)
        # std/string
        from src.std.string import FUNCTIONS as STRING_FUNCTIONS
        for name, fn in STRING_FUNCTIONS.items():
            self.global_env.define(name, fn, exported=True)
        # std/io
        from src.std.io import FUNCTIONS as IO_FUNCTIONS
        for name, fn in IO_FUNCTIONS.items():
            self.global_env.define(name, fn, exported=True)
        # std/fs
        from src.std.fs import FUNCTIONS as FS_FUNCTIONS
        for name, fn in FS_FUNCTIONS.items():
            self.global_env.define(name, fn, exported=True)

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
        fn = Fn(name=node.name, params=node.params, body=node.body, env=env)
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

    def _eval_ImportExpr(self, node, env):
        if not hasattr(self, 'module_loader') or self.module_loader is None:
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
        if len(args) != len(fn_obj.params):
            raise CentoError(f"Expected {len(fn_obj.params)} args, got {len(args)}")

        call_env = Environment(fn_obj.env)
        for name, val in zip(fn_obj.params, args):
            call_env.define(name, val)

        # TCO trampoline
        result = None
        body = fn_obj.body
        current_env = call_env

        while True:
            for i, expr in enumerate(body):
                is_tail = (i == len(body) - 1)
                if is_tail and isinstance(expr, CallExpr):
                    callee = self._eval(expr.callee, current_env)
                    if isinstance(callee, Fn):
                        args_vals = [self._eval(a, current_env) for a in expr.args]
                        if len(args_vals) != len(callee.params):
                            raise CentoError(f"Expected {len(callee.params)} args, got {len(args_vals)}")
                        new_env = Environment(callee.env)
                        for pname, val in zip(callee.params, args_vals):
                            new_env.define(pname, val)
                        body = callee.body
                        current_env = new_env
                        break  # restart while loop
                    else:
                        result = self._apply(callee, [self._eval(a, current_env) for a in expr.args])
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
