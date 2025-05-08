import json
from typing import List, Dict
import os


def read_jsonlines(file_path: str) -> List[Dict]:
    data = []
    if not os.path.exists(file_path):
        return data

    with open(file_path, 'r') as file:
        line = file.readline()
        while line != '':
            line = json.loads(line)
            data.append(line)
            line = file.readline()
    return data


def save_jsonlines(file_path: str, lines: List[Dict]):
    if type(lines) == dict:
        lines = [lines]

    with open(file_path, 'w') as file:
        for line in lines:
            line = json.dumps(line)
            file.write(line + '\n')


def append_jsonlines(file_path: str, lines: List[Dict]):
    if type(lines) == dict:
        lines = [lines]

    with open(file_path, 'a') as file:
        for line in lines:
            line = json.dumps(line)
            file.write(line + '\n')
