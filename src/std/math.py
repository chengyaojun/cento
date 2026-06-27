"""Cento standard math library - mathematical functions and constants."""

import math


# Trigonometric functions
def sin_fn(x):
    return math.sin(x)


def cos_fn(x):
    return math.cos(x)


def tan_fn(x):
    return math.tan(x)


def asin_fn(x):
    return math.asin(x)


def acos_fn(x):
    return math.acos(x)


def atan_fn(x):
    return math.atan(x)


# Exponential and logarithmic
def exp_fn(x):
    return math.exp(x)


def log_fn(x):
    return math.log(x)  # natural logarithm


def log10_fn(x):
    return math.log10(x)


def sqrt_fn(x):
    return math.sqrt(x)


def pow_fn(base, exp):
    return math.pow(base, exp)


# Rounding
def floor_fn(x):
    return float(math.floor(x))


def ceil_fn(x):
    return float(math.ceil(x))


def round_fn(x):
    return float(round(x))


FUNCTIONS = {
    # Trigonometric
    "Sin": sin_fn,
    "Cos": cos_fn,
    "Tan": tan_fn,
    "Asin": asin_fn,
    "Acos": acos_fn,
    "Atan": atan_fn,
    # Exponential and logarithmic
    "Exp": exp_fn,
    "Log": log_fn,
    "Log10": log10_fn,
    "Sqrt": sqrt_fn,
    "Pow": pow_fn,
    # Rounding
    "Floor": floor_fn,
    "Ceil": ceil_fn,
    "Round": round_fn,
}
