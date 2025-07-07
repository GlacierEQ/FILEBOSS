#!/usr/bin/env bash
# Run tests with coverage
set -euo pipefail

pytest --cov=casebuilder --cov-report=term-missing --cov-fail-under=90 "$@"
