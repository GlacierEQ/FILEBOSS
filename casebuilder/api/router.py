# casebuilder/api/router.py - All API routes for the application

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Any

# Import our database dependency and models
from casebuilder.database import get_db
from casebuilder.models import Evidence, EvidenceCreate, EvidenceRead

router = APIRouter()

@router.post("/evidence/", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
async def create_evidence(
    evidence: EvidenceCreate,
    db: AsyncSession = Depends(get_db)
) -> Evidence:
    """Create a new evidence record."""
    db_evidence = Evidence(filename=evidence.filename, description=evidence.description, case_id=evidence.case_id)
    db.add(db_evidence)
    await db.commit()
    await db.refresh(db_evidence)
    return db_evidence

@router.get("/evidence/{case_id}", response_model=List[EvidenceRead])
async def get_evidence_for_case(
    case_id: str,
    db: AsyncSession = Depends(get_db)
) -> List[Evidence]:
    """Get all evidence for a specific case."""
    result = await db.execute(Evidence.__table__.select().where(Evidence.case_id == case_id))
    return result.fetchall()
