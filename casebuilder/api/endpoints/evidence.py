"""Evidence API endpoints for the CaseBuilder application."""

from typing import Any, Dict, List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from casebuilder.db.base import get_async_db
from casebuilder.models import Evidence, EvidenceRead

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
    ) -> Evidence:
        """Create a new evidence record."""
        db_evidence = Evidence(
            filename=file.filename,
            description=description or file.filename,
            case_id=case_id,
        )
        self.db.add(db_evidence)
        await self.db.commit()
        await self.db.refresh(db_evidence)
        return db_evidence

    async def get_evidence(self, evidence_id: int) -> Optional[Evidence]:
        """Get evidence by ID."""
        return await self.db.get(Evidence, evidence_id)

    async def update_evidence(
        self, evidence_id: int, updates: Dict[str, Any]
    ) -> Optional[Evidence]:
        """Update evidence record."""
        evidence = await self.get_evidence(evidence_id)
        if evidence:
            for key, value in updates.items():
                setattr(evidence, key, value)
            await self.db.commit()
            await self.db.refresh(evidence)
            return evidence
        return None


def get_evidence_service(
    db: AsyncSession = Depends(get_async_db),
) -> EvidenceService:
    """Get evidence service instance."""
    return EvidenceService(db)


@router.post(
    "/upload/",
    response_model=EvidenceRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_evidence(
    file: UploadFile = File(...),
    case_id: str = Form("default_case"),
    description: Optional[str] = Form(None),
    tags: Optional[List[str]] = Form(None),
    evidence_service: EvidenceService = Depends(get_evidence_service),
) -> Evidence:
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


@router.get("/{evidence_id}", response_model=EvidenceRead)
async def get_evidence(
    evidence_id: int,
    evidence_service: EvidenceService = Depends(get_evidence_service),
) -> Evidence:
    """Get evidence by ID."""
    evidence = await evidence_service.get_evidence(evidence_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )
    return evidence


@router.put("/{evidence_id}", response_model=EvidenceRead)
async def update_evidence(
    evidence_id: int,
    updates: Dict[str, Any],
    evidence_service: EvidenceService = Depends(get_evidence_service),
) -> Evidence:
    """Update evidence record."""
    evidence = await evidence_service.update_evidence(evidence_id, updates)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found",
        )
    return evidence
