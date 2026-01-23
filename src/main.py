from collections import defaultdict

from evaluation import Evaluator
from modeleditor import GraphEditor
from queryexecutor import SingularityNetExecutor
from benchmark import Dataset, TestsAxis
from wikidata.utils import write_json
import requests
import json

fake_facts_path = '../data/benchmark/random.json'
popular_path = '../data/benchmark/popular.json'

# Add this configuration flag to control whether to use human-readable labels or IDs
# Useful because that's what the system actually responds with, otherwise tests fail
USE_LABELS = True  # Set to True to use human-readable labels, False for IDs

datasets = [
    fake_facts_path,
    popular_path
]


# load it into the graphRAG system, takes a while so normally do it in a diff file or use a wait function
base_url = 'http://0.0.0:8000'
db_name = 'test'
#TODO: mine the triplets 
for dataset_path in datasets:
    if dataset_path == fake_facts_path:
        dataset_name = 'fake_facts'
    if dataset_path == popular_path:
        dataset_name = 'popular'
    
    experiment_name = f'graph_{dataset_name}'
    print(experiment_name)

    graph_query_executor = SingularityNetExecutor(base_url=base_url, db_name=db_name)
    graph_editor = GraphEditor(query_executor=graph_query_executor)
    evaluator = Evaluator(query_executor=graph_query_executor, model_editor=graph_editor)
    dataset = Dataset.from_file(dataset_path, use_labels=USE_LABELS)

    precisions_json = dict()
    num_of_examples = 200

    examples_for_eval = dataset.sample(num_of_examples)
    eval_size = len(examples_for_eval)

    #lambda makes bad defaultdict keys return 0 as value
    succeeded_edits = defaultdict(lambda: 0)
    average_precision = defaultdict(lambda: 0)
    average_executed = defaultdict(lambda: 0)
    average_size = defaultdict(lambda: 0)
    total_checked_examples = defaultdict(lambda: 0)
    executed_portion_dict = defaultdict(lambda: 0)

    #manually update statistics
    for i, example in enumerate(examples_for_eval):
        if (i + 1) % 10 == 0:
            print(f'{i + 1}/{eval_size}')

        if example.fact.get_subject_label() == '' or example.fact.get_target_label() == '':
            print(f'Skipping example: {example.to_dict()}')
            continue

        evaluation_results = evaluator.evaluate(example)

        res_dict_for_json = dict()
        for axis, results in evaluation_results.items():
            precision, executed, size, edit_succeeded = results
            if executed == 0.0:
                continue
            if edit_succeeded:
                succeeded_edits[axis] += 1
                average_precision[axis] += precision
                res_dict_for_json[axis.name] = precision
                average_executed[axis] += executed
                average_size[axis] += size
            total_checked_examples[axis] += 1

        precisions_json[str(example.fact)] = res_dict_for_json

        for axis in TestsAxis:
            if axis in evaluation_results:
                executed_portion_dict[axis] += evaluation_results[axis][1]


    #print results
    res_str = ''
    for axis in TestsAxis:
        print(f'Results of axis {axis}:')
        res_str += f'Results of axis {axis}:\n'

        if total_checked_examples[axis] == 0:
            print(f'No checked tests for this axis')
            res_str += f'No checked tests for this axis\n'
            continue

        average_precision[axis] /= succeeded_edits[axis]
        average_executed[axis] /= succeeded_edits[axis]
        average_size[axis] /= succeeded_edits[axis]

        print(f'{(succeeded_edits[axis] / eval_size) * 100} successful edits (out of {eval_size})')
        res_str += f'{(succeeded_edits[axis] / eval_size) * 100} successful edits (out of {eval_size})\n'
        print(f'Average accuracy is {average_precision[axis]}')
        res_str += f'Average accuracy is {average_precision[axis]}\n'
        print(f'Average portion of executed_tests is {average_executed[axis]}')
        res_str += f'Average portion of executed_tests is {average_executed[axis]}\n'
        print(f'Average total number of tests is {average_size[axis]}')
        res_str += f'Average total number of tests is {average_size[axis]}\n'

    write_json(precisions_json, f'./{experiment_name}_res_2.json')

    with open(f'./{experiment_name}_2.txt', 'w+', encoding='utf-8') as f:
        f.write(res_str)
