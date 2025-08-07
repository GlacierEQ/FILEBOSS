from __future__ import annotations

"""AI-powered case orchestration and smart evidence renaming."""

import asyncio
from pathlib import Path
from typing import Iterable, List, Protocol


class AIAnalysisServiceProtocol(Protocol):
    """Protocol for AI analysis services used by the orchestrator."""

    async def analyze_evidence(
        self,
        evidence_content: str | bytes,
        content_type: str,
        **kwargs: object,
    ) -> object: ...


class SmartEvidenceRenamer:
    """Generate intelligent file names using an AI analysis service."""

    def __init__(self, ai_service: AIAnalysisServiceProtocol) -> None:
        self._ai_service = ai_service

    async def generate_name(self, file_path: Path) -> str:
        """Return an AI-generated descriptive name for ``file_path``."""
        content = file_path.read_text(errors="ignore")
        analysis = await self._ai_service.analyze_evidence(content, "text/plain")
        summary = getattr(analysis, "summary", None) or "evidence"
        normalized = "_".join(summary.lower().split())[:50]
        return f"{normalized}_{file_path.name}"


class AICaseOrchestrator:
    """Coordinate evidence processing and intelligent renaming."""

    def __init__(self, renamer: SmartEvidenceRenamer) -> None:
        self._renamer = renamer

    async def rename_files(self, files: Iterable[Path]) -> List[Path]:
        """Rename files using ``SmartEvidenceRenamer`` and return new paths."""
        new_paths: List[Path] = []
        for file_path in files:
            new_name = await self._renamer.generate_name(file_path)
            new_path = file_path.with_name(new_name)
            file_path.rename(new_path)
            new_paths.append(new_path)
        return new_paths
