from src.environment import Environment


def test_define_and_lookup():
    env = Environment()
    env.define("x", 10)
    assert env.lookup("x") == 10

def test_lookup_not_found():
    env = Environment()
    try:
        env.lookup("x")
        assert False, "Should have raised"
    except Exception as e:
        assert "x" in str(e)

def test_nested_lookup():
    parent = Environment()
    parent.define("x", 10)
    child = Environment(parent)
    assert child.lookup("x") == 10

def test_child_shadows_parent():
    parent = Environment()
    parent.define("x", 10)
    child = Environment(parent)
    child.define("x", 20)
    assert child.lookup("x") == 20
    assert parent.lookup("x") == 10

def test_define_in_child_does_not_affect_parent():
    parent = Environment()
    child = Environment(parent)
    child.define("y", 30)
    assert child.lookup("y") == 30
    try:
        parent.lookup("y")
        assert False, "Should have raised"
    except Exception:
        pass

def test_exported_symbols():
    env = Environment()
    env.define("Add", 1, exported=True)
    env.define("helper", 2, exported=False)
    assert env.exports() == {"Add"}

def test_extend():
    parent = Environment()
    parent.define("x", 10)
    child = parent.extend({"y": 20})
    assert child.lookup("x") == 10
    assert child.lookup("y") == 20
