import os
from src.lexer import Lexer
from src.parser import Parser
from src.evaluator import Evaluator
from src.environment import Environment
from src.errors import CentoError


class _ModuleEvaluator(Evaluator):
    """Evaluator subclass that promotes top-level let bindings to the module environment."""
    def _eval_LetExpr(self, node, env):
        child = Environment(env)
        for name, value_expr in node.bindings:
            val = self._eval(value_expr, child)
            child.define(name, val)
            # Also define in the parent (module) environment for export
            env.define(name, val)
        result = None
        for expr in node.body:
            result = self._eval(expr, child)
        return result


class ModuleLoader:
    def __init__(self, search_paths=None, std_path=None):
        self.search_paths = search_paths or []
        self.std_path = std_path or os.path.join(os.path.dirname(__file__), "std")
        self.cache = {}  # path -> exports dict

    def load(self, module_path: str) -> dict:
        if module_path in self.cache:
            return self.cache[module_path]

        file_path = self._resolve(module_path)
        if file_path is None:
            raise CentoError(f"Module not found: {module_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()

        evaluator = _ModuleEvaluator()
        evaluator.module_loader = self
        module_env = Environment(evaluator.global_env)
        for expr in ast.expressions:
            evaluator.evaluate(expr, module_env)

        exports = {}
        # Names starting with uppercase are automatically exported
        for name, value in module_env.bindings.items():
            if name[0].isupper():
                exports[name] = value
        # Also include explicitly marked exports
        for name in module_env.exports():
            if name not in exports:
                exports[name] = module_env.lookup(name)

        self.cache[module_path] = exports
        return exports

    def _resolve(self, module_path: str) -> str | None:
        if module_path.startswith("std/"):
            rel = module_path[4:]
            file_path = os.path.join(self.std_path, rel + ".ct")
            if os.path.exists(file_path):
                return file_path
            return None

        for base in self.search_paths:
            file_path = os.path.join(base, module_path + ".ct")
            if os.path.exists(file_path):
                return file_path

        return None

    def load_native_std(self, module_name: str) -> dict:
        native_modules = {
            "collection": self._load_native_collection,
            "string": self._load_native_string,
            "io": self._load_native_io,
            "fs": self._load_native_fs,
            "mutable": self._load_native_mutable,
        }
        loader = native_modules.get(module_name)
        if loader:
            return loader()
        return {}

    def _load_native_collection(self):
        from src.std.collection import FUNCTIONS
        return dict(FUNCTIONS)

    def _load_native_string(self):
        from src.std.string import FUNCTIONS
        return dict(FUNCTIONS)

    def _load_native_io(self):
        from src.std.io import FUNCTIONS
        return dict(FUNCTIONS)

    def _load_native_fs(self):
        from src.std.fs import FUNCTIONS
        return dict(FUNCTIONS)

    def _load_native_mutable(self):
        from src.std.mutable import FUNCTIONS
        return dict(FUNCTIONS)
