from src.errors import CentoError


class Keyword:
    __slots__ = ("name",)

    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, Keyword) and self.name == other.name

    def __hash__(self):
        return hash(("Keyword", self.name))

    def __repr__(self):
        return f":{self.name}"


class Symbol:
    __slots__ = ("name",)

    def __init__(self, name: str):
        self.name = name

    def __eq__(self, other):
        return isinstance(other, Symbol) and self.name == other.name

    def __hash__(self):
        return hash(("Symbol", self.name))

    def __repr__(self):
        return self.name


class Fn:
    __slots__ = ("name", "fixed_params", "rest_param", "body", "env")

    def __init__(self, name, fixed_params, rest_param, body, env):
        self.name = name
        self.fixed_params = fixed_params
        self.rest_param = rest_param
        self.body = body
        self.env = env

    def __repr__(self):
        if self.name:
            return f"<fn {self.name}>"
        return "<fn>"

    def __call__(self, *args):
        from src.evaluator import Evaluator
        ev = Evaluator.__new__(Evaluator)
        ev.global_env = self.env
        ev.module_loader = None
        return ev._apply_fn(self, list(args))


class CentoList(list):
    """Immutable list in Cento semantics, backed by Python list."""
    pass


class CentoMap(dict):
    """Immutable map in Cento semantics, backed by Python dict."""
    pass


class Ref:
    """Mutable reference cell."""
    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"<ref {self.value!r}>"


class CentoArray:
    """Mutable fixed-size array."""
    __slots__ = ("data",)

    def __init__(self, size: int):
        self.data = [None] * size

    def __repr__(self):
        return f"<array {self.data!r}>"


class MutableMap:
    """Mutable map."""
    __slots__ = ("data",)

    def __init__(self):
        self.data = {}

    def __repr__(self):
        return f"<mutable-map {self.data!r}>"
