from src.types import CentoList


def sort_fn(lst):
    return CentoList(sorted(lst))


def sort_desc_fn(lst):
    return CentoList(sorted(lst, reverse=True))


def sort_by_fn(fn, lst):
    return CentoList(sorted(lst, key=fn))


def sort_by_desc_fn(fn, lst):
    return CentoList(sorted(lst, key=fn, reverse=True))


def take_fn(n, lst):
    return CentoList(list(lst)[:int(n)])


def drop_fn(n, lst):
    return CentoList(list(lst)[int(n):])


def nth_fn(lst, i):
    idx = int(i)
    if idx < 0 or idx >= len(lst):
        raise IndexError(f"Nth index {idx} out of range (length {len(lst)})")
    return lst[idx]


def last_fn(lst):
    items = list(lst)
    if not items:
        raise IndexError("Last of empty list")
    return items[-1]


def range_fn(start, end, step=1):
    return CentoList([float(x) for x in range(int(start), int(end), int(step))])


def distinct_fn(lst):
    seen = []
    result = []
    for x in lst:
        if x not in seen:
            seen.append(x)
            result.append(x)
    return CentoList(result)


def flatten_fn(lst):
    result = []
    for x in lst:
        if isinstance(x, (list, CentoList)):
            result.extend(flatten_fn(x))
        else:
            result.append(x)
    return CentoList(result)


def zip_fn(lst1, lst2):
    result = []
    for a, b in zip(lst1, lst2):
        result.append(CentoList([a, b]))
    return CentoList(result)


def reverse_fn(lst):
    return CentoList(list(reversed(list(lst))))


FUNCTIONS = {
    "Sort": sort_fn,
    "Sort-desc": sort_desc_fn,
    "Sort-by": sort_by_fn,
    "Sort-by-desc": sort_by_desc_fn,
    "Take": take_fn,
    "Drop": drop_fn,
    "Nth": nth_fn,
    "Last": last_fn,
    "Range": range_fn,
    "Distinct": distinct_fn,
    "Flatten": flatten_fn,
    "Zip": zip_fn,
    "Reverse": reverse_fn,
}
