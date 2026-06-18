# tests/test_parser.py
import pytest
from src.lexer import Lexer
from src.parser import Parser
from src.ast_nodes import *


def test_number():
    ast = Parser(Lexer("42").tokenize()).parse()
    assert ast.expressions == [NumberLiteral(42.0)]

def test_string():
    ast = Parser(Lexer('"hello"').tokenize()).parse()
    assert ast.expressions == [StringLiteral("hello")]

def test_bool():
    ast = Parser(Lexer("true").tokenize()).parse()
    assert ast.expressions == [BoolLiteral(True)]

def test_nil():
    ast = Parser(Lexer("nil").tokenize()).parse()
    assert ast.expressions == [NilLiteral()]

def test_keyword():
    ast = Parser(Lexer(":name").tokenize()).parse()
    assert ast.expressions == [KeywordLiteral("name")]

def test_symbol():
    ast = Parser(Lexer("foo").tokenize()).parse()
    assert ast.expressions == [SymbolRef("foo")]

def test_list_literal():
    ast = Parser(Lexer("[1 2 3]").tokenize()).parse()
    assert ast.expressions == [ListLiteral([NumberLiteral(1.0), NumberLiteral(2.0), NumberLiteral(3.0)])]

def test_map_literal():
    ast = Parser(Lexer('{:a 1 :b 2}').tokenize()).parse()
    assert ast.expressions == [MapLiteral([
        (KeywordLiteral("a"), NumberLiteral(1.0)),
        (KeywordLiteral("b"), NumberLiteral(2.0)),
    ])]

def test_call():
    ast = Parser(Lexer("(+ 1 2)").tokenize()).parse()
    assert ast.expressions == [CallExpr(
        callee=SymbolRef("+"),
        args=[NumberLiteral(1.0), NumberLiteral(2.0)],
    )]

def test_let():
    ast = Parser(Lexer('(let [x 10] (+ x 1))').tokenize()).parse()
    assert ast.expressions == [LetExpr(
        bindings=[("x", NumberLiteral(10.0))],
        body=[CallExpr(callee=SymbolRef("+"), args=[SymbolRef("x"), NumberLiteral(1.0)])],
    )]

def test_fn():
    ast = Parser(Lexer('(fn add [a b] (+ a b))').tokenize()).parse()
    assert ast.expressions == [FnExpr(
        name="add",
        params=["a", "b"],
        body=[CallExpr(callee=SymbolRef("+"), args=[SymbolRef("a"), SymbolRef("b")])],
    )]

def test_anonymous_fn():
    ast = Parser(Lexer('(fn [x] (* x 2))').tokenize()).parse()
    assert ast.expressions == [FnExpr(
        name=None,
        params=["x"],
        body=[CallExpr(callee=SymbolRef("*"), args=[SymbolRef("x"), NumberLiteral(2.0)])],
    )]

def test_if():
    ast = Parser(Lexer('(if (> x 0) "pos" "neg")').tokenize()).parse()
    assert ast.expressions == [IfExpr(
        condition=CallExpr(callee=SymbolRef(">"), args=[SymbolRef("x"), NumberLiteral(0.0)]),
        then_branch=StringLiteral("pos"),
        else_branch=StringLiteral("neg"),
    )]

def test_if_no_else():
    ast = Parser(Lexer('(if true 1)').tokenize()).parse()
    assert ast.expressions == [IfExpr(
        condition=BoolLiteral(True),
        then_branch=NumberLiteral(1.0),
        else_branch=None,
    )]

def test_import():
    ast = Parser(Lexer('(import "std/io" [print])').tokenize()).parse()
    assert ast.expressions == [ImportExpr(
        path="std/io",
        symbols=[("print", None)],
    )]

def test_import_with_alias():
    ast = Parser(Lexer('(import "std/math" [add :as plus])').tokenize()).parse()
    assert ast.expressions == [ImportExpr(
        path="std/math",
        symbols=[("add", "plus")],
    )]

def test_try_catch():
    ast = Parser(Lexer('(try (foo) (catch [e] (print e)))').tokenize()).parse()
    assert ast.expressions == [TryExpr(
        body=[CallExpr(callee=SymbolRef("foo"), args=[])],
        catch_param="e",
        catch_body=[CallExpr(callee=SymbolRef("print"), args=[SymbolRef("e")])],
        finally_body=None,
    )]

def test_nested_expressions():
    code = '(let [f (fn [x] (* x 2))] (f 3))'
    ast = Parser(Lexer(code).tokenize()).parse()
    assert ast.expressions == [LetExpr(
        bindings=[("f", FnExpr(name=None, params=["x"], body=[CallExpr(callee=SymbolRef("*"), args=[SymbolRef("x"), NumberLiteral(2.0)])]))],
        body=[CallExpr(callee=SymbolRef("f"), args=[NumberLiteral(3.0)])],
    )]
