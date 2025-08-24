from enum import Enum, auto

from benchmark import RecentlyAddedExample, CounterFactualExample
from testcase import TestCase
from prompt_provider import PromptManager

class TestResult(Enum):
    NOT_EXECUTED = auto()
    PASSED = auto()
    FAILED = auto()


class ExampleResult(Enum):
    EXECUTED = auto()
    EDIT_FAILED = auto()
    NEW_FACT_KNOWN = auto()
    PREV_FACT_UNKNOWN = auto()


class TestRunner:

    # hardcode it here so I don't have to add to to all ancestor params while I test
    def __init__(self, query_executor, model_editor, graph: bool = False):
        self._query_executor = query_executor
        self._model_editor = model_editor
        self._prompt_manager = PromptManager("../data/prompts.yaml")
        self._graph = graph

    def run_testcases(self, example, test_cases, skip_edit=False, skip_restore=True, skip_preconditions=False):
        example_result = ExampleResult.EXECUTED
        test_results = {TestResult.NOT_EXECUTED: [], TestResult.PASSED: [], TestResult.FAILED: []}

        # Check testcase conditions
        if not skip_preconditions:
            for test_case in test_cases:
                for condition_query in test_case.get_condition_queries():
                    print('Executing condition query')
                    if not self._query_executor.execute_query(condition_query):
                        test_results[TestResult.NOT_EXECUTED].append(test_case)
                        break

        # Check if fact is known/unknown according to example type
        # Modified logic to do a simpler check for graphs using text-based prompts
        # TODO: test if this is necessary, as the answers seem fine
        if self._graph:
            if isinstance(example, RecentlyAddedExample):
                fact_prompt = self._prompt_manager.render_prompt("fact-known", fact=example.fact.get_fact_prompt())
                print('Executing fact check query')
                if self._query_executor._get_response(fact_prompt).equals("Yes"):
                    example_result = ExampleResult.NEW_FACT_KNOWN
            elif isinstance(example, CounterFactualExample):
                fact_prompt = self._prompt_manager.render_prompt("fact-unknown", fact=example.previous_fact.get_fact_prompt())
                print('Executing fact check query')
                if self._query_executor._get_response(fact_prompt).equals("No"):
                    example_result = ExampleResult.PREV_FACT_UNKNOWN
        else:
            if isinstance(example, RecentlyAddedExample):
                print('Executing fact check query')
                if self._query_executor.execute_query(example.fact.get_fact_query()):
                    example_result = ExampleResult.NEW_FACT_KNOWN
            elif isinstance(example, CounterFactualExample):
                print('Executing fact check query')
                if not self._query_executor.execute_query(example.previous_fact.get_fact_query()):
                    example_result = ExampleResult.PREV_FACT_UNKNOWN

        if self._model_editor is None:
            return example_result, test_results

        # Modify model
        if not skip_edit:
            self._model_editor.edit_model(example.fact)

        # Test edit
        if self._graph:
            fact_prompt = self._prompt_manager.render_prompt("fact-known", fact=example.fact.get_fact_prompt())
            print('Executing fact check query')
            if self._query_executor._get_response(fact_prompt).equals("Yes"):
                example_result = ExampleResult.NEW_FACT_KNOWN
        else:
            if not self._query_executor.execute_query(example.fact.get_fact_query()):
                example_result = ExampleResult.EDIT_FAILED

        # Test modified model
        for test_case in test_cases:
            if test_case not in test_results[TestResult.NOT_EXECUTED]:
                test_case_results = []
                for test_query in test_case.get_test_queries():
                    print('Executing test query')
                    test_case_results.append(self._query_executor.execute_query(test_query))
                if test_case.get_test_condition() == TestCase.OR_TEST_CONDITION and True in test_case_results:
                    test_results[TestResult.PASSED].append(test_case)
                elif test_case.get_test_condition() == TestCase.AND_TEST_CONDITION and False not in test_case_results:
                    test_results[TestResult.PASSED].append(test_case)
                else:
                    test_results[TestResult.FAILED].append(test_case)


        #TODO: extend model_editor restore model for graph
        # Restore model
        if not skip_restore:
            self._model_editor.restore_model()

        return example_result, test_results
