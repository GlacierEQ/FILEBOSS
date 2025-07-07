#!/usr/bin/env bash
# Run code formatters, linters, and tests
set -euo pipefail

black .
flake8
pytest tests/
