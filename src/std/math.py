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

FUNCTIONS = {
    # Trigonometric
    "Sin": sin_fn,
    "Cos": cos_fn,
    "Tan": tan_fn,
    "Asin": asin_fn,
    "Acos": acos_fn,
    "Atan": atan_fn,
}
