from typing import List, Tuple
from code_models import ModelBase
from .designer_agent import DesignerAgent
from .calculator_agent import CalculatorAgent


class TestChain:
    def __init__(
            self,
            model: ModelBase,
    ) -> None:
        self.model = model

    def generate(
            self,
            function_def: str,
            prompt_type: str,
            max_tokens: int = 512
    ) -> List[str]:
        designer = DesignerAgent(self.model)
        calculator = CalculatorAgent(self.model)

        inputs = designer.generate(
            function_def=function_def,
            max_tokens=int(max_tokens / 2)  # Since this method only requires generating test inputs and does not need to generate test outputs, to ensure fairness, we set the model's output token count to half that of other methods
        )
        test_cases = []

        inputs_set = {}

        for i in inputs:
            if inputs_set.__contains__(i):
                test_cases.append(inputs_set[i])
                continue

            test_case = calculator.generate(
                function_def=function_def,
                input=i,
                prompt_type=prompt_type,
                max_tokens=max_tokens
            )

            if test_case != '':
                test_cases.append(test_case)
            
            inputs_set[i] = test_case

        return test_cases
