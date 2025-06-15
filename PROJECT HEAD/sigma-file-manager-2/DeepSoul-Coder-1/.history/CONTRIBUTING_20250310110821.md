# Contributing to DeepSeek-Coder

Thank you for your interest in contributing to DeepSeek-Coder! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation Guidelines](#documentation-guidelines)
- [Pull Request Process](#pull-request-process)
- [Roadmap and Future Features](#roadmap-and-future-features)
- [Getting Help](#getting-help)

## Code of Conduct

We expect all contributors to adhere to the project's code of conduct. Please be respectful, inclusive, and constructive in all interactions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/DeepSeek-Coder.git
   cd DeepSeek-Coder
   ```
3. **Set up the development environment**:
   ```bash
   # Create and activate a virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   ```

4. **Set up pre-commit hooks**:
   ```bash
   pre-commit install
   ```

5. **Add the upstream repository as a remote**:
   ```bash
   git remote add upstream https://github.com/deepseek-ai/deepseek-coder.git
   ```

## Development Workflow

1. **Create a new branch** for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
   
   Use the following branch naming conventions:
   - `feature/` - for new features
   - `bugfix/` - for bug fixes
   - `docs/` - for documentation updates
   - `test/` - for adding or updating tests
   - `refactor/` - for code refactoring

2. **Make your changes**, adhering to the [Coding Standards](#coding-standards)

3. **Commit your changes** with clear and descriptive commit messages:
   ```bash
   git commit -m "Add feature: description of your feature"
   ```

4. **Fetch upstream changes** and rebase your branch:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

5. **Push your branch** to your fork:
   ```bash
   git push -u origin feature/your-feature-name
   ```

6. **Submit a pull request** from your branch to the main repository

## Coding Standards

We follow these standards to ensure code quality and consistency:

1. **Python Code Style**:
   - Follow [PEP 8](https://pep8.org/) style guidelines
   - Use 4 spaces for indentation (no tabs)
   - Maximum line length of 100 characters
   - Use meaningful variable and function names
   
2. **Code Formatting**:
   - We use [Black](https://black.readthedocs.io/) for Python code formatting
   - We use [isort](https://pycqa.github.io/isort/) for sorting imports
   
3. **Type Hints**:
   - Use Python type hints wherever possible
   - We check typing with [mypy](http://mypy-lang.org/)
   
4. **Documentation**:
   - All public modules, functions, classes, and methods should have docstrings
   - Follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings) for docstrings

## Testing Guidelines

1. **Writing Tests**:
   - Write tests for all new features and bug fixes
   - Place tests in the `tests/` directory
   - Use [pytest](https://docs.pytest.org/) for writing tests
   
2. **Running Tests**:
   ```bash
   # Run all tests
   pytest
   
   # Run specific test file
   pytest tests/test_module.py
   
   # Run with coverage report
   pytest --cov=. --cov-report=term
   ```
   
3. **Test Categories**:
   - Unit tests for individual functions and classes
   - Integration tests for module interactions
   - Mark GPU tests with `@pytest.mark.gpu` to allow skipping in CI

## Documentation Guidelines

1. **Code Documentation**:
   - Use docstrings for all public APIs
   - Include examples where appropriate
   - Document parameters, return types, and exceptions
   
2. **Project Documentation**:
   - Update the README.md file for significant changes
   - Keep documentation in the docs/ directory up-to-date
   - Use Markdown for documentation files

## Pull Request Process

1. **Create a Pull Request** via GitHub
2. **Fill in the PR template** with:
   - A clear description of the changes
   - Any related issues
   - Testing that was performed
   - Screenshots (if applicable)
3. **Review Process**:
   - Maintainers will review your PR
   - Address any comments or requested changes
   - Make sure CI checks pass
4. **Approval and Merge**:
   - PRs require approval from at least one maintainer
   - Once approved, a maintainer will merge your PR

## Roadmap and Future Features

We maintain a list of planned features and improvements in our [GitHub Issues](https://github.com/deepseek-ai/deepseek-coder/issues) with the "enhancement" label. Check there for ideas on what to work on.

Priority areas for contributions:

- Improved documentation and examples
- Performance optimizations
- Additional model fine-tuning scripts
- Enhanced evaluation methods
- Support for more programming languages
- Integration with popular IDEs and tools

## Getting Help

If you need help with contributing:

- **Open an issue** for project-related questions
- **Join our Discord community** for discussions
- **Contact the maintainers** for specific questions

Thank you for contributing to DeepSeek-Coder!
