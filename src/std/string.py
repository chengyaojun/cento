def split_fn(s, sep):
    from src.types import CentoList
    return CentoList(s.split(sep))

def join_fn(lst, sep):
    return sep.join(str(x) for x in lst)

def trim_fn(s):
    return s.strip()

def upper_fn(s):
    return s.upper()

def lower_fn(s):
    return s.lower()

def replace_fn(s, old, new):
    return s.replace(old, new)

def has_prefix_fn(s, prefix):
    return s.startswith(prefix)

def has_suffix_fn(s, suffix):
    return s.endswith(suffix)


FUNCTIONS = {
    "Split": split_fn,
    "Join": join_fn,
    "Trim": trim_fn,
    "Upper": upper_fn,
    "Lower": lower_fn,
    "Replace": replace_fn,
    "Has-prefix": has_prefix_fn,
    "Has-suffix": has_suffix_fn,
}
