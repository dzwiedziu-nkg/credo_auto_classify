import os
from typing import List, Iterable


def create_dir_if_not_exist(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def read_file_to_lines(fn: str) -> List[str]:
    try:
        with open(fn, 'rt') as f:
            return f.read().splitlines()
    except FileNotFoundError:
        return []


def append_lines_to_file(fn: str, lines: Iterable[str]) -> None:
    with open(fn, 'at') as f:
        f.writelines(map(lambda a: a + '\n' if len(a) > 0 and a[-1] != '\n' else a, lines))
