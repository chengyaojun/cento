import sys
from src.lexer import Lexer
from src.parser import Parser
from src.evaluator import Evaluator
from src.errors import CentoError


def start_repl():
    evaluator = Evaluator()
    print("Cento 0.1.0")
    print("Type (exit) to quit")

    while True:
        try:
            line = input("cento> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        line = line.strip()
        if not line:
            continue
        if line == "(exit)":
            break

        # Accumulate multi-line input for balanced parens
        source = line
        while not _balanced(source):
            try:
                continuation = input("  ... ")
            except (EOFError, KeyboardInterrupt):
                print()
                source = ""
                break
            source += "\n" + continuation

        if not source:
            continue

        try:
            tokens = Lexer(source).tokenize()
            ast = Parser(tokens).parse()
            result = None
            for expr in ast.expressions:
                result = evaluator.evaluate(expr)
            if result is not None:
                from src.evaluator import _format_val
                print(_format_val(result))
        except CentoError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error: {e}")


def _balanced(source: str) -> bool:
    """Check if parentheses, brackets, and braces are balanced."""
    depth = 0
    in_string = False
    i = 0
    while i < len(source):
        ch = source[i]
        if ch == '"' and not in_string:
            in_string = True
        elif ch == '"' and in_string:
            in_string = False
        elif not in_string:
            if ch in '([{':
                depth += 1
            elif ch in ')]}':
                depth -= 1
        i += 1
    return depth <= 0
