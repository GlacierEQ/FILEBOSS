"""Evidence processing service module."""

from __future__ import annotations

import asyncio
import mimetypes
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import (
    Case,
    CaseStatus,
    Evidence,
    EvidenceStatus,
    EvidenceType,
    TimelineEvent,
    TimelineEventType,
    User,
)
from ..db.repositories.evidence import EvidenceRepositoryAsync
from ..db.repositories.timeline import TimelineEventRepositoryAsync


class EvidenceProcessingService:
    """Service for processing and organizing evidence files."""

    def __init__(self, db_session: AsyncSession, storage_root: Optional[Path] = None) -> None:
        """Initialize the service with a database session."""

        self.db = db_session
        self.storage_root = Path(storage_root or Path("./data/evidence"))
        self.storage_root.mkdir(parents=True, exist_ok=True)

    async def process_evidence_upload(
        self,
        *,
        file: UploadFile,
        case_id: str,
        created_by: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Persist an uploaded evidence file and create database records."""

        await self._ensure_user(created_by)
        await self._ensure_case(case_id, created_by)

        stored_path = await self._store_uploaded_file(file, case_id)
        file_size = stored_path.stat().st_size
        mime_type, _ = mimetypes.guess_type(stored_path.name)

        evidence = Evidence(
            title=stored_path.stem,
            description=description or stored_path.name,
            evidence_type=EvidenceType.DOCUMENT,
            status=EvidenceStatus.PENDING_REVIEW,
            case_id=case_id,
            file_path=str(stored_path),
            file_name=stored_path.name,
            file_size=file_size,
            file_type=mime_type or "application/octet-stream",
            tags=tags or [],
            created_by_id=created_by,
            chain_of_custody=[
                self._build_custody_event(
                    action="FILE_UPLOADED",
                    user_id=created_by,
                    details={"filename": stored_path.name},
                )
            ],
            metadata_={"tags": tags or []},
        )

        self.db.add(evidence)
        await self.db.flush()
        await self.db.refresh(evidence)

        timeline_event = await self._create_timeline_event(
            title=f"Evidence uploaded: {stored_path.name}",
            description=description or "Evidence file uploaded",
            case_id=case_id,
            created_by=created_by,
            event_type=TimelineEventType.EVIDENCE_ADDED,
            metadata={
                "evidence_id": evidence.id,
                "filename": stored_path.name,
                "upload_type": "single",
            },
        )
        timeline_event.evidence.append(evidence)
        await self.db.flush()

        return {
            "id": evidence.id,
            "filename": stored_path.name,
            "content_type": mime_type or "application/octet-stream",
            "case_id": case_id,
            "description": description or stored_path.name,
            "tags": tags or [],
            "created_by": created_by,
            "status": evidence.status.value,
        }

    async def process_evidence_directory(
        self,
        *,
        directory: Path,
        case_id: str,
        evidence_type: EvidenceType,
        created_by: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Evidence]:
        """Process all files in a directory and create evidence entries."""

        source_dir = Path(directory)
        if not source_dir.exists() or not source_dir.is_dir():
            raise ValueError(f"Directory {source_dir} does not exist or is not a directory")

        await self._ensure_user(created_by)
        await self._ensure_case(case_id, created_by)

        evidence_items: List[Evidence] = []
        for file_path in sorted(p for p in source_dir.rglob("*") if p.is_file()):
            stored_path = await self._store_file(file_path, case_id)
            file_size = stored_path.stat().st_size
            mime_type, _ = mimetypes.guess_type(stored_path.name)

            evidence = Evidence(
                title=file_path.stem,
                description=description or f"Imported {file_path.name}",
                evidence_type=evidence_type,
                status=EvidenceStatus.PENDING_REVIEW,
                case_id=case_id,
                file_path=str(stored_path),
                file_name=stored_path.name,
                file_size=file_size,
                file_type=mime_type or "application/octet-stream",
                tags=tags or [],
                created_by_id=created_by,
                chain_of_custody=[
                    self._build_custody_event(
                        action="INGESTED_FROM_DIRECTORY",
                        user_id=created_by,
                        details={"source_path": str(file_path)},
                    )
                ],
                metadata_={
                    "source_path": str(file_path),
                    "tags": tags or [],
                },
            )

            self.db.add(evidence)
            await self.db.flush()
            await self.db.refresh(evidence)
            evidence_items.append(evidence)

            event = await self._create_timeline_event(
                title=f"Evidence added: {file_path.name}",
                description=description or "Evidence ingested from directory",
                case_id=case_id,
                created_by=created_by,
                event_type=TimelineEventType.EVIDENCE_ADDED,
                metadata={
                    "evidence_id": evidence.id,
                    "filename": file_path.name,
                    "source_path": str(file_path),
                },
            )
            event.evidence.append(evidence)
            await self.db.flush()

        return evidence_items

    async def organize_evidence_files(
        self,
        *,
        evidence_ids: Iterable[str],
        output_dir: Path,
        organization_scheme: str = "type_date",
    ) -> List[Dict[str, str]]:
        """Organize evidence files into a directory structure."""

        destination_root = Path(output_dir)
        destination_root.mkdir(parents=True, exist_ok=True)

        if not evidence_ids:
            return []

        stmt = select(Evidence).where(Evidence.id.in_(list(evidence_ids)))
        result = await self.db.execute(stmt)
        evidence_records = result.scalars().all()

        reorganized: List[Dict[str, str]] = []
        for evidence in evidence_records:
            source_path = await self._ensure_evidence_source(evidence)

            destination_path = self._build_destination_path(
                destination_root,
                evidence,
                organization_scheme,
            )
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            await asyncio.to_thread(shutil.copy2, source_path, destination_path)

            metadata = evidence.metadata
            organized_locations = list(metadata.get("organized_locations", []))
            organized_locations.append(str(destination_path))
            metadata["organized_locations"] = organized_locations
            evidence.metadata = metadata

            reorganized.append(
                {
                    "evidence_id": evidence.id,
                    "original_path": str(source_path),
                    "new_path": str(destination_path),
                }
            )

        await self.db.flush()
        return reorganized

    async def update_evidence_status(
        self,
        *,
        evidence_id: str,
        new_status: EvidenceStatus,
        user_id: str,
        notes: Optional[str] = None,
    ) -> Evidence:
        """Update the status of an evidence item and record custody events."""

        if isinstance(new_status, str):
            new_status = EvidenceStatus(new_status)

        stmt = select(Evidence).where(Evidence.id == evidence_id)
        result = await self.db.execute(stmt)
        evidence = result.scalar_one_or_none()
        if evidence is None:
            raise ValueError(f"Evidence {evidence_id} not found")

        if evidence.status != new_status:
            evidence.status = new_status
            custody_events = list(evidence.chain_of_custody or [])
            custody_events.append(
                self._build_custody_event(
                    action="STATUS_CHANGED",
                    user_id=user_id,
                    details={"new_status": new_status.value},
                    notes=notes,
                )
            )
            evidence.chain_of_custody = custody_events

            event = await self._create_timeline_event(
                title=f"Evidence status updated: {evidence.title}",
                description=notes or "Evidence status changed",
                case_id=evidence.case_id,
                created_by=user_id,
                event_type=TimelineEventType.EVIDENCE_STATUS_CHANGED,
                metadata={
                    "evidence_id": evidence.id,
                    "new_status": new_status.value,
                },
            )
            event.evidence.append(evidence)
            await self.db.flush()

        await self.db.refresh(evidence)
        return evidence

    async def link_evidence_to_timeline(
        self,
        *,
        evidence_id: str,
        timeline_event_id: str,
        user_id: str,
    ) -> bool:
        """Associate evidence with a timeline event and log custody information."""

        evidence_repo = EvidenceRepositoryAsync(self.db)
        timeline_repo = TimelineEventRepositoryAsync(self.db)

        evidence = await evidence_repo.get(evidence_id)
        timeline_event = await timeline_repo.get(timeline_event_id)
        if evidence is None or timeline_event is None:
            return False

        await timeline_repo.add_evidence(event_id=timeline_event_id, evidence_id=evidence_id)

        custody_events = list(evidence.chain_of_custody or [])
        custody_events.append(
            self._build_custody_event(
                action="LINKED_TO_TIMELINE_EVENT",
                user_id=user_id,
                details={"timeline_event_id": timeline_event_id},
            )
        )
        evidence.chain_of_custody = custody_events

        metadata = dict(timeline_event.metadata_ or {})
        linked_ids = set(metadata.get("linked_evidence_ids", []))
        linked_ids.add(evidence_id)
        metadata["linked_evidence_ids"] = list(linked_ids)
        timeline_event.metadata_ = metadata

        await self.db.flush()
        return True

    async def _ensure_user(self, user_id: str) -> User:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            user = User(
                id=user_id,
                email=f"{user_id}@auto.local",
                hashed_password="placeholder",
                full_name="Automated Evidence User",
                is_active=True,
                is_superuser=False,
            )
            self.db.add(user)
            await self.db.flush()
        return user

    async def _ensure_case(self, case_id: str, owner_id: str) -> Case:
        stmt = select(Case).where(Case.id == case_id)
        result = await self.db.execute(stmt)
        case = result.scalar_one_or_none()
        if case is None:
            case = Case(
                id=case_id,
                title=f"Case {case_id}",
                description="Auto-generated case for evidence ingestion",
                status=CaseStatus.ACTIVE,
                owner_id=owner_id,
            )
            self.db.add(case)
            await self.db.flush()
        return case

    async def _create_timeline_event(
        self,
        *,
        title: str,
        description: Optional[str],
        case_id: str,
        created_by: str,
        event_type: TimelineEventType,
        metadata: Dict[str, Any],
    ) -> TimelineEvent:
        event = TimelineEvent(
            title=title,
            description=description,
            event_type=event_type,
            event_date=datetime.utcnow(),
            case_id=case_id,
            created_by_id=created_by,
            metadata_=metadata,
        )
        self.db.add(event)
        await self.db.flush()
        await self.db.refresh(event)
        return event

    async def _store_uploaded_file(self, upload: UploadFile, case_id: str) -> Path:
        destination_dir = self.storage_root / case_id
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination_path = destination_dir / upload.filename

        def _write_file() -> None:
            with destination_path.open("wb") as target:
                while True:
                    chunk = upload.file.read(1024 * 1024)
                    if not chunk:
                        break
                    target.write(chunk)

        await asyncio.to_thread(_write_file)
        await asyncio.to_thread(upload.file.seek, 0)
        return destination_path

    async def _store_file(self, source: Path, case_id: str) -> Path:
        destination_dir = self.storage_root / case_id
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination_path = destination_dir / source.name
        if source.resolve() != destination_path.resolve():
            await asyncio.to_thread(shutil.copy2, source, destination_path)
        return destination_path

    async def _ensure_evidence_source(self, evidence: Evidence) -> Path:
        """Return a file path for the evidence, generating a placeholder if needed."""

        if evidence.file_path:
            candidate = Path(evidence.file_path)
            if candidate.exists():
                return candidate

        placeholder = await self._create_placeholder_file(evidence)
        evidence.file_path = str(placeholder)
        evidence.file_name = placeholder.name

        metadata = evidence.metadata
        placeholder_paths = list(metadata.get("placeholder_paths", []))
        placeholder_paths.append(str(placeholder))
        metadata["placeholder_paths"] = placeholder_paths
        metadata["placeholder_generated"] = True
        metadata["placeholder_last_generated_at"] = datetime.utcnow().isoformat()
        evidence.metadata = metadata

        return placeholder

    async def _create_placeholder_file(self, evidence: Evidence) -> Path:
        """Create a lightweight placeholder file when the original asset is missing."""

        case_segment = evidence.case_id or "unassigned"
        placeholder_dir = self.storage_root / case_segment / "placeholders"
        placeholder_dir.mkdir(parents=True, exist_ok=True)

        filename = evidence.file_name or f"{evidence.id or 'evidence'}.placeholder"
        placeholder_path = placeholder_dir / filename
        message = (
            "This placeholder was generated because the original evidence file "
            "was not available during organization."
        )

        def _write_placeholder() -> None:
            placeholder_path.write_text(
                f"{message}\nEvidence ID: {evidence.id}\nTitle: {evidence.title}\n"
            )

        await asyncio.to_thread(_write_placeholder)
        return placeholder_path

    def _build_destination_path(
        self,
        root: Path,
        evidence: Evidence,
        scheme: str,
    ) -> Path:
        timestamp = evidence.created_at or datetime.utcnow()
        filename = evidence.file_name or f"{evidence.id}.bin"
        if scheme == "type_date":
            type_component = (
                evidence.evidence_type.value
                if isinstance(evidence.evidence_type, EvidenceType)
                else str(evidence.evidence_type)
            )
            return (
                root
                / type_component
                / f"{timestamp.year:04d}"
                / f"{timestamp.month:02d}"
                / f"{timestamp.day:02d}"
                / filename
            )
        return root / filename

    def _build_custody_event(
        self,
        *,
        action: str,
        user_id: str,
        details: Dict[str, Any],
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        event = {
            "action": action,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details,
        }
        if notes:
            event["notes"] = notes
        return event
