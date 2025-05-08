from typing import List
from transformers import AutoTokenizer, AutoModelForCausalLM, StoppingCriteriaList
import torch
from .models import ModelBase
from .utils import rstrip_str, CodeStoppingCriteria


class CodeGen(ModelBase):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            padding_side='left'
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        self.tokenizer.pad_token = self.tokenizer.eos_token
        super().__init__('codegen')

    def generate(self, prompt: str, max_tokens: int = 1024, stop_strs: List[str] = [], temperature: float = 0.2) -> str:
        stop_ids = [self.tokenizer(i, add_special_tokens=False).input_ids for i in stop_strs]
        stop_criteria = CodeStoppingCriteria(stop_ids)

        input_ids = self.tokenizer(prompt, return_tensors='pt').to(self.model.device).input_ids
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=input_ids,
                do_sample=True,
                top_p=0.95,
                temperature=temperature,
                max_length=max_tokens,
                pad_token_id=self.tokenizer.eos_token_id,
                stopping_criteria=StoppingCriteriaList([stop_criteria])
            )
            code = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        return rstrip_str(code, stop_strs)
