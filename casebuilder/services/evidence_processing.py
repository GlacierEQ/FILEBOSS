"""
Evidence Processing Service

This module provides services for processing evidence files and integrating with
the FileBoss system, evidence repository, and timeline.
"""

from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.repositories.evidence import EvidenceRepositoryAsync
from ..db.repositories.timeline import TimelineEventRepositoryAsync
from ..db.models import (
    Evidence,
    TimelineEventType,
    EvidenceType,
    EvidenceStatus,
)
from .fileboss_integration import FileBossIntegrator

logger = logging.getLogger(__name__)


class EvidenceProcessingService:
    """
    Service for processing evidence files and managing their integration
    with the case management system.
    """

    def __init__(
        self, db_session: AsyncSession, fileboss_config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the evidence processing service.

        Args:
            db_session: Async database session
            fileboss_config: Optional configuration for FileBossIntegrator
        """
        self.db_session = db_session
        self.evidence_repo = EvidenceRepositoryAsync(db_session)
        self.timeline_repo = TimelineEventRepositoryAsync(db_session)
        self.fileboss = FileBossIntegrator(config=fileboss_config or {})

    async def process_evidence_directory(
        self,
        directory: Union[str, Path],
        case_id: str,
        evidence_type: EvidenceType,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_by: Optional[str] = None,
        organization_scheme: str = "type_date",
    ) -> List[Evidence]:
        """Process a directory of files and create evidence records.

        Args:
            directory: Directory containing evidence files
            case_id: ID of the case to associate with the evidence
            evidence_type: Type of evidence
            description: Optional description for the evidence
            tags: Optional list of tags for the evidence
            created_by: ID of the user creating the evidence
            organization_scheme: How to organize the processed files

        Returns:
            List of created Evidence objects
        """
        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            raise NotADirectoryError(f"Directory not found: {directory}")

        # Process files with FileBoss
        processed_files = await self.fileboss.process_directory(
            directory=directory, case_id=case_id, recursive=True
        )

        created_evidence = []

        for file_meta in processed_files:
            try:
                # Create evidence record
                evidence_data = {
                    "case_id": case_id,
                    "title": file_meta.name,
                    "description": description or f"Evidence file: {file_meta.name}",
                    "evidence_type": evidence_type,
                    "status": EvidenceStatus.PENDING_REVIEW,
                    "file_path": str(file_meta.path),
                    "file_size": file_meta.size,
                    "file_type": file_meta.mime_type,
                    "hash_value": file_meta.hash,
                    "metadata": {
                        "original_path": str(file_meta.path),
                        "file_metadata": file_meta.metadata,
                        "processing_timestamp": datetime.utcnow().isoformat(),
                    },
                    "tags": tags or [],
                    "created_by": created_by,
                }

                evidence = await self.evidence_repo.create(evidence_data)

                # Create initial chain of custody event
                custody_event = {
                    "action": "EVIDENCE_CREATED",
                    "location": str(file_meta.path),
                    "notes": "Initial evidence creation from file processing",
                }

                await self.evidence_repo.add_custody_event(
                    evidence_id=evidence.id,
                    event=custody_event,
                    user_id=created_by or "system",
                )

                # Create timeline event
                timeline_event = {
                    "case_id": case_id,
                    "event_type": TimelineEventType.EVIDENCE_ADDED,
                    "title": f"New Evidence Added: {file_meta.name}",
                    "description": "Evidence file processed and added to case",
                    "timestamp": datetime.utcnow(),
                    "created_by": created_by,
                    "metadata": {
                        "evidence_id": str(evidence.id),
                        "file_name": file_meta.name,
                        "file_type": file_meta.mime_type,
                        "file_size": file_meta.size,
                    },
                }

                await self.timeline_repo.create(timeline_event)

                created_evidence.append(evidence)

                logger.info(
                    f"Processed evidence file: {file_meta.path} (ID: {evidence.id})"
                )

            except Exception as e:
                logger.error(
                    f"Error processing file {file_meta.path}: {e}", exc_info=True
                )
                continue

        return created_evidence

    async def organize_evidence_files(
        self,
        evidence_ids: List[str],
        output_dir: Union[str, Path],
        organization_scheme: str = "type_date",
    ) -> List[Dict[str, str]]:
        """Organize evidence files according to the specified scheme.

        Args:
            evidence_ids: List of evidence IDs to organize
            output_dir: Base directory for organized files
            organization_scheme: Scheme to use for organization
                - 'type_date': Organize by file type and date
                - 'type': Organize by file type only
                - 'date': Organize by date only
                - 'flat': All files in a single directory

        Returns:
            List of dictionaries with original and new file paths
        """
        # Get evidence records
        evidence_list = []
        for evidence_id in evidence_ids:
            evidence = await self.evidence_repo.get(evidence_id)
            if evidence and evidence.file_path:
                evidence_list.append(
                    {
                        "path": evidence.file_path,
                        "type": evidence.evidence_type.value.lower(),
                        "modified": datetime.timestamp(
                            evidence.updated_at or evidence.created_at
                        ),
                    }
                )

        # Organize files using FileBoss
        return await self.fileboss.organize_files(
            files=evidence_list,
            output_dir=output_dir,
            organization_scheme=organization_scheme,
        )

    async def update_evidence_status(
        self,
        evidence_id: str,
        new_status: EvidenceStatus,
        user_id: str,
        notes: Optional[str] = None,
    ) -> Optional[Evidence]:
        """Update the status of an evidence item and create a timeline event.

        Args:
            evidence_id: ID of the evidence to update
            new_status: New status to set
            user_id: ID of the user making the change
            notes: Optional notes about the status change

        Returns:
            Updated Evidence object if successful, None otherwise
        """
        # Get current evidence
        evidence = await self.evidence_repo.get(evidence_id)
        if not evidence:
            return None

        # Update status
        evidence.status = new_status
        await self.db_session.commit()

        # Create custody event
        custody_event = {
            "action": f"STATUS_CHANGED_TO_{new_status.name}",
            "location": evidence.file_path,
            "notes": notes or f"Evidence status changed to {new_status.value}",
        }

        await self.evidence_repo.add_custody_event(
            evidence_id=evidence.id, event=custody_event, user_id=user_id
        )

        # Create timeline event
        timeline_event = {
            "case_id": evidence.case_id,
            "event_type": TimelineEventType.EVIDENCE_STATUS_CHANGED,
            "title": f"Evidence Status Updated: {evidence.title}",
            "description": f"Status changed to {new_status.value}",
            "timestamp": datetime.utcnow(),
            "created_by": user_id,
            "metadata": {
                "evidence_id": str(evidence.id),
                "previous_status": evidence.status.value,
                "new_status": new_status.value,
                "notes": notes,
            },
        }

        await self.timeline_repo.create(timeline_event)

        logger.info(f"Updated status for evidence {evidence_id} to {new_status}")
        return evidence

    async def link_evidence_to_timeline(
        self, evidence_id: str, timeline_event_id: str, user_id: str
    ) -> bool:
        """Link an evidence item to a timeline event.

        Args:
            evidence_id: ID of the evidence to link
            timeline_event_id: ID of the timeline event to link to
            user_id: ID of the user making the link

        Returns:
            True if the link was created successfully, False otherwise
        """
        try:
            # Add evidence to timeline event
            await self.timeline_repo.add_evidence(
                event_id=timeline_event_id, evidence_id=evidence_id
            )

            # Get evidence for logging
            evidence = await self.evidence_repo.get(evidence_id)
            if evidence:
                # Create custody event
                custody_event = {
                    "action": "LINKED_TO_TIMELINE_EVENT",
                    "location": evidence.file_path,
                    "notes": f"Linked to timeline event {timeline_event_id}",
                }

                await self.evidence_repo.add_custody_event(
                    evidence_id=evidence.id, event=custody_event, user_id=user_id
                )

                logger.info(
                    "Linked evidence %s to timeline event %s",
                    evidence_id,
                    timeline_event_id,
                )

            return True

        except Exception as e:
            logger.error(
                "Error linking evidence %s to timeline event %s: %s",
                evidence_id,
                timeline_event_id,
                e,
                exc_info=True,
            )
            return False
