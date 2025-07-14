# EGen Evaluation Framework

This directory contains the evaluation and benchmarking framework for the EGen platform. The framework provides tools for evaluating model performance on standard benchmarks and calculating various metrics.

## Overview

The evaluation framework consists of the following components:

- **Benchmarks**: Tools for running standard benchmarks like MMLU, HellaSWAG, GSM8K, and TruthfulQA
- **Metrics**: Functions for calculating various evaluation metrics for different tasks

## Benchmarks

The framework supports the following benchmarks:

- **MMLU** (Massive Multitask Language Understanding): Tests the model's knowledge across 57 subjects
- **HellaSWAG**: Tests commonsense reasoning abilities
- **GSM8K**: Tests mathematical reasoning on grade school math problems
- **TruthfulQA**: Tests the model's ability to provide truthful answers
- **Custom**: Allows for custom benchmarks with user-provided datasets

## Metrics

The framework provides the following metrics:

- **Classification Metrics**: Accuracy, Precision, Recall, F1 Score
- **Generation Metrics**: ROUGE, BLEU, BERTScore
- **Language Modeling Metrics**: Perplexity

## Usage

### Running Benchmarks

To run a benchmark on a model, use the `run_benchmark` function:

```python
from egen.evaluation import run_benchmark, BenchmarkType
from egen.model import THL150

# Load your model
model = THL150.from_pretrained("path/to/model")

# Run MMLU benchmark
results = run_benchmark(
    model=model,
    benchmark_type=BenchmarkType.MMLU,
    batch_size=4,
    device="cuda",
)

print(f"Overall accuracy: {results['overall_accuracy']}")
```

### Running from Command Line

You can also run benchmarks from the command line using the `run_benchmarks.py` script:

```bash
python scripts/run_benchmarks.py \
    --model_path path/to/model/checkpoint \
    --config_path path/to/model/config.json \
    --benchmark mmlu \
    --batch_size 4 \
    --device cuda
```

### Calculating Metrics

To calculate metrics for a specific task, use the `calculate_metrics` function:

```python
from egen.evaluation import calculate_metrics

# For classification tasks
metrics = calculate_metrics(
    loss=loss_value,
    predictions=[0, 1, 0, 1],
    labels=[0, 1, 1, 0],
    task_type="classification",
)

# For generation tasks
metrics = calculate_metrics(
    predictions=["Generated text 1", "Generated text 2"],
    labels=["Reference text 1", "Reference text 2"],
    task_type="generation",
    use_rouge=True,
    use_bleu=True,
)
```

## Extending the Framework

### Adding New Benchmarks

To add a new benchmark:

1. Add a new value to the `BenchmarkType` enum in `benchmarks.py`
2. Create a new dataset class that inherits from `BenchmarkDataset`
3. Implement the required methods: `_load_data`, `get_prompt`, and `evaluate_response`
4. Update the `get_benchmark_dataset` function to return your new dataset class

### Adding New Metrics

To add a new metric:

1. Add a new function in `metrics.py` that calculates your metric
2. Update the `calculate_metrics` function to include your new metric when appropriate