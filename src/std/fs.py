import os
from src.types import CentoList


def exists_fn(path):
    return os.path.exists(path)

def is_dir_fn(path):
    return os.path.isdir(path)

def list_dir_fn(path):
    return CentoList(os.listdir(path))

def mkdir_fn(path):
    os.makedirs(path, exist_ok=True)
    return None

def rmdir_fn(path):
    import shutil
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)
    return None


FUNCTIONS = {
    "Exists?": exists_fn,
    "Is-dir?": is_dir_fn,
    "List-dir": list_dir_fn,
    "Mkdir": mkdir_fn,
    "Rmdir": rmdir_fn,
}
