from src.types import Ref, CentoArray, MutableMap, Keyword


def make_ref(value):
    return Ref(value)

def ref_get(r):
    return r.value

def ref_set(r, value):
    r.value = value
    return value

def make_array(size):
    return CentoArray(int(size))

def array_get(arr, index):
    return arr.data[int(index)]

def array_set(arr, index, value):
    arr.data[int(index)] = value
    return value

def make_mutable_map():
    return MutableMap()

def mutable_map_get(m, key):
    return m.data.get(key)

def mutable_map_set(m, key, value):
    m.data[key] = value
    return value


# Registry of all std/mutable functions
FUNCTIONS = {
    "Ref": make_ref,
    "Ref-get": ref_get,
    "Ref-set!": ref_set,
    "Array": make_array,
    "Array-get": array_get,
    "Array-set!": array_set,
    "Mutable-map": make_mutable_map,
    "Mutable-map-get": mutable_map_get,
    "Mutable-map-set!": mutable_map_set,
}
