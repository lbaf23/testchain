from .dataset import CodeDataset
from typing import Dict, List
import json


class LocalDataset(CodeDataset):
    data_range: List[int] = []

    def __init__(self, name: str, dataset_file: str, start: int = 0, end: int = -1, selected_data: List[int] = [],
                 selected: bool = False):
        self.name = name

        self.dataset_file = dataset_file

        self.selected = selected
        self.selected_data = selected_data
        self.data = []
        if selected:
            self.data_range = selected_data
            print(f'-------------------- load dataset {self.dataset_file} [{selected_data}] --------------------')
            i = 0
            with open(self.dataset_file, 'r') as file:
                line = file.readline()
                while line != '':
                    if selected_data.__contains__(i):
                        self.data.append(json.loads(line))
                    i += 1
                    line = file.readline()
            self.start = 0
            self.end = len(self.data)
        else:
            print(f'-------------------- load dataset {self.dataset_file} [{start}, {end}] --------------------')
            self.select_all = end <= 0
            index = 0
            with open(self.dataset_file, 'r') as file:
                line = file.readline()
                while line != '':
                    if self.select_all or start <= index < end:
                        self.data.append(json.loads(line))
                    index += 1
                    line = file.readline()

            if self.select_all:
                self.start = 0
                self.end = index
            else:
                self.start = start
                self.end = end

            self.data_range = [i for i in range(self.start, self.end)]

    def get_data(self, i: int) -> Dict:
        """
        return
            index
            prompt
            entry_point
            solution
            test_cases
        """
        if i < self.start or i >= self.end:
            raise IndexError

        d = self.data[i - self.start]

        if self.name == 'humaneval':
            return {
                'index': i,
                'prompt': d['prompt_wo_examples'],
                'entry_point': d['entry_point'],
                'solution': d['prompt_wo_examples'] + d['canonical_solution'],
                'tests': d['test_cases'],
                'prompt_full': d['prompt']
            }
        elif self.name == 'leetcode-hard':
            return {
                'index': i,
                'prompt': d['prompt_wo_examples'],
                'entry_point': d['entry_point'],
                'solution': d['solution'],
                'tests': d['tests'],
                'prompt_full': d['prompt_full']
            }
        else:
            raise NotImplementedError
