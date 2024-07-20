from argparse import ArgumentParser
from utils import read_jsonl_all
import os
import json
from typing import Dict, List


def load_codes(code_file: str) -> List[str]:
    codes = []
    with open(code_file, 'r') as file:
        line = file.readline()
        while line != '':
            d = json.loads(line)
            codes.append(d['code'])
            line = file.readline()
    return codes


def round_percentage(f: float):
    return round(f * 100, 5)


def count():
    parser = ArgumentParser()
    parser.add_argument('--base_dir', type=str)
    parser.add_argument('--max_nums', type=int, default=10)

    parser.add_argument('--detail', action='store_true')
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=200)
    args = parser.parse_args()


    avg_correct_nums = 0
    avg_accuracy = 0
    avg_valid_rate = 0

    avg_duplicated_rate = 0
    avg_syntax_error_rate = 0

    i = 0
    while True:
        result_file = os.path.join(args.base_dir, f'result_{i}.jsonl')
        if not os.path.exists(result_file):
            break

        if not (args.start <= i < args.end):
            i += 1
            continue

        res = read_jsonl_all(result_file)

        i_nums = 0

        i_correct_nums = 0
        i_wrong_nums = 0

        i_valid_nums = 0
        i_invalid_nums = 0

        i_duplicated_nums = 0
        i_syntax_error_nums = 0

        if args.max_nums > 0:
            res = res[ : args.max_nums]

        for r in res:
            if r['correct']:
                i_correct_nums += 1
                i_valid_nums += 1
            elif r['reason'] == 'duplicated':
                i_duplicated_nums += 1
                i_invalid_nums += 1
            elif r['reason'] == 'syntax_invalid':
                i_invalid_nums += 1
                i_syntax_error_nums += 1
            elif r['reason'] == 'no_entry_point':
                i_invalid_nums += 1
                i_syntax_error_nums += 1
            else:
                i_wrong_nums += 1
                i_valid_nums += 1
            i_nums += 1

        i_correct_rate = 0
        if i_valid_nums > 0:
            i_correct_rate = i_correct_nums / i_valid_nums

        i_valid_rate = 0
        i_duplicated_rate = 0
        i_syntax_error_rate = 0
        if i_nums > 0:
            i_valid_rate = i_valid_nums / i_nums
            i_duplicated_rate = i_duplicated_nums / i_nums
            i_syntax_error_rate = i_syntax_error_nums / i_nums


        avg_correct_nums += i_correct_nums
        avg_accuracy += i_correct_rate
        avg_valid_rate += i_valid_rate

        avg_duplicated_rate += i_duplicated_rate
        avg_syntax_error_rate += i_syntax_error_rate
        
        i += 1

    avg_correct_nums = avg_correct_nums / i
    avg_accuracy = round_percentage(avg_accuracy / i)
    avg_valid_rate = round_percentage(avg_valid_rate / i)

    avg_duplicated_rate = round_percentage(avg_duplicated_rate / i)
    avg_syntax_error_rate = round_percentage(avg_syntax_error_rate / i)


    print(f'''\
--- total ---
Valid.: {avg_valid_rate} %
Duplicate.: {avg_duplicated_rate} %
Syntactically Incorrect: {avg_syntax_error_rate} %

--- valid ---
avg_correct_nums: {round(avg_correct_nums, 5)}
avg_accuracy: {avg_accuracy} %

''')


if __name__ == '__main__':
    count()


