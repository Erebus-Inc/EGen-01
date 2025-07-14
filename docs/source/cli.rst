Command-Line Interface
====================

Overview
--------

The EGen platform provides a command-line interface (CLI) for interacting with the model, running self-healing operations, and managing the platform.

Usage
-----

.. code-block:: bash

    python -m egen.cli [command] [options]

Commands
--------

Model Commands
~~~~~~~~~~~~

.. code-block:: bash

    python -m egen.cli model [load|inference|prompt]

**load**

Load a THL-150 model from a specified path or download it from Hugging Face Hub.

.. code-block:: bash

    python -m egen.cli model load --path /path/to/model
    python -m egen.cli model load --hub-id ErebusTN/THL-150

Options:

- `--path`: Local path to model weights
- `--hub-id`: Hugging Face Hub model ID
- `--revision`: Specific model revision to load (default: main)
- `--cache-dir`: Directory to store downloaded models

**inference**

Run inference using a loaded model.

.. code-block:: bash

    python -m egen.cli model inference --input "def fibonacci(n):"

Options:

- `--input`: Input text for inference
- `--input-file`: Path to file containing input text
- `--output-file`: Path to save output (default: stdout)
- `--max-length`: Maximum generation length (default: 100)
- `--temperature`: Sampling temperature (default: 0.7)
- `--domain`: Specific domain to use (code, math, security, general)

**prompt**

Start an interactive prompt session with the model.

.. code-block:: bash

    python -m egen.cli model prompt

Options:

- `--max-length`: Maximum generation length (default: 100)
- `--temperature`: Sampling temperature (default: 0.7)
- `--domain`: Specific domain to use (code, math, security, general)
- `--history-file`: Path to save conversation history

Self-Healing Commands
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    python -m egen.cli self-healing [monitor|repair]

**monitor**

Start the self-healing monitoring system.

.. code-block:: bash

    python -m egen.cli self-healing monitor

Options:

- `--interval`: Monitoring interval in seconds (default: 60)
- `--log-file`: Path to log file (default: logs/monitor.log)
- `--config`: Path to monitoring configuration file

**repair**

Run the self-healing repair system.

.. code-block:: bash

    python -m egen.cli self-healing repair

Options:

- `--issue-id`: Specific issue ID to repair
- `--dry-run`: Show repair plan without executing
- `--log-file`: Path to log file (default: logs/repair.log)
- `--config`: Path to repair configuration file

Self-Optimization Commands
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    python -m egen.cli self-optimization [hyperparameter|nas|pruning|quantization]

**hyperparameter**

Run hyperparameter optimization.

.. code-block:: bash

    python -m egen.cli self-optimization hyperparameter

Options:

- `--dataset`: Path to dataset
- `--trials`: Number of optimization trials (default: 10)
- `--output`: Path to save optimized parameters
- `--config`: Path to optimization configuration file

**nas**

Run neural architecture search.

.. code-block:: bash

    python -m egen.cli self-optimization nas

Options:

- `--dataset`: Path to dataset
- `--search-space`: Path to search space configuration
- `--trials`: Number of search trials (default: 10)
- `--output`: Path to save discovered architecture

**pruning**

Run model pruning.

.. code-block:: bash

    python -m egen.cli self-optimization pruning

Options:

- `--model-path`: Path to model
- `--dataset`: Path to dataset
- `--target-sparsity`: Target sparsity ratio (default: 0.5)
- `--output`: Path to save pruned model

**quantization**

Run model quantization.

.. code-block:: bash

    python -m egen.cli self-optimization quantization

Options:

- `--model-path`: Path to model
- `--dataset`: Path to dataset
- `--precision`: Target precision (fp16, int8, int4)
- `--output`: Path to save quantized model

Examples
--------

Load a model and run inference:

.. code-block:: bash

    python -m egen.cli model load --hub-id ErebusTN/THL-150
    python -m egen.cli model inference --input "def fibonacci(n):" --max-length 200 --domain code

Start an interactive prompt session:

.. code-block:: bash

    python -m egen.cli model prompt --temperature 0.8 --domain general

Run the self-healing monitoring system:

.. code-block:: bash

    python -m egen.cli self-healing monitor --interval 30 --log-file logs/custom_monitor.log

Optimize model with pruning and quantization:

.. code-block:: bash

    python -m egen.cli self-optimization pruning --model-path models/thl150 --target-sparsity 0.3
    python -m egen.cli self-optimization quantization --model-path models/thl150_pruned --precision int8