from typing import List, Tuple
from code_models import ModelBase
from .designer_agent import DesignerAgent
from .calculator_agent import CalculatorAgent
from .python_inter import PyInterpreter


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
            existing_test_inputs: List[str] = [],
            existing_test_cases: List[str] = [],
            max_tokens: int = 1024,
            generate_temperature: float = 0.2,
            calculate_temperature: float = 0.2,
            tests_count: int = 10,
    ) -> Tuple[List[str], List[str]]:
        if len(existing_test_cases) >= tests_count:
            return existing_test_cases, existing_test_inputs

        designer = DesignerAgent(self.model)

        all_inputs = existing_test_inputs
        gens = 0
        while len(all_inputs) < tests_count:
            if len(all_inputs) == 0:
                all_inputs = designer.generate(
                    function_def=function_def,
                    max_tokens=max_tokens,
                    temperature=generate_temperature
                )
            else:
                all_inputs += designer.generate_additional(
                    function_def=function_def,
                    existing=all_inputs,
                    max_tokens=max_tokens,
                    temperature=generate_temperature
                )

            gens += 1
            if gens >= 10:
                break

        test_inputs = all_inputs[: tests_count]
        test_cases = existing_test_cases

        start_index = len(test_cases)
        inputs_set = {}
        for i in range(0, start_index):
            inputs_set[test_inputs[i]] = test_cases[i]

        py_inter = PyInterpreter()
        calculator = CalculatorAgent(self.model, py_inter)

        for i in range(start_index, tests_count):
            if inputs_set.__contains__(test_inputs[i]):
                test_cases.append(inputs_set[test_inputs[i]])
                continue

            test_case = calculator.generate(
                function_def=function_def,
                input=test_inputs[i],
                prompt_type=prompt_type,
                max_tokens=max_tokens,
                temperature=calculate_temperature
            )

            test_cases.append(test_case)
            inputs_set[test_inputs[i]] = test_case

        py_inter.exit()

        return test_cases, all_inputs

    def generate_wo_reasoning(
            self,
            test_inputs: List[str],
            function_def: str,
            entry_point: str,
            code: str,
    ) -> List[str]:
        """
        Generate directly from the input, generate a code for each test to execute
        """
        calculator = CalculatorAgent(self.model)
        test_cases = []

        inputs_set = {}

        for t in test_inputs:
            if inputs_set.__contains__(t):
                test_cases.append(inputs_set[t])
                continue

            test_case = calculator.generate_directly_from_code(entry_point, t, code)

            test_cases.append(test_case)
            inputs_set[t] = test_case

        return test_cases

    def generate_wo_code(
            self,
            test_inputs: List[str],
            function_def: str,
            entry_point: str
    ) -> List[str]:
        calculator = CalculatorAgent(self.model)
        test_cases = []

        inputs_set = {}

        for t in test_inputs:
            if inputs_set.__contains__(t):
                test_cases.append(inputs_set[t])
                continue

            test_case = calculator.generate_directly_reasoning(function_def, entry_point, t)

            test_cases.append(test_case)
            inputs_set[t] = test_case

        return test_cases

    def generate_wo_code_and_reasoning(
            self,
            test_inputs: List[str],
            function_def: str,
            entry_point: str
    ) -> List[str]:
        calculator = CalculatorAgent(self.model)
        test_cases = []

        inputs_set = {}

        for t in test_inputs:
            if inputs_set.__contains__(t):
                test_cases.append(inputs_set[t])
                continue

            test_case = calculator.generate_directly(function_def, entry_point, t)

            test_cases.append(test_case)
            inputs_set[t] = test_case

        return test_cases
