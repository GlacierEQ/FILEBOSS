"""
Test script to verify database models with SQLite.
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=" * 60)
print("🔍 Testing Database Models with SQLite")
print("=" * 60)

# Set up test database URL
TEST_DATABASE_URL = "sqlite:///./test_fileboss.db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Import SQLAlchemy and models
try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker, Session
    from casebuilder.db.base import Base
    from casebuilder.db.models import (
        User, Case, Evidence, Analysis, Report, 
        CaseStatus, EvidenceType, AnalysisStatus, ReportStatus
    )
    
    print("✅ Successfully imported database modules")
    
    # Create test database engine and session
    engine = create_engine(TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    print("\n🔄 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    # Test database connection
    print("\n🔍 Testing database connection...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print(f"✅ Database connection test: {'Success' if result.scalar() == 1 else 'Failed'}")
    
    # Create a test session
    db = TestingSessionLocal()
    
    try:
        # Test User model
        print("\n🔍 Testing User model...")
        test_user = User(
            email="test@example.com",
            hashed_password="hashed_password_here",  # In a real app, hash the password
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ Created test user with ID: {test_user.id}")
        
        # Test Case model
        print("\n🔍 Testing Case model...")
        test_case = Case(
            title="Test Case",
            description="A test case description",
            status=CaseStatus.OPEN,
            created_by_id=test_user.id
        )
        db.add(test_case)
        db.commit()
        db.refresh(test_case)
        print(f"✅ Created test case with ID: {test_case.id}")
        
        # Test Evidence model
        print("\n🔍 Testing Evidence model...")
        test_evidence = Evidence(
            case_id=test_case.id,
            name="Test Evidence",
            evidence_type=EvidenceType.DOCUMENT,
            source="Test Source",
            collected_by_id=test_user.id,
            collection_date=datetime.now(timezone.utc)
        )
        db.add(test_evidence)
        db.commit()
        db.refresh(test_evidence)
        print(f"✅ Created test evidence with ID: {test_evidence.id}")
        
        # Test Analysis model
        print("\n🔍 Testing Analysis model...")
        test_analysis = Analysis(
            evidence_id=test_evidence.id,
            status=AnalysisStatus.PENDING,
            started_by_id=test_user.id,
            started_at=datetime.now(timezone.utc)
        )
        db.add(test_analysis)
        db.commit()
        db.refresh(test_analysis)
        print(f"✅ Created test analysis with ID: {test_analysis.id}")
        
        # Test Report model
        print("\n🔍 Testing Report model...")
        test_report = Report(
            case_id=test_case.id,
            title="Test Report",
            status=ReportStatus.DRAFT,
            created_by_id=test_user.id,
            created_at=datetime.now(timezone.utc)
        )
        db.add(test_report)
        db.commit()
        db.refresh(test_report)
        print(f"✅ Created test report with ID: {test_report.id}")
        
        # Query test data
        print("\n🔍 Querying test data...")
        case = db.query(Case).filter(Case.id == test_case.id).first()
        print(f"✅ Queried case: {case.title} (ID: {case.id})")
        print(f"   - Evidence count: {len(case.evidence)}")
        print(f"   - Reports count: {len(case.reports)}")
        
    except Exception as e:
        print(f"❌ Error during model testing: {e}")
        db.rollback()
        raise
    
    finally:
        # Clean up (drop all tables)
        print("\n🧹 Cleaning up test database...")
        Base.metadata.drop_all(bind=engine)
        print("✅ Test database cleaned up")
        db.close()
    
    print("\n🏁 All tests completed successfully!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    
    # Try to clean up even if there was an error
    try:
        if 'Base' in locals() and 'engine' in locals():
            Base.metadata.drop_all(bind=engine)
            print("\n✅ Dropped test tables after error")
    except Exception as cleanup_error:
        print(f"\n⚠️ Error during cleanup: {cleanup_error}")
