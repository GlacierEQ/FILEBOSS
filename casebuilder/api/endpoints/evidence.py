"""
Evidence API Endpoints

This module provides API endpoints for evidence processing and management.
"""
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from ....db.session import get_db
from ....models import Evidence, EvidenceType, EvidenceStatus
from ....schemas.evidence import EvidenceCreate, EvidenceUpdate, EvidenceInDB
from ....schemas.timeline import TimelineEventCreate
from ....services.evidence_processing import EvidenceProcessingService
from ....core.security import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Dependency to get the evidence processing service
def get_evidence_service(
    db: AsyncSession = Depends(get_db)
) -> EvidenceProcessingService:
    """Get an instance of the evidence processing service."""
    return EvidenceProcessingService(db)

@router.post("/process-directory/", response_model=List[EvidenceInDB])
async def process_evidence_directory(
    directory: str,
    case_id: str,
    evidence_type: EvidenceType,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_active_user),
    evidence_service: EvidenceProcessingService = Depends(get_evidence_service)
):
    """
    Process all files in a directory and create evidence records.
    
    - **directory**: Path to the directory containing evidence files
    - **case_id**: ID of the case to associate with the evidence
    - **evidence_type**: Type of evidence (document, image, etc.)
    - **description**: Optional description for the evidence
    - **tags**: Optional list of tags for the evidence
    """
    try:
        # Process the directory
        evidence_list = await evidence_service.process_evidence_directory(
            directory=directory,
            case_id=case_id,
            evidence_type=evidence_type,
            description=description,
            tags=tags,
            created_by=current_user.id
        )
        
        return evidence_list
        
    except Exception as e:
        logger.error(f"Error processing directory {directory}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing directory: {str(e)}"
        )

@router.post("/upload/", response_model=EvidenceInDB)
async def upload_evidence(
    file: UploadFile = File(...),
    case_id: str = None,
    evidence_type: EvidenceType = EvidenceType.DOCUMENT,
    description: str = None,
    tags: List[str] = None,
    current_user: dict = Depends(get_current_active_user),
    evidence_service: EvidenceProcessingService = Depends(get_evidence_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a single file as evidence.
    
    - **file**: The file to upload
    - **case_id**: ID of the case to associate with the evidence
    - **evidence_type**: Type of evidence (document, image, etc.)
    - **description**: Optional description for the evidence
    - **tags**: Optional list of tags for the evidence
    """
    try:
        # Create a temporary directory for uploads if it doesn't exist
        upload_dir = Path("uploads") / str(case_id or "temp")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the uploaded file
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Process the file
        evidence_list = await evidence_service.process_evidence_directory(
            directory=str(file_path.parent),
            case_id=case_id,
            evidence_type=evidence_type,
            description=description or f"Uploaded file: {file.filename}",
            tags=tags or [],
            created_by=current_user.id
        )
        
        if not evidence_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process uploaded file"
            )
        
        return evidence_list[0]
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

@router.get("/{evidence_id}", response_model=EvidenceInDB)
async def get_evidence(
    evidence_id: str,
    current_user: dict = Depends(get_current_active_user),
    evidence_service: EvidenceProcessingService = Depends(get_evidence_service)
):
    """
    Get an evidence item by ID.
    
    - **evidence_id**: ID of the evidence to retrieve
    """
    evidence = await evidence_service.evidence_repo.get(evidence_id)
    if not evidence:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence not found"
        )
    return evidence

@router.put("/{evidence_id}/status/", response_model=EvidenceInDB)
async def update_evidence_status(
    evidence_id: str,
    new_status: EvidenceStatus,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_active_user),
    evidence_service: EvidenceProcessingService = Depends(get_evidence_service)
):
    """
    Update the status of an evidence item.
    
    - **evidence_id**: ID of the evidence to update
    - **new_status**: New status to set
    - **notes**: Optional notes about the status change
    """
    try:
        evidence = await evidence_service.update_evidence_status(
            evidence_id=evidence_id,
            new_status=new_status,
            user_id=current_user.id,
            notes=notes
        )
        
        if not evidence:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )
            
        return evidence
        
    except Exception as e:
        logger.error(f"Error updating evidence status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating evidence status: {str(e)}"
        )

@router.post("/{evidence_id}/link-timeline/{timeline_event_id}", status_code=status.HTTP_200_OK)
async def link_evidence_to_timeline(
    evidence_id: str,
    timeline_event_id: str,
    current_user: dict = Depends(get_current_active_user),
    evidence_service: EvidenceProcessingService = Depends(get_evidence_service)
):
    """
    Link an evidence item to a timeline event.
    
    - **evidence_id**: ID of the evidence to link
    - **timeline_event_id**: ID of the timeline event to link to
    """
    try:
        result = await evidence_service.link_evidence_to_timeline(
            evidence_id=evidence_id,
            timeline_event_id=timeline_event_id,
            user_id=current_user.id
        )
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to link evidence to timeline event"
            )
            
        return {"status": "success", "message": "Evidence linked to timeline event"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking evidence to timeline: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error linking evidence to timeline: {str(e)}"
        )

@router.post("/organize/", response_model=List[dict])
async def organize_evidence_files(
    evidence_ids: List[str],
    output_dir: str,
    organization_scheme: str = "type_date",
    current_user: dict = Depends(get_current_active_user),
    evidence_service: EvidenceProcessingService = Depends(get_evidence_service)
):
    """
    Organize evidence files according to the specified scheme.
    
    - **evidence_ids**: List of evidence IDs to organize
    - **output_dir**: Base directory for organized files
    - **organization_scheme**: Scheme to use for organization
        - 'type_date': Organize by file type and date
        - 'type': Organize by file type only
        - 'date': Organize by date only
        - 'flat': All files in a single directory
    """
    try:
        results = await evidence_service.organize_evidence_files(
            evidence_ids=evidence_ids,
            output_dir=output_dir,
            organization_scheme=organization_scheme
        )
        
        return results
        
    except Exception as e:
        logger.error(f"Error organizing evidence files: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error organizing evidence files: {str(e)}"
        )

@router.get("/case/{case_id}", response_model=List[EvidenceInDB])
async def get_evidence_by_case(
    case_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_active_user),
    evidence_service: EvidenceProcessingService = Depends(get_evidence_service)
):
    """
    Get all evidence items for a case.
    
    - **case_id**: ID of the case
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (for pagination)
    """
    try:
        evidence = await evidence_service.evidence_repo.get_by_case(
            case_id=case_id,
            skip=skip,
            limit=limit
        )
        
        return evidence
        
    except Exception as e:
        logger.error(f"Error getting evidence for case {case_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting evidence for case: {str(e)}"
        )
