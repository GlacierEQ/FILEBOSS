#!/usr/bin/env bash
# Run full audit: formatting, linting, tests, security scan
set -euo pipefail

scripts/run_checks.sh
scripts/run_security_scan.sh
