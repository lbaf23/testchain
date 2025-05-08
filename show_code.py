from utils import read_jsonlines
import os
from argparse import  ArgumentParser


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--result_dir', type=str, default='result/leetcode-hard/gpt4o')
    parser.add_argument('--run_type_list', nargs='+', default=[
        'sampling',
        'sampling_filtering_0-shot',
        'sampling_filtering_1-shot',
        'sampling_filtering_testchain',
        'codet_0-shot',
        'codet_1-shot',
        'codet_testchain',
        'reflexion',
        'reflexion_0-shot',
        'reflexion_1-shot',
        'reflexion_testchain',
    ])
    parser.add_argument('--k_list', nargs='+', default=[1, 2, 3])
    parser.add_argument('--suffix_list', nargs='+', default=['-1', '-2', '-3'])
    parser.add_argument('--nums', type=int, default=50)
    args = parser.parse_args()

    k_list = args.k_list
    suffix_list = args.suffix_list
    run_type_list = args.run_type_list
    result_dir = args.result_dir

    for k in k_list:
        print(f'=== k={k} ===')
        for run_type in run_type_list:
            pass_rate = 0
            for suffix in suffix_list:
                file_path = os.path.join(result_dir, run_type, f'submit_nums={args.nums}_k={k}{suffix}.jsonl')
                content = read_jsonlines(file_path)

                if len(content) == 0 or not content[-1].__contains__('pass_rate'):
                    raise NotImplementedError(f'File {file_path} does not contain pass_rate')
                pass_rate += content[-1]['pass_rate']

            pass_rate /= len(suffix_list)
            print(f'{run_type}: {pass_rate * 100:.2f}')
