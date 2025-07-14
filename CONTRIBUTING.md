# Contributing to EGen Platform

Thank you for your interest in contributing to the EGen Platform! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md) to foster an open and welcoming environment.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up the development environment**:
   ```bash
   # Create and activate a virtual environment
   conda create -n egen python=3.12.6
   conda activate egen
   
   # Install in development mode
   pip install -e .
   ```

## Development Workflow

1. **Create a branch** for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and write tests for them

3. **Run tests** to ensure your changes don't break existing functionality:
   ```bash
   make test
   ```

4. **Format your code** using Black and isort:
   ```bash
   make format
   ```

5. **Run linting** to ensure code quality:
   ```bash
   make lint
   ```

6. **Update documentation** if necessary:
   ```bash
   make docs
   ```

7. **Commit your changes** with a descriptive commit message:
   ```bash
   git commit -m "Add feature: your feature description"
   ```

8. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

9. **Submit a pull request** to the main repository

## Pull Request Guidelines

- Fill in the required template
- Include tests for new features or bug fixes
- Update documentation for significant changes
- Follow the project's code style
- Keep pull requests focused on a single topic

## Code Style

We follow the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code. We use:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting

## Testing

We use pytest for testing. All new code should include tests. To run tests:

```bash
make test
```

To run tests with coverage:

```bash
make test-cov
```

## Documentation

We use Sphinx for documentation. Please update the documentation when making significant changes:

```bash
make docs
```

## Project Structure

```
EGen/
├── egen/               # Main package
│   ├── model/          # THL-150 transformer
│   ├── self_healing/   # Autonomous repair
│   ├── self_optimization/ # NAS & tuning
│   ├── data_autonomy/  # Dataset management
│   ├── monitoring/     # Metrics & alerting
│   ├── api/            # FastAPI endpoints
│   ├── web/            # Streamlit UI
│   └── assistant/      # EGen-01 integration
├── tests/              # Test suite
├── docs/               # Documentation
└── docker/             # Docker configuration
```

## License

By contributing, you agree that your contributions will be licensed under the project's license.