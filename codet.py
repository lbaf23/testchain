"""
CodeT

"""

from code_datasets import LocalDataset
from code_evaluator import evaluator_factory, CodeEvaluator
from typing import Tuple, List, Dict
from utils import read_jsonlines, save_jsonlines, create_dirs, load_config
from tqdm import tqdm
import math
import argparse
import os


def CodeT(
        index: int,
        codes: List[str],
        tests: List[str],
        result_file: str,
        evaluator: CodeEvaluator,
) -> None:
    code_passed_tests = [[] for _ in range(len(codes))]
    """
    code i passed tests:
        code_passed_tests[i] = [test_index1, test_index2, ...]
    """

    for i, code in tqdm(enumerate(codes), desc=f'[{index}]'):
        _, test_res = evaluator.evaluate(code, tests)
        tests_index = []
        for j, r in enumerate(test_res):
            if r['passed']:
                tests_index.append(j)
        code_passed_tests[i] = tests_index

    # agreement groups
    agreement = dict()
    """
    test_set : code_set
        agreement[tuple(tests_index)] = [code_index1, code_index2, ...]
    """
    for i, code in enumerate(codes):
        tests_index = tuple(code_passed_tests[i])
        if agreement.__contains__(tests_index):
            agreement[tests_index].append(i)
        else:
            agreement[tests_index] = [i]

    res = []
    for k in agreement.keys():
        codes_i = [codes[index] for index in agreement[k]]
        tests_i = [tests[index] for index in k]
        reward = math.sqrt(len(codes_i)) * len(tests_i)
        res.append({
            'reward': reward,
            'codes': codes_i,
            'tests': tests_i,
        })

    res = sorted(res, key=lambda x: x['reward'], reverse=True)
    save_jsonlines(result_file, res)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='config/leetcode-hard/config-gpt4o-code.json')
    parser.add_argument('--run_type', type=str, default='codet')

    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=-1)

    parser.add_argument('--rerun', action='store_true')
    args = parser.parse_args()
    config = load_config(args.config)
    print(config, flush=True)

    dataset = LocalDataset(**config['dataset'])

    result_dir = os.path.join(config['result_dir'], args.run_type)

    create_dirs(result_dir)

    run_config = config[args.run_type]
    max_codes = run_config['max_codes']

    max_tests = 10
    codes_dir = os.path.join(config['result_dir'], run_config['codes'])
    tests_dir = os.path.join(config['result_dir'], run_config['tests'])

    evaluator = evaluator_factory('py_asserts', 5.0)

    for i in dataset.data_range:
        if args.start < args.end and not args.start <= i < args.end:
            continue

        data = dataset.get_data(i)

        result_file = os.path.join(result_dir, f'result_{i}.jsonl')

        codes_file = os.path.join(codes_dir, f'result_{i}.jsonl')
        codes = read_jsonlines(codes_file)
        codes = [c['code'] for c in codes]
        codes = codes[ : max_codes]

        tests_file = os.path.join(tests_dir, f'result_{i}.jsonl')
        tests = read_jsonlines(tests_file)
        tests = [t['test_case'] for t in tests]
        tests = tests[ : max_tests]

        CodeT(
            index=i,
            codes=codes,
            tests=tests,
            result_file=result_file,
            evaluator=evaluator
        )
