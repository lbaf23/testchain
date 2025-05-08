from argparse import ArgumentParser
from utils import read_jsonlines
import os
import json
from typing import List


def load_codes(code_file: str) -> List[str]:
    codes = []
    with open(code_file, 'r') as file:
        line = file.readline()
        while line != '':
            d = json.loads(line)
            codes.append(d['code'])
            line = file.readline()
    return codes


def round_percentage(f: float, l: int = 2):
    return round(f * 100, l)


def count():
    parser = ArgumentParser()
    parser.add_argument('--base_dir', type=str)
    parser.add_argument('--max_nums', type=int, default=10)

    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=164)

    parser.add_argument('--detail', action='store_true')
    args = parser.parse_args()

    total_problems = 0
    total_tests_nums = 0

    # correct
    total_correct_nums = 0

    # correct / total
    avg_accuracy = 0.0

    # correct / val
    avg_val_accuracy = 0.0

    # valid
    total_val_nums = 0
    avg_val_rate = 0.0

    # duplicate
    total_dup_nums = 0
    avg_dup_rate = 0.0

    # syntax invalid
    total_syn_nums = 0
    avg_syn_rate = 0.0

    # input output mismatch
    total_mis_match_nums = 0
    avg_mis_match_rate = 0

    # other error, such as timeout error
    total_oth_nums = 0
    avg_oth_rate = 0.0

    for i in range(args.start, args.end):
        result_file = os.path.join(args.base_dir, f'result_{i}.jsonl')
        assert os.path.exists(result_file), f'{result_file} not found.'

        res = read_jsonlines(result_file)
        if args.max_nums > 0:
            res = res[: args.max_nums]

        i_tests_nums = 0

        i_correct_nums = 0
        i_val_nums = 0
        i_dup_nums = 0
        i_syn_nums = 0
        i_mis_match_nums = 0
        i_oth_nums = 0

        for r in res:
            if r['correct']:
                i_correct_nums += 1
                i_val_nums += 1
            elif r['reason'] == 'duplicated':
                i_dup_nums += 1
            elif r['reason'] == 'syntax_invalid' or r['reason'] == 'no_entry_point':
                i_syn_nums += 1
            elif r['reason'] == 'assertion_error':
                i_mis_match_nums += 1
                i_val_nums += 1
            else:
                i_oth_nums += 1
                i_val_nums += 1
            i_tests_nums += 1

        i_accuracy = i_correct_nums / i_tests_nums if i_tests_nums > 0 else 0
        i_val_accuracy = i_correct_nums / i_val_nums if i_val_nums > 0 else 0

        i_val_rate = i_val_nums / i_tests_nums if i_tests_nums > 0 else 0
        i_dup_rate = i_dup_nums / i_tests_nums if i_tests_nums > 0 else 0
        i_syn_rate = i_syn_nums / i_tests_nums if i_tests_nums > 0 else 0
        i_mis_match_rate = i_mis_match_nums / i_tests_nums if i_tests_nums > 0 else 0
        i_oth_rate = i_oth_nums / i_tests_nums if i_tests_nums > 0 else 0

        avg_accuracy += i_accuracy
        avg_val_accuracy += i_val_accuracy

        avg_dup_rate += i_dup_rate
        avg_syn_rate += i_syn_rate
        avg_val_rate += i_val_rate
        avg_mis_match_rate += i_mis_match_rate
        avg_oth_rate += i_oth_rate

        total_problems += 1

        total_tests_nums += i_tests_nums

        total_dup_nums += i_dup_nums
        total_syn_nums += i_syn_nums
        total_correct_nums += i_correct_nums
        total_mis_match_nums += i_mis_match_nums
        total_oth_nums += i_oth_nums

        total_val_nums += i_val_nums

    avg_correct_nums = total_correct_nums / total_problems

    acc = round_percentage(total_correct_nums / total_tests_nums)
    dup = round_percentage(total_dup_nums / total_tests_nums)
    syn = round_percentage(total_syn_nums / total_tests_nums)
    mis = round_percentage(total_mis_match_nums / total_tests_nums)
    oth = round_percentage(total_oth_nums / total_tests_nums)

    print(f'''\

=== Total ===
tests: {total_tests_nums}

Acc: {acc} %, #Total Corr: {total_correct_nums}
Dup: {dup} %, #Total Dup: {total_dup_nums}
Syn: {syn} %, #Total Syn: {total_syn_nums}
Mis: {mis} %, #Total Mis: {total_mis_match_nums}
Oth: {oth} %, #Total Oth: {total_oth_nums}

#(Avg) Corr: {avg_correct_nums}
''')


if __name__ == '__main__':
    count()
