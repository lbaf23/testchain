import ast
from typing import List
import datetime
import ast
import re
import astunparse
import black
from io import StringIO
import sys


def extract_test_cases(output: str) -> List[str]:
    """
    extract line start with assert, may contains some errors or duplicated
    """
    blocks = extract_blocks(output)
    for i in range(len(blocks)):
        try:
            blocks[i] = format_code(blocks[i], 'py')
        except Exception:
            pass
    content = '\n'.join(blocks) if len(blocks) > 0 else output
    content = content.split('\n')

    test_cases = []
    for line in content:
        line = line.strip()
        if line.startswith('assert'):
            test_cases.append(line)

    return test_cases


def extract_test_inputs(output: str, prefix: str = 'input:') -> List[str]:
    """
    extract line start with `input:`, may contains some errors or duplicated
    """
    blocks = extract_blocks(output, 'text')
    content = '\n'.join(blocks) if len(blocks) > 0 else output
    
    inputs = []
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith(prefix):
            inputs.append(line[line.index(prefix) + len(prefix) : ].strip())
    return inputs


def is_test_valid(test: str, entry_point: str) -> bool:
    return test.__contains__(entry_point)


def is_syntax_valid(code: str, lang: str = 'py') -> bool:
    """
    filter 1
    """
    if lang == 'py':
        try:
            ast.parse(code)
            return True
        except Exception:
            return False
    else:
        raise NotImplementedError


def now_time():
    return str(datetime.datetime.now())


def format_code(code: str, lang: str = 'py') -> str:
    if lang == 'py':
        code = ast.parse(code)
        code = astunparse.unparse(code)
        code = black.format_str(code, mode=black.Mode(line_length=100000))
        code = code.strip()
        return code
    else:
        raise NotImplementedError


def print_float(f: float) -> float:
    return round(f, 5)


def extract_first_block(content: str, lang: str = 'python') -> str:
    matches = extract_blocks(content, lang)
    if len(matches) > 0:
        return matches[0]
    return ''


def extract_blocks(content: str, lang: str = 'python') -> List[str]:
    # python code block
    pattern = fr"```{lang}\n(.*?)\n```"
    matches = re.findall(pattern, content, re.DOTALL)
    if len(matches) > 0:
        return matches

    # any block
    pattern = r'```.*?\n([\s\S]*?)\n```'
    matches = re.findall(pattern, content, re.DOTALL)
    return matches


class StdUtils:
    def __init__(self) -> None:
        self.stdin = sys.stdin
        self.stdout = sys.stdout
        self.stderr = sys.stderr
    
    def redirect(self):
        sys.stdin = StringIO()
        sys.stdout = StringIO()
        sys.stderr = StringIO()
    
    def recover(self):
        sys.stdin = self.stdin
        sys.stdout = self.stdout
        sys.stderr = self.stderr


class ExtractInputTransformer(ast.NodeTransformer):
    def visit_Assert(self, node):
        if isinstance(node.test, ast.Compare):
            func_call = node.test.left
        elif isinstance(node.test, ast.Call):
            func_call = node.test
        else:
            return node
        return ast.List(func_call.args)


def extract_inputs(test: str) -> str:
    tree = ast.parse(test)
    trans = ExtractInputTransformer()
    new_tree = trans.visit(tree)
    return astunparse.unparse(new_tree).strip()
