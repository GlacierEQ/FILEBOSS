#!/usr/bin/env python3
"""
Sync GitHub Actions workflows across repositories.

This script helps manage and synchronize GitHub Actions workflows
across multiple repositories in an organization.
"""

import os
import sys
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sync_github_actions.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG_FILE = Path(__file__).parent.parent / '.github' / 'workflows' / 'sync-config.json'
WORKFLOWS_DIR = Path(__file__).parent.parent / '.github' / 'workflows'
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

class GitHubActionsSyncer:
    def __init__(self, config_path: Path):
        """Initialize the GitHub Actions syncer with configuration."""
        self.config = self._load_config(config_path)
        self.workflows = self._discover_workflows()

    def _load_config(self, config_path: Path) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            sys.exit(1)

    def _discover_workflows(self) -> List[Path]:
        """Discover all workflow files in the workflows directory."""
        return list(WORKFLOWS_DIR.glob('*.yml')) + list(WORKFLOWS_DIR.glob('*.yaml'))

    def clone_repo(self, repo_url: str, target_dir: Path) -> bool:
        """Clone a git repository."""
        try:
            subprocess.run(
                ['git', 'clone', repo_url, str(target_dir)],
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone {repo_url}: {e.stderr}")
            return False

    def sync_workflows_to_repo(self, repo_path: Path) -> bool:
        """Sync workflows to a target repository."""
        try:
            repo_workflows_dir = repo_path / '.github' / 'workflows'
            repo_workflows_dir.mkdir(parents=True, exist_ok=True)

            # Copy each workflow file
            for workflow in self.workflows:
                target_path = repo_workflows_dir / workflow.name
                with open(workflow, 'r') as src, open(target_path, 'w') as dst:
                    dst.write(src.read())
                logger.info(f"Updated {target_path}")

            return True
        except Exception as e:
            logger.error(f"Error syncing workflows to {repo_path}: {e}")
            return False

    def run(self):
        """Run the sync process for all configured repositories."""
        if not GITHUB_TOKEN:
            logger.error("GITHUB_TOKEN environment variable not set")
            sys.exit(1)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            for repo in self.config.get('repositories', []):
                repo_url = repo.get('url')
                if not repo_url:
                    logger.warning("Repository URL not provided in config")
                    continue

                repo_name = repo_url.split('/')[-1].replace('.git', '')
                repo_path = temp_path / repo_name

                logger.info(f"Processing repository: {repo_url}")
                
                if self.clone_repo(repo_url, repo_path):
                    if self.sync_workflows_to_repo(repo_path):
                        self._commit_and_push_changes(repo_path)

    def _commit_and_push_changes(self, repo_path: Path):
        """Commit and push changes to the repository."""
        try:
            # Add all changes
            subprocess.run(
                ['git', 'add', '.'],
                cwd=repo_path,
                check=True,
                capture_output=True
            )

            # Check if there are any changes to commit
            status = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=repo_path,
                capture_output=True,
                text=True
            )

            if not status.stdout.strip():
                logger.info("No changes to commit")
                return

            # Commit changes
            subprocess.run(
                ['git', 'commit', '-m', 'chore: update GitHub Actions workflows'],
                cwd=repo_path,
                check=True,
                capture_output=True
            )

            # Push changes
            subprocess.run(
                ['git', 'push'],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            
            logger.info("Successfully pushed workflow updates")

        except subprocess.CalledProcessError as e:
            logger.error(f"Error committing/pushing changes: {e.stderr}")

def main():
    """Main entry point."""
    if not CONFIG_FILE.exists():
        logger.error(f"Configuration file not found: {CONFIG_FILE}")
        sys.exit(1)

    syncer = GitHubActionsSyncer(CONFIG_FILE)
    syncer.run()

if __name__ == "__main__":
    main()
