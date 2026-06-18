import sys
import os
from src.repl import start_repl
from src.lexer import Lexer
from src.parser import Parser
from src.evaluator import Evaluator
from src.errors import CentoError
from src.modules import ModuleLoader


def main():
    args = sys.argv[1:]

    if not args:
        start_repl()
        return

    if args[0] == "run":
        if len(args) < 2:
            print("Usage: cento run <file.ct> [args...]", file=sys.stderr)
            sys.exit(1)
        filepath = args[1]
        run_file(filepath, args[2:])
    else:
        print(f"Unknown command: {args[0]}", file=sys.stderr)
        print("Usage: cento [run <file.ct>]", file=sys.stderr)
        sys.exit(1)


def run_file(filepath: str, cli_args: list[str] | None = None):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
    except FileNotFoundError:
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    try:
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        evaluator = Evaluator()
        file_dir = os.path.dirname(os.path.abspath(filepath))
        evaluator.module_loader = ModuleLoader(search_paths=[file_dir])
        if cli_args:
            evaluator.global_env.define("*args*", cli_args)
        for expr in ast.expressions:
            evaluator.evaluate(expr)
    except CentoError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
