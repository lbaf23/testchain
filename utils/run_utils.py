import torch
import os
from typing import List
from .jsonl_utils import read_jsonlines


def get_tests(file_path: str, max_tests: int = 10) -> List[str]:
    content = read_jsonlines(file_path)
    content = content[ : max_tests]
    tests = [c['test_case'] for c in content]
    return tests


def init_cuda():
    try:
        torch.cuda.empty_cache()
        os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:1024"
    except Exception:
        print('cuda emtpy cache failed.', flush=True)


def safe_div(a, b):
    return a / b if b > 0 else 0
