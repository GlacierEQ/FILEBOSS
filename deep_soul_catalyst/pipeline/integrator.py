import os
from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader


class ProjectIntegrator:
    """Phase-2 Blueprint generator. Produces an integration plan & scaffolds directories."""

    def __init__(self, project_root: Path, analysis_results: Dict):
        self.project_root = project_root
        self.analysis = analysis_results
        self.template_env = Environment(loader=FileSystemLoader(str(project_root / "templates")))
        self.integration_plan: Dict = {}

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    def create_integration_plan(self) -> Dict:
        """Produce a high-level integration plan (components, interfaces, data-flows)."""
        self.integration_plan = {
            "components": self._define_components(),
            "interfaces": self._define_interfaces(),
            "data_flows": self._define_data_flows(),
        }
        return self.integration_plan

    def generate_code_scaffolding(self):
        """Generate directory structure and skeleton code from templates."""
        self._create_directory_structure()
        self._render_templates()

    # ------------------------------------------------------------------
    # Internal helpers – plan definition
    # ------------------------------------------------------------------
    def _define_components(self) -> List[Dict]:
        comps: List[Dict] = [
            {
                "name": "FastAPI Core",
                "description": "Main FastAPI app",
                "status": "existing",
                "dependencies": ["PostgreSQL", "JWT"],
            },
            {
                "name": "DeepSoulCatalyst",
                "description": "Advanced analysis engine",
                "status": "new",
                "dependencies": [],
            },
        ]
        # add DB models detected from analysis
        for model in self.analysis.get("database_models", []):
            comps.append(
                {
                    "name": model["class"],
                    "description": f"DB model for {model['class']}",
                    "status": "existing",
                    "dependencies": ["PostgreSQL"],
                }
            )
        return comps

    def _define_interfaces(self) -> List[Dict]:
        ints: List[Dict] = []
        for ep in self.analysis.get("api_endpoints", []):
            ints.append(
                {
                    "name": f"API: {ep['function']}",
                    "type": "REST",
                    "methods": ep["methods"],
                    "provider": ep["module"],
                }
            )
        # placeholder for catalyst gRPC interface
        ints.append(
            {
                "name": "DeepSoulCatalyst gRPC",
                "type": "gRPC",
                "methods": ["Invoke", "History", "Feedback"],
                "provider": "DeepSoulCatalyst",
            }
        )
        return ints

    def _define_data_flows(self) -> List[Dict]:
        return [
            {
                "name": "Document processing",
                "steps": [
                    {"component": "FastAPI Core", "action": "upload"},
                    {"component": "DeepSoulCatalyst", "action": "analyze"},
                    {"component": "PostgreSQL", "action": "persist"},
                ],
            }
        ]

    # ------------------------------------------------------------------
    # Internal helpers – scaffolding
    # ------------------------------------------------------------------
    def _create_directory_structure(self):
        dirs = [
            "app/api",
            "app/core",
            "app/db",
            "app/models",
            "app/services/deep_soul_catalyst",
            "tests/unit",
            "tests/integration",
            "deployment",
        ]
        for d in dirs:
            os.makedirs(self.project_root / d, exist_ok=True)

    def _render_templates(self):
        """Render available templates if present (safe no-op when none)."""
        try:
            api_tpl = self.template_env.get_template("api_route.py.j2")
            with open(self.project_root / "app/api/deep_soul.py", "w", encoding="utf-8") as f:
                f.write(
                    api_tpl.render(
                        path="/api/analysis",
                        function_name="analyze_document",
                        description="Analyze a document",
                    )
                )
        except Exception:
            # Template may not exist yet – that's fine for now.
            pass
