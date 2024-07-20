import os
from code_evaluator.coverage import coverage
from utils import read_jsonlines


def evaluate_coverage(
        dataset_path: str,
        base_dir: str,
        max_nums: int = 10,
        time_limit: float = 10.0
):
    dataset = read_jsonlines(dataset_path)
    i = 0
    average_coverage = 0.0

    while True:
        test_file = os.path.join(base_dir, f'result_{i}.jsonl')
        if not os.path.exists(test_file):
            break

        tests = read_jsonlines(test_file)
        if max_nums > 0:
            tests = tests[ : max_nums]
        # choose correct cases
        tests = [t['test_case'] for t in tests if t['correct']]

        if dataset_path.__contains__('humaneval'):
            prefix = dataset[i]['prompt']
            code = dataset[i]['prompt'] + dataset[i]['canonical_solution']
        else:
            prefix = ''
            code = dataset[i]['solution']

        if len(tests) > 0:
            cov, _, _ = coverage(prefix, code, tests, time_limit=time_limit)
        else:
            cov = 0

        average_coverage += cov
        i += 1

    average_coverage /= i
    print(f'''
average_coverage: {round(average_coverage * 100, 5)} %
''')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_path', type=str, default='data/humaneval-wo-examples.jsonl')
    parser.add_argument('--base_dir', type=str, default='result/humaneval/gpt35/TestChain_py_inter')
    parser.add_argument('--max_nums', type=int, default=10)
    parser.add_argument('--time_limit', type=float, default=10.0)
    args = parser.parse_args()

    evaluate_coverage(args.dataset_path, args.base_dir, args.max_nums, args.time_limit)
