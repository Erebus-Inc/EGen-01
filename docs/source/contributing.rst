Contributing
===========

Thank you for your interest in contributing to the EGen Platform! This guide will help you get started with contributing to the project.

Code of Conduct
--------------

Please read and follow our :doc:`Code of Conduct <code_of_conduct>` to foster an open and welcoming environment.

Getting Started
--------------

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up the development environment**:

   .. code-block:: bash

      # Create and activate a virtual environment
      conda create -n egen python=3.12.6
      conda activate egen
      
      # Install in development mode
      pip install -e .

Development Workflow
------------------

1. **Create a branch** for your feature or bugfix:

   .. code-block:: bash

      git checkout -b feature/your-feature-name

2. **Make your changes** and write tests for them

3. **Run tests** to ensure your changes don't break existing functionality:

   .. code-block:: bash

      make test

4. **Format your code** using Black and isort:

   .. code-block:: bash

      make format

5. **Run linting** to ensure code quality:

   .. code-block:: bash

      make lint

6. **Update documentation** if necessary:

   .. code-block:: bash

      make docs

7. **Commit your changes** with a descriptive commit message:

   .. code-block:: bash

      git commit -m "Add feature: your feature description"

8. **Push to your fork**:

   .. code-block:: bash

      git push origin feature/your-feature-name

9. **Submit a pull request** to the main repository

Pull Request Guidelines
---------------------

- Fill in the required template
- Include tests for new features or bug fixes
- Update documentation for significant changes
- Follow the project's code style
- Keep pull requests focused on a single topic

Code Style
---------

We follow the `PEP 8 <https://www.python.org/dev/peps/pep-0008/>`_ style guide for Python code. We use:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting

Testing
-------

We use pytest for testing. All new code should include tests. To run tests:

.. code-block:: bash

   make test

To run tests with coverage:

.. code-block:: bash

   make test-cov

Documentation
-------------

We use Sphinx for documentation. Please update the documentation when making significant changes:

.. code-block:: bash

   make docs

Documentation is written in reStructuredText format. Here's a quick reference:

- **Headings**:

  .. code-block:: rst

     Heading 1
     =========

     Heading 2
     ---------

     Heading 3
     ~~~~~~~~~

- **Code blocks**:

  .. code-block:: rst

     .. code-block:: python

        def example_function():
            return "Hello, world!"

- **Links**:

  .. code-block:: rst

     `External link <https://example.com>`_
     :doc:`Internal link <file_name>`

Project Structure
---------------

.. code-block:: text

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

Adding New Features
-----------------

When adding new features, please follow these guidelines:

1. **Discuss first**: Open an issue to discuss the feature before implementing it
2. **Design**: Create a design document for significant features
3. **Implementation**: Implement the feature with appropriate tests
4. **Documentation**: Update documentation to reflect the new feature
5. **Review**: Submit a pull request for review

Reporting Bugs
-------------

When reporting bugs, please include:

- A clear and descriptive title
- Steps to reproduce the bug
- Expected behavior
- Actual behavior
- Environment information (OS, Python version, etc.)
- Any relevant logs or error messages

Feature Requests
--------------

When requesting features, please include:

- A clear and descriptive title
- A detailed description of the feature
- Use cases for the feature
- Any relevant examples or mockups

License
-------

By contributing, you agree that your contributions will be licensed under the project's license.