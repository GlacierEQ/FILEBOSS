"""
Test script for EvidenceProcessingService.

This script demonstrates how to use the EvidenceProcessingService to process evidence files,
organize them, and integrate with the timeline system.
"""
import asyncio
import logging
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from casebuilder.services.evidence_processing import EvidenceProcessingService
from casebuilder.db.repositories.evidence import EvidenceRepositoryAsync
from casebuilder.db.repositories.timeline import TimelineEventRepositoryAsync
from casebuilder.db.models import Base, Evidence, TimelineEvent, EvidenceType, EvidenceStatus, TimelineEventType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
TEST_DB_URL = "sqlite+aiosqlite:///./test_evidence_processing.db"
TEST_FILES_DIR = Path("test_files")
TEST_OUTPUT_DIR = Path("test_output")

# Sample test data
SAMPLE_CASE_ID = "test-case-123"
SAMPLE_USER_ID = "test-user-456"

# Create test files
def setup_test_files():
    """Create sample test files."""
    # Create test directories
    test_dirs = ["documents", "images", "data"]
    
    # Clean up any existing test files
    if TEST_FILES_DIR.exists():
        shutil.rmtree(TEST_FILES_DIR)
    
    TEST_FILES_DIR.mkdir(exist_ok=True)
    
    # Create sample files
    for dir_name in test_dirs:
        dir_path = TEST_FILES_DIR / dir_name
        dir_path.mkdir()
        
        # Create a few sample files in each directory
        for i in range(3):
            file_path = dir_path / f"{dir_name}_file_{i+1}.txt"
            with open(file_path, "w") as f:
                f.write(f"This is a test file: {file_path.name}")

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def db_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DB_URL, echo=True)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Clean up
    await engine.dispose()
    if os.path.exists("./test_evidence_processing.db"):
        os.remove("./test_evidence_processing.db")

@pytest.fixture(scope="function")
async def db_session(db_engine):
    """Create a test database session."""
    async with AsyncSession(db_engine) as session:
        await session.begin()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

@pytest.fixture(scope="function")
def evidence_service(db_session):
    """Create an EvidenceProcessingService instance."""
    return EvidenceProcessingService(db_session)

@pytest.mark.skip(reason="EvidenceProcessingService does not have process_evidence_directory method yet.")
@pytest.mark.asyncio
async def test_process_evidence_directory(evidence_service, db_session):
    """Test processing a directory of evidence files."""
    # Setup test files
    setup_test_files()
    
    # Process the test directory
    evidence_list = await evidence_service.process_evidence_directory(
        directory=TEST_FILES_DIR,
        case_id=SAMPLE_CASE_ID,
        evidence_type=EvidenceType.DOCUMENT,
        description="Test evidence processing",
        tags=["test", "automated"],
        created_by=SAMPLE_USER_ID
    )
    
    # Verify results
    assert len(evidence_list) > 0
    
    # Check that evidence records were created
    evidence_repo = EvidenceRepositoryAsync(db_session)
    all_evidence = await evidence_repo.get_by_case(SAMPLE_CASE_ID)
    assert len(all_evidence) == len(evidence_list)
    
    # Check that timeline events were created
    timeline_repo = TimelineEventRepositoryAsync(db_session)
    timeline_events = await timeline_repo.get_timeline_for_case(
        case_id=SAMPLE_CASE_ID,
        event_types=[TimelineEventType.EVIDENCE_ADDED]
    )
    assert len(timeline_events) == len(evidence_list)
    
    logger.info(f"Successfully processed {len(evidence_list)} evidence files")

@pytest.mark.skip(reason="EvidenceProcessingService does not have organize_evidence_files method yet.")
@pytest.mark.asyncio
async def test_organize_evidence_files(evidence_service, db_session):
    """Test organizing evidence files."""
    # Create some test evidence records
    evidence_repo = EvidenceRepositoryAsync(db_session)
    evidence_ids = []
    
    for i in range(3):
        evidence = await evidence_repo.create({
            "case_id": SAMPLE_CASE_ID,
            "title": f"Test Evidence {i+1}",
            "description": f"Test evidence file {i+1}",
            "evidence_type": EvidenceType.DOCUMENT,
            "status": EvidenceStatus.PENDING_REVIEW,
            "file_path": f"/path/to/test_file_{i+1}.txt",
            "file_size": 1024 * (i + 1),
            "file_type": "text/plain",
            "created_by": SAMPLE_USER_ID
        })
        evidence_ids.append(evidence.id)
    
    # Create output directory
    if TEST_OUTPUT_DIR.exists():
        shutil.rmtree(TEST_OUTPUT_DIR)
    TEST_OUTPUT_DIR.mkdir()
    
    # Organize the files
    results = await evidence_service.organize_evidence_files(
        evidence_ids=evidence_ids,
        output_dir=TEST_OUTPUT_DIR,
        organization_scheme="type_date"
    )
    
    # Verify results
    assert len(results) == len(evidence_ids)
    for result in results:
        assert "original_path" in result
        assert "new_path" in result
        assert TEST_OUTPUT_DIR.name in result["new_path"]
    
    logger.info(f"Successfully organized {len(results)} evidence files")

@pytest.mark.skip(reason="EvidenceProcessingService does not have update_evidence_status method yet.")
@pytest.mark.asyncio
async def test_update_evidence_status(evidence_service, db_session):
    """Test updating evidence status."""
    # Create a test evidence record
    evidence_repo = EvidenceRepositoryAsync(db_session)
    evidence = await evidence_repo.create({
        "case_id": SAMPLE_CASE_ID,
        "title": "Status Test Evidence",
        "description": "Test evidence for status updates",
        "evidence_type": EvidenceType.DOCUMENT,
        "status": EvidenceStatus.PENDING_REVIEW,
        "file_path": "/path/to/status_test.txt",
        "file_size": 1024,
        "file_type": "text/plain",
        "created_by": SAMPLE_USER_ID
    })
    
    # Update the status
    updated_evidence = await evidence_service.update_evidence_status(
        evidence_id=evidence.id,
        new_status=EvidenceStatus.UNDER_REVIEW,
        user_id=SAMPLE_USER_ID,
        notes="Moving to review status"
    )
    
    # Verify the update
    assert updated_evidence is not None
    assert updated_evidence.status == EvidenceStatus.UNDER_REVIEW
    
    # Check that a custody event was created
    custody_events = updated_evidence.chain_of_custody or []
    assert len(custody_events) > 0
    assert any("STATUS_CHANGED" in event.get("action", "") for event in custody_events)
    
    # Check that a timeline event was created
    timeline_repo = TimelineEventRepositoryAsync(db_session)
    timeline_events = await timeline_repo.get_timeline_for_case(
        case_id=SAMPLE_CASE_ID,
        event_types=[TimelineEventType.EVIDENCE_STATUS_CHANGED]
    )
    assert len(timeline_events) > 0
    assert any(ev.metadata.get("evidence_id") == str(evidence.id) for ev in timeline_events)
    
    logger.info(f"Successfully updated evidence status to {updated_evidence.status}")

@pytest.mark.skip(reason="EvidenceProcessingService does not have link_evidence_to_timeline method yet.")
@pytest.mark.asyncio
async def test_link_evidence_to_timeline(evidence_service, db_session):
    """Test linking evidence to a timeline event."""
    # Create a test evidence record
    evidence_repo = EvidenceRepositoryAsync(db_session)
    evidence = await evidence_repo.create({
        "case_id": SAMPLE_CASE_ID,
        "title": "Timeline Test Evidence",
        "description": "Test evidence for timeline linking",
        "evidence_type": EvidenceType.DOCUMENT,
        "status": EvidenceStatus.PENDING_REVIEW,
        "file_path": "/path/to/timeline_test.txt",
        "file_size": 1024,
        "file_type": "text/plain",
        "created_by": SAMPLE_USER_ID
    })
    
    # Create a test timeline event
    timeline_repo = TimelineEventRepositoryAsync(db_session)
    timeline_event = await timeline_repo.create({
        "case_id": SAMPLE_CASE_ID,
        "event_type": TimelineEventType.INVESTIGATION_NOTE,
        "title": "Test Investigation Note",
        "description": "A test note for evidence linking",
        "created_by": SAMPLE_USER_ID,
        "metadata": {"note": "This is a test note"}
    })
    
    # Link the evidence to the timeline event
    result = await evidence_service.link_evidence_to_timeline(
        evidence_id=evidence.id,
        timeline_event_id=timeline_event.id,
        user_id=SAMPLE_USER_ID
    )
    
    # Verify the link was created
    assert result is True
    
    # Check that the evidence is linked to the timeline event
    timeline_event = await timeline_repo.get_with_related(timeline_event.id, load_evidence=True)
    assert any(ev.id == evidence.id for ev in timeline_event.evidence)
    
    # Check that a custody event was created
    evidence = await evidence_repo.get(evidence.id)
    custody_events = evidence.chain_of_custody or []
    assert any("LINKED_TO_TIMELINE_EVENT" in event.get("action", "") for event in custody_events)
    
    logger.info(f"Successfully linked evidence {evidence.id} to timeline event {timeline_event.id}")

async def main():
    """Run the test script."""
    # Create test database engine
    engine = create_async_engine(TEST_DB_URL, echo=True)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create a session
    async with AsyncSession(engine) as session:
        # Create the service
        service = EvidenceProcessingService(session)
        
        # Run the tests
        print("\n=== Testing process_evidence_directory ===")
        await test_process_evidence_directory(service, session)
        
        print("\n=== Testing organize_evidence_files ===")
        await test_organize_evidence_files(service, session)
        
        print("\n=== Testing update_evidence_status ===")
        await test_update_evidence_status(service, session)
        
        print("\n=== Testing link_evidence_to_timeline ===")
        await test_link_evidence_to_timeline(service, session)
    
    # Clean up
    await engine.dispose()
    if os.path.exists("./test_evidence_processing.db"):
        os.remove("./test_evidence_processing.db")
    if TEST_OUTPUT_DIR.exists():
        shutil.rmtree(TEST_OUTPUT_DIR)
    if TEST_FILES_DIR.exists():
        shutil.rmtree(TEST_FILES_DIR)

if __name__ == "__main__":
    asyncio.run(main())
