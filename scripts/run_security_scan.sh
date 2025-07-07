#!/usr/bin/env bash
# Run security scanning with Bandit
set -euo pipefail

bandit -r casebuilder -ll
