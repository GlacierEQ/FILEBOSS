# DeepSeek-Coder Developer Guide

This guide provides detailed information for developers who want to contribute to or extend the DeepSeek-Coder project.

## Development Environment Setup

### Prerequisites

- Python 3.8-3.11
- Git
- CUDA-compatible GPU (recommended)
- Docker and Docker Compose (recommended)

### Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/deepseek-ai/deepseek-coder.git
   cd deepseek-coder
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Development with Docker

For a containerized development environment:

1. Build and start the development container:
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

2. Access JupyterLab at http://localhost:8888 (token: deepsoul)

3. Execute commands in the container:
   ```bash
   docker-compose -f docker-compose.dev.yml exec deepsoul-dev bash
   ```

## Project Architecture

### Core Components

- **Model Framework**: Built on PyTorch and Hugging Face Transformers
- **API Server**: FastAPI-based server for exposing model capabilities
- **Knowledge Store**: Elasticsearch-based system for code knowledge
- **Evaluation System**: Tools for benchmarking and evaluating models

### Directory Structure

- `implementation/`: Core model implementation
- `scripts/`: Utility scripts
- `utils/`: Helper functions and utilities
- `tests/`: Test suite
- `docs/`: Documentation
- `demo/`: Demo applications
- `Evaluation/`: Evaluation benchmarks and tools
- `finetune/`: Fine-tuning scripts

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_app.py

# Run tests with coverage report
pytest --cov=. --cov-report=term-missing

# Run without GPU-specific tests
pytest -m "not gpu"
```

### Code Formatting and Linting

All code is automatically formatted and linted using pre-commit hooks. You can also run these commands manually:

```bash
# Format code
black .

# Sort imports
isort .

# Run linting
flake8 .

# Type checking
mypy .
```

### Documentation

We use Sphinx for documentation:

```bash
# Build documentation
cd docs
make html

# View documentation
open build/html/index.html

# Live documentation server (auto-reload)
make livehtml
```

## Release Process

### Versioning

We use semantic versioning (MAJOR.MINOR.PATCH):

1. MAJOR version for incompatible API changes
2. MINOR version for new functionality in a backward-compatible manner
3. PATCH version for backward-compatible bug fixes

### Creating a Release

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a pull request for the release
4. After merging, tag the release:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
5. GitHub Actions will build and publish the release

## Troubleshooting

### Common Development Issues

- **CUDA Out of Memory**:
  - Reduce batch size or model size
  - Try using model parallelism or gradient accumulation

- **Pre-commit Hook Failures**:
  - Check the specific error messages
  - Run hooks manually: `pre-commit run --all-files`

- **Tests Failing**:
  - Ensure all dependencies are installed
  - Check if the test requires GPU when none is available

### Getting Help

- Open an issue on GitHub
- Join our Discord community for discussions
- Contact maintainers via email

## Further Reading

- [API Documentation](docs/api/index.md)
- [Model Architecture](docs/architecture.md)
- [Performance Optimization Tips](docs/performance.md)
- [Contributing Guide](CONTRIBUTING.md)
