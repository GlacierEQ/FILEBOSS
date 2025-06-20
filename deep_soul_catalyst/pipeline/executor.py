import logging
import subprocess
from pathlib import Path
from typing import Dict


class ProjectExecutor:
    """Phase-3: Execute integration plan (deps install, tests, docker build)."""

    def __init__(self, project_root: Path, integration_plan: Dict):
        self.project_root = project_root
        self.integration_plan = integration_plan
        self.logger = self._setup_logger()
        self.status: Dict = {}

    # --------------------------------------------------------
    def run(self) -> Dict:
        self.logger.info("🔧 Executing integration plan …")
        self._install_dependencies()
        self._run_tests()
        self._build_docker_images()
        self.logger.info("✅ Execution completed")
        return self.status

    # --------------------------------------------------------
    def _setup_logger(self):
        logger = logging.getLogger("executor")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))
        logger.addHandler(handler)
        return logger

    def _install_dependencies(self):
        req = self.project_root / "requirements.txt"
        if req.exists():
            self.logger.info("📦 Installing dependencies")
            subprocess.run(["pip", "install", "-r", str(req)], check=False)
        else:
            self.logger.warning("requirements.txt not found – skipping install")

    def _run_tests(self):
        self.logger.info("🧪 Running tests via pytest")
        subprocess.run(["pytest", str(self.project_root / "tests")], check=False)

    def _build_docker_images(self):
        compose_file = self.project_root / "deployment/docker-compose.yml"
        if compose_file.exists():
            self.logger.info("🐳 Building docker images via compose")
            subprocess.run(["docker-compose", "-f", str(compose_file), "build"], check=False)
        else:
            self.logger.warning("docker-compose.yml not found – skipping build")
