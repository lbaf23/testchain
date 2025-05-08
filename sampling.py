from code_generator import CodeGenerator
from typing import Dict
from utils import read_jsonlines, append_jsonlines
from tqdm import tqdm
import argparse


def Sampling(
        index: int,
        code_generator: CodeGenerator,
        data: Dict,
        result_file: str,
        log_file: str,
        run_config: Dict,
) -> None:
    sampling_nums = run_config['sampling_nums']

    prompt = data['prompt']

    r = 0

    # load result
    result = read_jsonlines(result_file)
    if len(result) > 0:
        r = result[-1]['r'] + 1
    else:
        create_or_clear_file(log_file)
        create_or_clear_file(result_file)

    td = tqdm(initial=r, total=sampling_nums)
    td.set_description(f'''[{index}]''')

    # repair
    while r < sampling_nums:
        code = code_generator.generate(prompt)
        item = {'r': r, 'code': code}

        append_jsonlines(result_file, item)
        td.update(1)
        r += 1


from utils import load_config, config_log, create_dirs, create_or_clear_file
from code_models import model_factory
from code_datasets import LocalDataset
import os


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='config/leetcode-hard/config-gpt4o-code.json')
    parser.add_argument('--run_type', type=str, default='sampling')
    parser.add_argument('--api_key', type=str, default='')
    parser.add_argument('--base_url', type=str, default='')

    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=-1)

    parser.add_argument('--rerun', action='store_true')
    args = parser.parse_args()
    config = load_config(args.config)
    print(config, flush=True)

    extra_args = {}
    if args.api_key != '':
        extra_args['api_key'] = args.api_key
    if args.base_url != '':
        extra_args['base_url'] = args.base_url
    model = model_factory(**config['model'], **extra_args)
    code_generator = CodeGenerator(model)
    dataset = LocalDataset(**config['dataset'])

    result_dir = os.path.join(config['result_dir'], args.run_type)
    log_dir = os.path.join(config['log_dir'], args.run_type)

    create_dirs(result_dir)
    create_dirs(log_dir)

    for i in dataset.data_range:
        if args.start < args.end and not args.start <= i < args.end:
            continue

        data = dataset.get_data(i)

        # create files
        log_file = os.path.join(log_dir, f'log_{i}.log')
        result_file = os.path.join(result_dir, f'result_{i}.jsonl')
        config_log(log_file)

        run_config = config[args.run_type]
        Sampling(
            index=i,
            code_generator=code_generator,
            data=data,
            result_file=result_file,
            log_file=log_file,
            run_config=run_config,
        )
