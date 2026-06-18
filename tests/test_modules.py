import os
import tempfile
import pytest
from src.modules import ModuleLoader
from src.evaluator import Evaluator


def test_load_module_from_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        mod_path = os.path.join(tmpdir, "mymod.ct")
        with open(mod_path, "w") as f:
            f.write('(fn Add [a b] (+ a b))\n(let [Pi 3.14])')
        loader = ModuleLoader(search_paths=[tmpdir])
        exports = loader.load("mymod")
        assert "Add" in exports
        assert "Pi" in exports
        assert "helper" not in exports  # lowercase = not exported

def test_module_caching():
    with tempfile.TemporaryDirectory() as tmpdir:
        mod_path = os.path.join(tmpdir, "mymod.ct")
        with open(mod_path, "w") as f:
            f.write('(let [X 1])')
        loader = ModuleLoader(search_paths=[tmpdir])
        exports1 = loader.load("mymod")
        exports2 = loader.load("mymod")
        assert exports1 is exports2

def test_import_in_evaluator():
    with tempfile.TemporaryDirectory() as tmpdir:
        mod_path = os.path.join(tmpdir, "mymod.ct")
        with open(mod_path, "w") as f:
            f.write('(fn Double [x] (* x 2))')
        ev = Evaluator()
        ev.module_loader = ModuleLoader(search_paths=[tmpdir])
        from src.lexer import Lexer
        from src.parser import Parser
        code = '(import "mymod" [Double]) (Double 5)'
        tokens = Lexer(code).tokenize()
        ast = Parser(tokens).parse()
        result = None
        for expr in ast.expressions:
            result = ev.evaluate(expr)
        assert result == 10.0
