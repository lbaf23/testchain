"""
Sampling Filtering


"""

from utils import read_jsonlines, save_jsonlines, create_dirs, load_config, config_log
from code_datasets import LocalDataset
from code_evaluator import evaluator_factory
from tqdm import tqdm
import os
import argparse


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='config/leetcode-hard/config-gpt4o-code.json')
    parser.add_argument('--run_type', type=str, default='sampling_filtering')

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

    evaluator = evaluator_factory('py_asserts', 3.0)

    for i in dataset.data_range:
        if args.start < args.end and not args.start <= i < args.end:
            continue

        result_file = os.path.join(result_dir, f'result_{i}.jsonl')

        tests_file = os.path.join(tests_dir, f'result_{i}.jsonl')
        tests = read_jsonlines(tests_file)
        tests = [t['test_case'] for t in tests]
        tests = tests[ : max_tests]

        codes = read_jsonlines(os.path.join(codes_dir, f'result_{i}.jsonl'))
        codes = codes[ : max_codes]

        for c in tqdm(codes, desc=f'[{i}]'):
            code = c['code']
            code_res, _ = evaluator.evaluate(code, tests)
            c['score'] = code_res['score']

        save_jsonlines(result_file, codes)
