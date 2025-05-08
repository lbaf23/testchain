from utils import read_jsonlines, save_jsonlines, extract_assert_inputs, create_dirs
import os


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, default='humaneval')
    parser.add_argument('--model', type=str, default='gpt4')
    parser.add_argument('--testchain_dir', type=str, default='TestChain_py_inter')
    # parser.add_argument('--result_dir', type=str, default='result/leetcode-hard/gpt4/TestChain_py_inter')
    args = parser.parse_args()

    result_dir = f'result/{args.dataset}/{args.model}/{args.testchain_dir}'
    output_dir = f'{result_dir}_inputs'

    create_dirs(output_dir)

    i = 0
    while True:
        result_file = os.path.join(args.result_dir, f'result_{i}.jsonl')
        if not os.path.exists(result_file):
            break

        content = read_jsonlines(result_file)
        test_inputs = []
        for c in content:
            try:
                input = extract_assert_inputs(c['test_case'])
                input = input[1:-1]
                reason = ''
            except Exception:
                input = ''
                reason = 'syntax_invalid'
            test_inputs.append({
                'index': c['index'],
                'input': input,
                'reason': reason
            })

        output_file = os.path.join(output_dir, f'result_{i}.jsonl')
        save_jsonlines(output_file, test_inputs)
        i += 1
