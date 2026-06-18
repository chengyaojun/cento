import sys


def read_line_fn():
    return sys.stdin.readline().rstrip("\n")

def read_file_fn(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file_fn(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return None


FUNCTIONS = {
    "Read-line": read_line_fn,
    "Read-file": read_file_fn,
    "Write-file": write_file_fn,
}
