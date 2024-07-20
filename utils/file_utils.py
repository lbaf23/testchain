import json
import os
from typing import Dict, List


def count_lines(file_path: str) -> int:
    i = 0
    if not os.path.exists(file_path):
        return 0
    with open(file_path, 'r') as file:
        line = file.readline()
        while line != '':
            i += 1
            line = file.readline()
    return i


def append_line(file_path: str, content: str | Dict):
    if isinstance(content, dict):
        content = json.dumps(content)
    with open(file_path, 'a') as file:
        file.write(content + '\n')


def write_file(file_path: str, content: str | Dict):
    if isinstance(content, dict):
        content = json.dumps(content)
    with open(file_path, 'w') as file:
        file.write(content + '\n')


def create_dirs(file_dir: str):
    try:
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
    except Exception:
        pass


def safe_filename(filename: str) -> str:
    return ''.join([c for c in str(filename) if c.isalpha() or c.isdigit() or c == '_'])


def read_jsonl_all(file_path: str) -> List[Dict]:
    res = []
    with open(file_path, 'r') as file:
        line = file.readline()
        while line != '':
            res.append(json.loads(line))
            line = file.readline()
    return res


def write_jsonl_all(file_path: str, content: List[Dict]) -> None:
    assert type(content) == list
    with open(file_path, 'w') as file:
        for line in content:
            line = json.dumps(line)
            file.write(line + '\n')


def exists_file(file_path: str) -> str:
    return os.path.exists(file_path)


def read_file(file_path: str) -> str:
    with open(file_path, 'r') as file:
        content = file.read()
    return content


def read_last_line(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ''
    
    with open(file_path, 'r') as file:
        content = ''
        line = file.readline()
        while line != '':
            content = line
            line = file.readline()
    return content


def read_first_line(file_path: str) -> str:
    if not os.path.exists(file_path):
        return ''
    
    with open(file_path, 'r') as file:
        line = file.readline()
    return line


def create_or_clear_file(file_path: str):
    with open(file_path, 'w'):
        pass


def load_config(config_path):
    with open(config_path, 'r') as file:
        config = json.load(file)
    return config
