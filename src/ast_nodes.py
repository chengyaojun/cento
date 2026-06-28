from dataclasses import dataclass, field


@dataclass
class NumberLiteral:
    value: float


@dataclass
class StringLiteral:
    value: str


@dataclass
class BoolLiteral:
    value: bool


@dataclass
class NilLiteral:
    pass


@dataclass
class KeywordLiteral:
    name: str


@dataclass
class SymbolRef:
    name: str


@dataclass
class ListLiteral:
    elements: list


@dataclass
class MapLiteral:
    pairs: list  # list of (KeywordLiteral, expr) tuples


@dataclass
class CallExpr:
    callee: object
    args: list


@dataclass
class LetExpr:
    bindings: list  # list of (name: str, value_expr) tuples
    body: list  # list of exprs


@dataclass
class FnExpr:
    name: str | None
    fixed_params: list[str]
    rest_param: str | None
    body: list


@dataclass
class IfExpr:
    condition: object
    then_branch: object
    else_branch: object | None


@dataclass
class CondExpr:
    clauses: list  # list of (test_expr, result_expr) tuples


@dataclass
class ImportExpr:
    path: str
    symbols: list  # list of (name, alias) tuples, empty means import all


@dataclass
class TryExpr:
    body: list
    catch_param: str | None
    catch_body: list | None
    finally_body: list | None


@dataclass
class Program:
    expressions: list
