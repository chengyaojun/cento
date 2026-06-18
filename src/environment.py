from src.errors import CentoError


class Environment:
    def __init__(self, parent=None):
        self.parent = parent
        self.bindings = {}
        self._exports = set()

    def define(self, name: str, value, exported=False):
        self.bindings[name] = value
        if exported:
            self._exports.add(name)

    def lookup(self, name: str):
        if name in self.bindings:
            return self.bindings[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        raise CentoError(f"Undefined symbol: {name}")

    def has(self, name: str) -> bool:
        if name in self.bindings:
            return True
        if self.parent is not None:
            return self.parent.has(name)
        return False

    def exports(self) -> set[str]:
        return self._exports.copy()

    def extend(self, bindings: dict) -> "Environment":
        child = Environment(self)
        for name, value in bindings.items():
            child.define(name, value)
        return child
