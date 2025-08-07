"""Evidence API endpoints for the CaseBuilder application."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from casebuilder.db.base import get_async_db

router = APIRouter()


class EvidenceService:
    """Service class for evidence operations."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize the evidence service."""
        self.db = db

    async def create_evidence(
        self,
        *,
        file: UploadFile,
        case_id: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        created_by: int,
    ) -> Dict[str, Any]:
        """Create a new evidence record."""
        return {
            "id": 1,
            "filename": file.filename,
            "case_id": case_id,
            "description": description or file.filename,
            "tags": tags or [],
            "created_by": created_by,
            "status": "uploaded",
        }

    async def get_evidence(self, evidence_id: int) -> Optional[Dict[str, Any]]:
        """Get evidence by ID."""
        if evidence_id == 1:
            return {
                "id": 1,
                "filename": "example.pdf",
                "case_id": "case_001",
                "description": "Sample evidence",
                "tags": ["document"],
                "created_by": 1,
                "status": "uploaded",
            }
        return None

    async def update_evidence(
        self, evidence_id: int, updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update evidence record."""
        evidence = await self.get_evidence(evidence_id)
        if evidence:
            evidence.update(updates)
            return evidence
        return None


def get_evidence_service(
    db: AsyncSession = Depends(get_async_db),
) -> EvidenceService:
    """Get evidence service instance."""
    return EvidenceService(db)


@router.post("/upload/", status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    file: UploadFile = File(...),
    case_id: str = "default_case",
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    evidence_service: EvidenceService = Depends(get_evidence_service),
) -> Dict[str, Any]:
    """Upload a new evidence file."""
    try:
        evidence = await evidence_service.create_evidence(
            file=file,
            case_id=case_id,
            description=description,
            tags=tags,
            created_by=1,
        )
        return evidence
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload evidence: {str(e)}",
        ) from e


@router.get("/{evidence_id}")
async def get_evidence(
    evidence_id: int,
    evidence_service: EvidenceService = Depends(get_evidence_service),
) -> Dict[str, Any]:
    """Get evidence by ID."""
    evidence = await evidence_service.get_evidence(evidence_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )
    return evidence


@router.put("/{evidence_id}")
async def update_evidence(
    evidence_id: int,
    updates: Dict[str, Any],
    evidence_service: EvidenceService = Depends(get_evidence_service),
) -> Dict[str, Any]:
    """Update evidence record."""
    evidence = await evidence_service.update_evidence(evidence_id, updates)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )
    return evidence