from src.types import CentoList, CentoMap, Keyword


def map_fn(fn, lst):
    return CentoList([fn(x) for x in lst])

def filter_fn(fn, lst):
    return CentoList([x for x in lst if fn(x)])

def reduce_fn(fn, init, lst):
    result = init
    for x in lst:
        result = fn(result, x)
    return result

def each_fn(fn, lst):
    for x in lst:
        fn(x)
    return None

def concat_fn(*lists):
    result = []
    for lst in lists:
        result.extend(lst)
    return CentoList(result)

def contains_fn(lst, val):
    return val in lst

def assoc_fn(m, key, val):
    new_m = CentoMap(dict(m))
    new_m[key] = val
    return new_m

def dissoc_fn(m, key):
    new_m = CentoMap(dict(m))
    new_m.pop(key, None)
    return new_m

def keys_fn(m):
    return CentoList(list(m.keys()))

def values_fn(m):
    return CentoList(list(m.values()))

def merge_fn(*maps):
    result = {}
    for m in maps:
        result.update(m)
    return CentoMap(result)


FUNCTIONS = {
    "Map": map_fn,
    "Filter": filter_fn,
    "Reduce": reduce_fn,
    "Each": each_fn,
    "Concat": concat_fn,
    "Contains": contains_fn,
    "Assoc": assoc_fn,
    "Dissoc": dissoc_fn,
    "Keys": keys_fn,
    "Values": values_fn,
    "Merge": merge_fn,
}
