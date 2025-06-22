import deepeval
import pytest
from deepeval.test_case.llm_test_case import LLMTestCase
from deepeval.dataset.dataset import EvaluationDataset
from deepeval.dataset.golden import Golden
from deepeval.metrics.answer_relevancy.answer_relevancy import AnswerRelevancyMetric
from deepeval import evaluate
from recipe_agent import suggest_dish

dataset = EvaluationDataset()
dataset.pull(alias="RecipeDataset")
print("Dataset is pulled successfully")
#print(dataset.goldens) 

metric = AnswerRelevancyMetric()

print("Dataset is being prepared...")
test_cases = []
for golden in dataset.goldens:
    input = golden.input
    try:
        output = suggest_dish(golden.input)
        #print(f"Input: {input}, Output: {output}")
        test_case = LLMTestCase(input=input, actual_output=output, expected_output=golden.expected_output)
        #test_case = LLMTestCase(input=input, actual_output=output)
        #print(test_case)
        test_cases.append(test_case)
    except Exception as e:
        print(f"Error processing golden input: {input}, Error: {e}")

print("Dataset preparation completed.")
print(f"Total test cases prepared: {len(test_cases)}")
print(test_cases[0])  # Print the first test case for verification
