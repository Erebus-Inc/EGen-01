Installation
============

Prerequisites
-------------

- Python 3.12+
- NVIDIA GPU with CUDA
- Docker & Docker Compose (for enterprise features)
- 16GB+ RAM

Quick Start
-----------

.. code-block:: bash

    # Clone repository
git clone https://github.com/Erebus-Inc/EGen-01.git
cd EGen-01

    # Setup environment (Conda recommended)
    conda create -n egen python=3.12.6
    conda activate egen

    # Install dependencies
    pip install -r requirements.txt

    # Configure environment
    cp .env.example .env
    # Set your API keys in .env

    # Start services
    docker-compose up -d  # Enterprise features

    # Or run components individually
    python -m egen.api.main  # API server
    python -m egen.web.app  # Web interface
    python -m egen.cli  # Command-line interface

Development Setup
----------------

.. code-block:: bash

    # Install in development mode
    pip install -e .

    # Run tests
    python -m pytest

    # Generate documentation
    sphinx-build -b html docs/source docs/build

Docker Deployment
----------------

The EGen platform uses Docker Compose for containerized deployment. The following services are defined:

- **egen-model**: Core AI model service
- **egen-ui**: Web interface
- **prometheus**: Metrics collection
- **grafana**: Metrics visualization
- **elasticsearch**: Log storage
- **kibana**: Log visualization

To start all services:

.. code-block:: bash

    docker-compose up -d

To view logs:

.. code-block:: bash

    docker-compose logs -f

To stop all services:

.. code-block:: bash

    docker-compose down

Environment Configuration
------------------------

The EGen platform uses a `.env` file for environment configuration. Copy the `.env.example` file to `.env` and set the following variables:

.. code-block:: bash

    # API Keys
    HUGGINGFACE_API_KEY=your_huggingface_api_key
    OPENAI_API_KEY=your_openai_api_key
    WANDB_API_KEY=your_wandb_api_key

    # Model Configuration
    MODEL_PATH=./models/thl150
    MODEL_PRECISION=fp16  # Options: fp32, fp16, int8, int4

    # Deployment Configuration
    DEPLOYMENT_MODE=development  # Options: development, production
    API_HOST=0.0.0.0
    API_PORT=8000
    WEB_UI_PORT=8501