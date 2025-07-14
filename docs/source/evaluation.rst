Evaluation Framework
===================

The EGen platform includes a comprehensive evaluation framework for benchmarking models and calculating various metrics. This document describes how to use the framework and how to extend it with custom benchmarks and metrics.

Overview
--------

The evaluation framework consists of the following components:

- **Benchmarks**: Tools for running standard benchmarks like MMLU, HellaSWAG, GSM8K, and TruthfulQA
- **Metrics**: Functions for calculating various evaluation metrics for different tasks

Supported Benchmarks
-------------------

The framework supports the following benchmarks:

- **MMLU** (Massive Multitask Language Understanding): Tests the model's knowledge across 57 subjects
- **HellaSWAG**: Tests commonsense reasoning abilities
- **GSM8K**: Tests mathematical reasoning on grade school math problems
- **TruthfulQA**: Tests the model's ability to provide truthful answers
- **Custom**: Allows for custom benchmarks with user-provided datasets

Supported Metrics
----------------

The framework provides the following metrics:

- **Classification Metrics**: Accuracy, Precision, Recall, F1 Score
- **Generation Metrics**: ROUGE, BLEU, BERTScore
- **Language Modeling Metrics**: Perplexity

Using the Framework
------------------

Running Benchmarks
~~~~~~~~~~~~~~~~~

To run a benchmark on a model, use the ``run_benchmark`` function:

.. code-block:: python

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

Running from Command Line
~~~~~~~~~~~~~~~~~~~~~~~~

You can also run benchmarks from the command line using the ``run_benchmarks.py`` script:

.. code-block:: bash

    python scripts/run_benchmarks.py \
        --model_path path/to/model/checkpoint \
        --config_path path/to/model/config.json \
        --benchmark mmlu \
        --batch_size 4 \
        --device cuda

Calculating Metrics
~~~~~~~~~~~~~~~~~

To calculate metrics for a specific task, use the ``calculate_metrics`` function:

.. code-block:: python

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

Extending the Framework
---------------------

Adding New Benchmarks
~~~~~~~~~~~~~~~~~~~

To add a new benchmark:

1. Add a new value to the ``BenchmarkType`` enum in ``benchmarks.py``
2. Create a new dataset class that inherits from ``BenchmarkDataset``
3. Implement the required methods: ``_load_data``, ``get_prompt``, and ``evaluate_response``
4. Update the ``get_benchmark_dataset`` function to return your new dataset class

Here's an example of adding a new benchmark:

.. code-block:: python

    class CustomBenchmarkDataset(BenchmarkDataset):
        """Custom benchmark dataset."""
        
        def _load_data(self) -> List[Dict]:
            """Load custom data from file."""
            examples = []
            
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for item in data:
                examples.append({
                    "input": item["input"],
                    "output": item["output"],
                })
            
            return examples
        
        def get_prompt(self, example: Dict) -> str:
            """Get the prompt for a custom example."""
            return f"Input: {example['input']}\n\nOutput:"
        
        def evaluate_response(self, example: Dict, response: str) -> float:
            """Evaluate the model's response for a custom example."""
            # Implement your evaluation logic here
            return 1.0 if response.strip() == example["output"].strip() else 0.0

    # Update get_benchmark_dataset function
    def get_benchmark_dataset(benchmark_type: BenchmarkType, data_path: str) -> BenchmarkDataset:
        if benchmark_type == BenchmarkType.MMLU:
            return MMLUDataset(data_path)
        elif benchmark_type == BenchmarkType.CUSTOM:
            return CustomBenchmarkDataset(data_path)
        # ...

Adding New Metrics
~~~~~~~~~~~~~~~~

To add a new metric:

1. Add a new function in ``metrics.py`` that calculates your metric
2. Update the ``calculate_metrics`` function to include your new metric when appropriate

Here's an example of adding a new metric:

.. code-block:: python

    def calculate_meteor_score(predictions: List[str], references: List[str]) -> float:
        """Calculate METEOR score for generated text."""
        try:
            from nltk.translate.meteor_score import meteor_score
            import nltk
            
            # Download NLTK data if needed
            try:
                nltk.data.find("wordnet")
            except LookupError:
                nltk.download("wordnet")
            
            # Calculate METEOR score
            scores = []
            for pred, ref in zip(predictions, references):
                score = meteor_score([ref.split()], pred.split())
                scores.append(score)
            
            return float(np.mean(scores))
        except ImportError:
            print("Warning: nltk package not installed. Skipping METEOR metric.")
            return 0.0

    # Update calculate_generation_metrics function
    def calculate_generation_metrics(
        predictions: List[str],
        references: List[str],
        use_rouge: bool = True,
        use_bleu: bool = True,
        use_bertscore: bool = False,
        use_meteor: bool = False,  # Add new parameter
    ) -> Dict[str, float]:
        metrics = {}
        
        # ... existing code ...
        
        if use_meteor:
            meteor = calculate_meteor_score(predictions, references)
            metrics["meteor"] = meteor
        
        return metrics