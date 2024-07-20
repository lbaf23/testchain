from typing import List
from transformers import StoppingCriteria
import torch


def rstrip_code(code: str, stop_strs: List = []) -> str:
    if stop_strs is None or len(stop_strs) == 0:
        return code
    
    for token in stop_strs:
        if code.endswith(token):
            code = code.rstrip(token)
    return code.strip()


class CodeStoppingCriteria(StoppingCriteria):       
    def __init__(self, stop_ids: List[List]):
        self.stop_ids = stop_ids
    
    def endswith(self, input_id):
        for ids in self.stop_ids:
            l = len(ids)
            if len(input_id) >= l and list(input_id[-l:].detach().cpu().numpy()) == ids:
                return True
        return False

    def __call__(self, input_ids: torch.LongTensor, score: torch.FloatTensor, **kwargs):
        if self.endswith(input_ids[0]):
            return True
        return False
