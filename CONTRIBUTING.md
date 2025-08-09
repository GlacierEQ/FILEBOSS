# Contributing to FileBoss

Thank you for your interest in contributing to FileBoss! We appreciate your time and effort in making this project better.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)
- [License](#license)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment (see below)
4. Create a new branch for your changes
5. Make your changes and commit them
6. Push your changes to your fork
7. Open a pull request

## Development Setup

### Prerequisites

- Python 3.9+
- pip
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/FileBoss.git
   cd FileBoss
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package in development mode with all dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Running Tests

Run the test suite using the following command:

```bash
make test
```

This will run all tests with coverage reporting. For more specific test runs, you can use:

```bash
# Run a specific test file
pytest tests/unit/test_example.py

# Run tests with specific markers
pytest -m "not slow"
```

## Code Style

We use several tools to maintain code quality and style:

- **Black** for code formatting
- **isort** for import sorting
- **mypy** for static type checking
- **flake8** for linting

Run the formatters and linters:

```bash
make format    # Auto-format code
make lint      # Run all linters
make check-types  # Run type checking
```

## Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a build.
2. Update the README.md with details of changes to the interface, including new environment variables, exposed ports, useful file locations, and container parameters.
3. Increase the version numbers in any example files and the README.md to the new version that this Pull Request would represent. The versioning scheme we use is [SemVer](http://semver.org/).
4. You may merge the Pull Request in once you have the sign-off of two other developers, or if you do not have permission to do that, you may request the second reviewer to merge it for you.

## Reporting Issues

When reporting issues, please include the following:

- A description of the problem
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Any relevant logs or error messages
- Version of the software you're using
- Operating system and version

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
