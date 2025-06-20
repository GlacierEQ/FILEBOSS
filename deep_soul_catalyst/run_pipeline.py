"""Run the full Deep Soul Catalyst automation pipeline.

Usage (from repo root):

    python -m deep_soul_catalyst.run_pipeline

This will:
1. Analyze the codebase (Phase-1)
2. Build an integration blueprint & scaffold (Phase-2)
3. Execute the plan (Phase-3)
"""
from pathlib import Path

from deep_soul_catalyst.pipeline.analyzer import ProjectAnalyzer
from deep_soul_catalyst.pipeline.integrator import ProjectIntegrator
from deep_soul_catalyst.pipeline.executor import ProjectExecutor


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]  # go up to repo root

    # Phase-1: Analysis ---------------------------------------------------
    analyzer = ProjectAnalyzer(project_root)
    analysis = analyzer.analyze()

    # Phase-2: Blueprint & Scaffolding -----------------------------------
    integrator = ProjectIntegrator(project_root, analysis)
    plan = integrator.create_integration_plan()
    integrator.generate_code_scaffolding()

    # Phase-3: Execution --------------------------------------------------
    executor = ProjectExecutor(project_root, plan)
    executor.run()


if __name__ == "__main__":
    main()
