def identity_fn(x):
    return x


def inc_fn(x):
    return x + 1


def dec_fn(x):
    return x - 1


def even_pred(x):
    return int(x) % 2 == 0


def odd_pred(x):
    return int(x) % 2 != 0


def zero_pred(x):
    return x == 0


def pos_pred(x):
    return x > 0


def neg_pred(x):
    return x < 0


def parse_number_fn(s):
    return float(s)


def comp_fn(*fns):
    """组合多个函数: (Comp f g h) => x -> f(g(h(x)))"""
    if not fns:
        return identity_fn

    def composed(*args):
        # 从右向左应用：最右函数接收原始参数，其余接收单个值
        result = fns[-1](*args)
        for fn in reversed(fns[:-1]):
            result = fn(result)
        return result

    return composed


def apply_fn(fn, args):
    return fn(*list(args))


def const_fn(x):
    def const_inner(*_args):
        return x
    return const_inner


def complement_fn(fn):
    def complemented(*args):
        return not fn(*args)
    return complemented


FUNCTIONS = {
    "Identity": identity_fn,
    "Inc": inc_fn,
    "Dec": dec_fn,
    "Even?": even_pred,
    "Odd?": odd_pred,
    "Zero?": zero_pred,
    "Pos?": pos_pred,
    "Neg?": neg_pred,
    "Parse-number": parse_number_fn,
    "Comp": comp_fn,
    "Apply": apply_fn,
    "Const": const_fn,
    "Complement": complement_fn,
}
