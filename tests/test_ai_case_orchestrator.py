import asyncio
from types import SimpleNamespace
from pathlib import Path
import pytest

from casebuilder.services.ai_case_orchestrator import (
    SmartEvidenceRenamer,
    AICaseOrchestrator,
)


class DummyAI:
    async def analyze_evidence(
        self, evidence_content: str | bytes, content_type: str, **kwargs
    ) -> object:
        return SimpleNamespace(summary="Test Summary")


@pytest.mark.asyncio
async def test_orchestrator_renames_files(tmp_path: Path) -> None:
    file1 = tmp_path / "doc1.txt"
    file1.write_text("example")

    renamer = SmartEvidenceRenamer(DummyAI())
    orchestrator = AICaseOrchestrator(renamer)

    new_paths = await orchestrator.rename_files([file1])

    assert len(new_paths) == 1
    assert new_paths[0].name.startswith("test_summary_doc1.txt")
    assert new_paths[0].exists()
