"""
Test script to verify project's database models by direct import.
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
print("🔍 Testing Project Database Models")
print("=" * 60)

# Set up test database URL
TEST_DATABASE_URL = "sqlite:///./test_project_models.db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Try to import project models
try:
    print("\n🔍 Importing project modules...")
    from casebuilder.db.base import Base, engine, SessionLocal
    from casebuilder.db.models import (
        User, Case, Evidence, Analysis, Report,
        CaseStatus, EvidenceType, AnalysisStatus, ReportStatus
    )
    print("✅ Successfully imported project models")
    
    # Create all tables
    print("\n🔄 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    # Test database connection
    print("\n🔍 Testing database connection...")
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print(f"✅ Database connection test: {'Success' if result.scalar() == 1 else 'Failed'}")
    
    # Create a test session
    db = SessionLocal()
    
    try:
        # Create a test user
        print("\n🔍 Creating test user...")
        test_user = User(
            id="test-user-123",
            email="test@example.com",
            hashed_password="hashed_password_here",
            full_name="Test User",
            is_active=True,
            is_superuser=False
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        print(f"✅ Created test user with ID: {test_user.id}")
        
        # Create a test case
        print("\n🔍 Creating test case...")
        test_case = Case(
            id="test-case-123",
            title="Test Case",
            description="A test case description",
            status=CaseStatus.OPEN,
            created_by_id=test_user.id
        )
        db.add(test_case)
        db.commit()
        db.refresh(test_case)
        print(f"✅ Created test case with ID: {test_case.id}")
        
        # Create test evidence
        print("\n🔍 Creating test evidence...")
        test_evidence = Evidence(
            id="test-evidence-123",
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
        
        # Create test analysis
        print("\n🔍 Creating test analysis...")
        test_analysis = Analysis(
            id="test-analysis-123",
            evidence_id=test_evidence.id,
            status=AnalysisStatus.PENDING,
            started_by_id=test_user.id,
            started_at=datetime.now(timezone.utc)
        )
        db.add(test_analysis)
        db.commit()
        db.refresh(test_analysis)
        print(f"✅ Created test analysis with ID: {test_analysis.id}")
        
        # Create test report
        print("\n🔍 Creating test report...")
        test_report = Report(
            id="test-report-123",
            case_id=test_case.id,
            title="Test Report",
            status=ReportStatus.DRAFT,
            created_by_id=test_user.id
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
        
        if case.evidence:
            evidence = case.evidence[0]
            print(f"   - First evidence: {evidence.name} (Type: {evidence.evidence_type})")
            print(f"   - Analyses count: {len(evidence.analyses)}")
        
        # Clean up
        print("\n🧹 Cleaning up test database...")
        db.rollback()  # Rollback any pending transactions
        Base.metadata.drop_all(bind=engine)
        print("✅ Test database cleaned up")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        db.rollback()
        raise
    
    finally:
        db.close()
    
    print("\n🏁 All tests completed successfully!")
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("\n🔍 Python path:")
    for i, path in enumerate(sys.path):
        print(f"{i}: {path}")
    
    # Try to locate the casebuilder package
    print("\n🔍 Searching for casebuilder package...")
    import importlib.util
    
    def find_package(pkg_name):
        spec = importlib.util.find_spec(pkg_name)
        if spec is not None:
            print(f"✅ Found {pkg_name} at: {spec.origin}")
            return True
        else:
            print(f"❌ Could not find {pkg_name} in Python path")
            return False
    
    find_package("casebuilder")
    find_package("casebuilder.db")
    find_package("casebuilder.db.models")
    
    # Check if the files exist directly
    print("\n🔍 Checking for module files...")
    def check_file(path):
        full_path = Path(project_root) / path
        exists = full_path.exists()
        print(f"{'✅' if exists else '❌'} {path}: {'Exists' if exists else 'Not found'}")
        return exists
    
    check_file("casebuilder/__init__.py")
    check_file("casebuilder/db/__init__.py")
    check_file("casebuilder/db/base.py")
    check_file("casebuilder/db/models.py")
    
    # Try to import the modules directly
    print("\n🔍 Attempting direct imports...")
    
    def try_import(module_name):
        try:
            module = __import__(module_name, fromlist=[''])
            print(f"✅ Successfully imported {module_name}")
            return module
        except ImportError as ie:
            print(f"❌ Failed to import {module_name}: {ie}")
            return None
    
    try_import("casebuilder")
    try_import("casebuilder.db")
    try_import("casebuilder.db.base")
    try_import("casebuilder.db.models")
    
    print("\n💡 Try running: `python -m pip install -e .` from the project root")
    
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    
    # Try to clean up even if there was an error
    try:
        if 'Base' in locals() and 'engine' in locals():
            Base.metadata.drop_all(bind=engine)
            print("\n✅ Dropped test tables after error")
    except Exception as cleanup_error:
        print(f"\n⚠️ Error during cleanup: {cleanup_error}")
