#!/usr/bin/env bash
# Run full CI pipeline: formatting, linting, tests with coverage, security scan, and docs build
set -euo pipefail

scripts/run_checks.sh
scripts/run_security_scan.sh
scripts/run_coverage.sh
scripts/build_docs.sh
