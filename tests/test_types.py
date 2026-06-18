from src.types import Keyword, Symbol, Fn, CentoList, CentoMap, Ref, CentoArray, MutableMap
from src.errors import CentoError

def test_keyword_equality():
    assert Keyword("name") == Keyword("name")
    assert Keyword("name") != Keyword("age")

def test_keyword_repr():
    assert repr(Keyword("name")) == ":name"

def test_symbol_equality():
    assert Symbol("foo") == Symbol("foo")
    assert Symbol("foo") != Symbol("bar")

def test_symbol_repr():
    assert repr(Symbol("foo")) == "foo"

def test_fn_creation():
    env = {}
    fn = Fn(name="add", params=["a", "b"], body=[], env=env)
    assert fn.name == "add"
    assert fn.params == ["a", "b"]

def test_cento_list_is_list():
    lst = CentoList([1, 2, 3])
    assert isinstance(lst, list)
    assert len(lst) == 3

def test_cento_map_is_dict():
    m = CentoMap({Keyword("a"): 1})
    assert isinstance(m, dict)
    assert m[Keyword("a")] == 1

def test_ref_creation():
    r = Ref(42)
    assert r.value == 42

def test_ref_mutation():
    r = Ref(0)
    r.value = 10
    assert r.value == 10

def test_cento_array():
    arr = CentoArray(3)
    arr.data[0] = 10
    assert arr.data[0] == 10

def test_mutable_map():
    m = MutableMap()
    m.data[Keyword("x")] = 1
    assert m.data[Keyword("x")] == 1

def test_cento_error():
    err = CentoError("something went wrong")
    assert str(err) == "something went wrong"
    assert isinstance(err, Exception)

def test_cento_error_with_data():
    err = CentoError("error", data={Keyword("code"): 404})
    assert err.data == {Keyword("code"): 404}
