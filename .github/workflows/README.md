# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the FileBoss project.

## Available Workflows

### CI Workflow (`ci.yml`)

Runs on every push to `main`/`master` and pull requests. It includes:

- Python package installation
- Running tests with pytest
- Code coverage reporting
- Linting with flake8
- Code formatting checks with black and isort

### Release Workflow (`release.yml`)

Triggered when a new tag is pushed (format: `v*.*.*`). It includes:

- Building Python package
- Publishing to PyPI
- Creating GitHub releases

### Workflow Syncer (`scripts/sync_github_actions.py`)

A script to synchronize GitHub Actions workflows across multiple repositories.

## Setup

1. **Secrets**:
   - `PYPI_API_TOKEN`: PyPI API token for publishing packages
   - `GITHUB_TOKEN`: GitHub token for repository access

2. **Configuration**:
   - Update `.github/workflows/sync-config.json` with your repository details

## Usage

### Manual Workflow Sync

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run the sync script
python scripts/sync_github_actions.py
```

### Creating a New Release

```bash
# Create a new version tag
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0
```

## Best Practices

1. Keep workflow files in `.github/workflows/`
2. Use environment variables for sensitive data
3. Cache dependencies to speed up builds
4. Use custom actions for complex, reusable steps
5. Document new workflows in this README
