import numpy as np
import pandas as pd
import scipy
from scipy import stats
from scipy.special import factorial

import os
import pickle
from datetime import datetime
import tabulate
import wandb
from collections import namedtuple


API = wandb.Api()


DATASET_CORESET_SIZE = 22500
ACCURACY_THRESHOLD = 0.95
TASK_ACC_COLS = [f'Test Accuracy, Query #{i}' for i in range(1, 11)]


QUERY_NAMES = ['blue', 'brown', 'cyan', 'gray', 'green', 
               'orange', 'pink', 'purple', 'red', 'yellow', 
               'cone', 'cube', 'cylinder', 'dodecahedron', 'ellipsoid',
               'octahedron', 'pyramid', 'rectangle', 'sphere', 'torus', 
               'chain_mail', 'marble', 'maze', 'metal', 'metal_weave',
               'polka', 'rubber', 'rug', 'tiles', 'wood_plank']

COLOR = 'color'
COLOR_INDEX = 0
SHAPE = 'shape'
SHAPE_INDEX = 1
TEXTURE = 'texture'
TEXTURE_INDEX = 2
COMBINED = 'combined'
COMBINED_INDEX = 3
DIMENSION_NAMES = [COLOR, SHAPE, TEXTURE]

RESULT_SET_FIELDS = ['name', 'mean', 'std']
ANALYSIS_SET_FIELDS = ['examples', 'log_examples', 'accuracies', 'accuracy_drops', 'examples_by_task']
CONDITION_ANALYSES_FIELDS = DIMENSION_NAMES + [COMBINED]

ResultSet = namedtuple('ResultSet', RESULT_SET_FIELDS)
AnalysisSet = namedtuple('AnalysisSet', ANALYSIS_SET_FIELDS)
ConditionAnalysesSet = namedtuple('ConditionAnalysesSet', CONDITION_ANALYSES_FIELDS)

NAMED_TUPLE_CLASSES = (ResultSet, AnalysisSet, ConditionAnalysesSet)
for NamedTupleClass in NAMED_TUPLE_CLASSES:
    NamedTupleClass.__new__.__defaults__ = (None,) * len(NamedTupleClass._fields)


RESULT_SET_NAMES = ('Examples to criterion', 'Log examples to criterion', 
                    'New task accuracy', 'New task accuracy delta')
ANALYSIS_FIELDS_TO_NAMES = {field: name for (name, field) in 
                            zip(ANALYSIS_SET_FIELDS, RESULT_SET_NAMES)}
ANALYSIS_NAMES_TO_FIELDS = {name: field for (name, field) in 
                            zip(ANALYSIS_SET_FIELDS, RESULT_SET_NAMES)}


CACHE_PATH = './analyses_caches/meta_learning_analyses_cache.pickle'
BACKUP_CACHE_PATH = './analyses_caches/meta_learning_analyses_cache_{date}.pickle'


def refresh_cache(new_values_dict=None, cache_path=CACHE_PATH):
    if new_values_dict is None:
        new_values_dict = {}
    
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as cache_file:
            cache = pickle.load(cache_file)
    
    else:
        cache = {}
    
    cache.update(new_values_dict)
    
    if os.path.exists(cache_path):
        os.rename(CACHE_PATH, BACKUP_CACHE_PATH.format(date=datetime.now().strftime('%Y-%m-%d_%H-%M-%S')))

    with open(cache_path, 'wb') as cache_file:
        pickle.dump(cache, cache_file)

    return cache
    

def examples_per_epoch(task, latest_task):
    if task == latest_task:
        return 22500
    
    return 22500 // (latest_task - 1)
            

def parse_run_results(current_run_id=None, current_run=None, samples=1000):
    if current_run_id is None and current_run is None:
        print('Must provide either a current run or its id')
        return
    
    if current_run is None:
        current_run = API.run(f'meta-learning-scaling/sequential-benchmark-baseline/{current_run_id}')
        
    current_df = current_run.history(pandas=True, samples=samples)
    
    examples_to_criterion = np.empty((10, 10))
    examples_to_criterion.fill(np.nan)
    absolute_accuracy = np.empty((9, 9))
    absolute_accuracy.fill(np.nan)
    accuracy_drop = np.empty((9, 9))
    accuracy_drop.fill(np.nan)
    
    first_task_finished = current_df['Test Accuracy, Query #2'].first_valid_index() - 1
    examples_to_criterion[0, 0] = first_task_finished * examples_per_epoch(1, 1)
    absolute_accuracy[0, 0] = current_df['Test Accuracy, Query #1'][first_task_finished + 1]
    accuracy_drop[0, 0] = current_df['Test Accuracy, Query #1'][first_task_finished] - absolute_accuracy[0, 0]

    for current_task in range(2, 11):
        current_task_start = current_df[f'Test Accuracy, Query #{current_task}'].first_valid_index()

        if current_task == 10:
            current_task_end = current_df.shape[0]
        else:
            current_task_end = current_df[f'Test Accuracy, Query #{current_task + 1}'].first_valid_index()

        current_task_subset = current_df[TASK_ACC_COLS][current_task_start:current_task_end] > 0.95

        for task in range(1, current_task + 1):
            number_times_learned = current_task - task + 1
            number_total_tasks = current_task

            examples_to_criterion[number_times_learned - 1, number_total_tasks - 1] = examples_per_epoch(task, current_task) * \
                (current_task_subset[f'Test Accuracy, Query #{task}'].idxmax() - current_task_start + 1)
            
            if current_task < 10:
                absolute_accuracy[number_times_learned - 1, number_total_tasks - 1] = \
                    current_df[f'Test Accuracy, Query #{task}'][current_task_end]
                accuracy_drop[number_times_learned - 1, number_total_tasks - 1] = \
                    current_df[f'Test Accuracy, Query #{task}'][current_task_end - 1] - \
                    absolute_accuracy[number_times_learned - 1, number_total_tasks - 1]
            
    return examples_to_criterion, absolute_accuracy, accuracy_drop


PRINT_HEADERS = ['###'] + [str(x) for x in range(1, 11)]


def pretty_print_results(results, **kwargs):
    result_rows = [[str(i + 1)] + list(results[i]) for i in range(len(results))]
    tab_args = dict(tablefmt='fancy_grid')
    tab_args.update(kwargs)
    print(tabulate.tabulate(result_rows, PRINT_HEADERS, **tab_args))


def runs_by_dimension(max_rep_id):
    runs = API.runs('meta-learning-scaling/sequential-benchmark-baseline')
    
    results = ConditionAnalysesSet([], [], [], [])
    
    for run in runs:
        run_id = int(run.description.split('\n')[0][-4:])
        dimension = (run_id // 1000) - 1
        rep = run_id % 1000
        if rep < max_rep_id:
            results[dimension].append(run)
            # combined / all runs
            results[3].append(run)
            
    return results


def query_modulated_runs_by_dimension(max_rep_id):
    runs = API.runs('meta-learning-scaling/sequential-benchmark-task-modulated')
    
    results = {level: ConditionAnalysesSet([], [], [], []) for level in range(1, 5)}
    
    for run in runs:
        level, run_id = [int(x) for x in run.description.split('\n')[0][-6:].split('-')]
        dimension = (run_id // 1000) - 1
        rep = run_id % 1000
        if rep < max_rep_id:
            results[level][dimension].append(run)
            # combined / all runs
            results[level][3].append(run)
            
    return results


def process_multiple_runs(runs, debug=False, ignore_runs=None, samples=1000):
    examples = []
    log_examples = []
    abs_accuracies = []
    accuracy_drops = []
    
    examples_by_task = np.zeros((30, 10))
    counts_by_task = np.zeros((30, 10))
    
    for run in runs:
        print(run.name)
        if ignore_runs is not None and run.name in ignore_runs:
            continue
        
        examples_to_criterion, absolute_accuracy, accuracy_drop = parse_run_results(current_run=run, samples=samples)
        examples.append(examples_to_criterion)
        log_examples.append(np.log(examples_to_criterion))
        abs_accuracies.append(absolute_accuracy)
        accuracy_drops.append(accuracy_drop)
        
        for index, task in enumerate(run.config['query_order']):
            task_examples = np.diag(examples_to_criterion, index)
            examples_by_task[task,:10 - index] += task_examples
            counts_by_task[task,:10 - index] += 1

    output = {}
    for result_set, name, field in zip((examples, log_examples, abs_accuracies, accuracy_drops), 
                                RESULT_SET_NAMES, ANALYSIS_SET_FIELDS):
        output[field] = ResultSet(name=name, 
                                  mean=np.mean(result_set, axis=0), 
                                  std=np.std(result_set, axis=0))

    # to avoid division by zero
    counts_by_task[counts_by_task == 0] = 1
    average_examples_by_task = np.divide(examples_by_task, counts_by_task)
    output['examples_by_task'] = average_examples_by_task
    
    analysis = AnalysisSet(**output)
        
    if debug:
        return analysis, examples
    
    return analysis
