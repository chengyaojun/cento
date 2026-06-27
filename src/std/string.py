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


def substr_fn(s, start, end):
    return s[int(start):int(end)]

def index_of_fn(s, sub):
    return float(s.find(sub))

def includes_fn(s, sub):
    return sub in s

def reverse_str_fn(s):
    return s[::-1]

def repeat_fn(s, n):
    return s * int(n)

def char_at_fn(s, i):
    return s[int(i)]

def split_lines_fn(s):
    from src.types import CentoList
    return CentoList(s.split("\n"))

def len_fn(s):
    return float(len(s))


FUNCTIONS = {
    "Split": split_fn,
    "Join": join_fn,
    "Trim": trim_fn,
    "Upper": upper_fn,
    "Lower": lower_fn,
    "Replace": replace_fn,
    "Has-prefix": has_prefix_fn,
    "Has-suffix": has_suffix_fn,
    "Substr": substr_fn,
    "Index-of": index_of_fn,
    "Includes": includes_fn,
    "Reverse-str": reverse_str_fn,
    "Repeat": repeat_fn,
    "Char-at": char_at_fn,
    "Split-lines": split_lines_fn,
    "Len": len_fn,
}
