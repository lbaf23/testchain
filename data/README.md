
## Datasets


The datasets used in the experiment were modified from the following datasets. 

- [HumanEval](https://github.com/openai/human-eval)

- [LeetCode-hard](https://github.com/GammaTauAI/leetcode-hard-gym)


Below is the description of the datasets. 

For the prompt, we've removed the example inputs and outputs but retained `Note` and `Constraints`. 

For the LeetCode-hard dataset, we collect solution from the official [LeetCode website](https://leetcode.com). 

For the HumanEval-cwb dataset, we use the test cases provided in the dataset to verify if the code is correct. 
For the LeetCode-hard dataset, we verify the correctness of the code by submitting it to the official [LeetCode website](https://leetcode.com). 


- HumanEval-wo-examples

We've modified the prompt of the HumanEval dataset.

```json
{
    "index": "The sequence number of the data, starting from 0",
    "task_id": "The ID of the problem",
    "prompt_wo_examples": "The prompt with example test cases removed",
    "prompt": "The original prompt",
    "test_cases": "Test cases for the problem",
    "canonical_solution": "`prompt + canonical_solution` will be the complete solution for the problem",
    "entry_point": "Target function name"
}
```


- LeetCode-hard-wo-examples

We've modified the prompt of the LeetCode-hard dataset and collect the solution. 

```json
{
    "index": "The sequence number of the data, starting from 0",
    "task_id": "The ID of the problem, for example: `minimum-time-to-visit-a-cell-in-a-grid`",
    "prompt_wo_examples": "The prompt with example test cases removed",
    "prompt": "The original prompt",
    "public_test_cases": "Public test cases for the problem",
    "solution": "Complete solution program for the problem, collected from the official LeetCode website",
    "entry_point": "Target function name"
}
```


- HumanEval-cwb

```json
{
    "index": "The sequence number of the data, starting from 0",
    "task_id": "The ID of the problem",
    "code_with_bugs": [
        {
            "code": "Code with bugs",
            "score": "The score of the code on the test cases provided in the dataset"
        },
        "..."
    ]
}
```


- LeetCode-hard-cwb

```json
{
    "index": "The sequence number of the data, starting from 0",
    "task_id": "The ID of the problem",
    "code_with_bugs": [
        {
            "code": "Code with bugs",
            "score": "The score of the code on the official LeetCode website"
        },
        "..."
    ]
}
```


