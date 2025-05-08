import os
from code_evaluator.coverage import coverage
from utils import read_jsonlines


def evaluate_coverage(
        dataset_path: str = 'data/humaneval-wo-examples.jsonl',
        test_dir: str = 'result/humaneval/gpt4o/TestChain_py_inter',
        max_test_nums: int = 20,
        time_limit: float = 10.0
):
    dataset = read_jsonlines(dataset_path)
    i = 0

    average_coverage = 0.0

    while True:
        test_file = os.path.join(test_dir, f'result_{i}.jsonl')
        if not os.path.exists(test_file):
            break

        tests = read_jsonlines(test_file)
        if max_test_nums > 0:
            tests = tests[ : max_test_nums]
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

        # print(f'[{i}], cov: {cov}, {len(tests)}')
        i += 1

    average_coverage /= i
    print(f'''
average_coverage: {average_coverage}
''')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset_path', type=str, default='')
    parser.add_argument('--base_dir', type=str)
    parser.add_argument('--max_nums', type=int, default=10)
    parser.add_argument('--time_limit', type=float, default=10.0)
    parser.add_argument('--start', type=float, default=0)
    parser.add_argument('--end', type=float, default=-1)
    args = parser.parse_args()

    if args.dataset_path != '':
        dataset_path = args.dataset_path
    elif args.base_dir.__contains__('humaneval'):
        dataset_path = 'data/humaneval-wo-examples.jsonl'
    elif args.base_dir.__contains__('leetcode-hard'):
        dataset_path = 'data/leetcode-hard-wo-examples.jsonl'
    else:
        raise NotImplementedError

    evaluate_coverage(dataset_path, args.base_dir, args.max_nums, args.time_limit)
