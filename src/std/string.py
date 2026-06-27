from src.errors import CentoError


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

def char_at_fn(s, i):
    return s[int(i)]

def substring_fn(s, start, end=None):
    if end is None:
        return s[int(start):]
    return s[int(start):int(end)]

def from_code_fn(n):
    return chr(int(n))

def digit_q_fn(ch):
    return len(ch) == 1 and ch in "0123456789"

def alpha_q_fn(ch):
    return len(ch) == 1 and ch.isalpha() and ch.isascii()

def space_q_fn(ch):
    return len(ch) == 1 and ch.isspace() and ch.isascii()

def parse_number_fn(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        raise CentoError(f"Cannot parse number: {s}")


FUNCTIONS = {
    "Split": split_fn,
    "Join": join_fn,
    "Trim": trim_fn,
    "Upper": upper_fn,
    "Lower": lower_fn,
    "Replace": replace_fn,
    "Has-prefix": has_prefix_fn,
    "Has-suffix": has_suffix_fn,
    "char-at": char_at_fn,
    "substring": substring_fn,
    "from-code": from_code_fn,
    "digit?": digit_q_fn,
    "alpha?": alpha_q_fn,
    "space?": space_q_fn,
    "parse-number": parse_number_fn,
}
