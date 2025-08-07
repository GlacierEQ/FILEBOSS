"""
Simplified test script for database models.
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
print("🔍 Testing Database Models (Simplified)")
print("=" * 60)

# Set up test database URL
TEST_DATABASE_URL = "sqlite:///./test_models.db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Import SQLAlchemy
try:
    from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Enum, Text, Boolean
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship, sessionmaker, Session
    import enum
    
    print("✅ Successfully imported SQLAlchemy")
    
    # Define enums
    class CaseStatus(str, enum.Enum):
        OPEN = "open"
        IN_PROGRESS = "in_progress"
        CLOSED = "closed"
    
    class EvidenceType(str, enum.Enum):
        DOCUMENT = "document"
        IMAGE = "image"
        VIDEO = "video"
        OTHER = "other"
    
    class AnalysisStatus(str, enum.Enum):
        PENDING = "pending"
        IN_PROGRESS = "in_progress"
        COMPLETED = "completed"
        FAILED = "failed"
    
    class ReportStatus(str, enum.Enum):
        DRAFT = "draft"
        IN_REVIEW = "in_review"
        PUBLISHED = "published"
    
    # Create base class
    Base = declarative_base()
    
    # Define models
    class User(Base):
        __tablename__ = "users"
        
        id = Column(String, primary_key=True, index=True)
        email = Column(String, unique=True, index=True, nullable=False)
        hashed_password = Column(String, nullable=False)
        full_name = Column(String, index=True)
        is_active = Column(Boolean(), default=True)
        is_superuser = Column(Boolean(), default=False)
        
        # Relationships
        cases_created = relationship("Case", back_populates="created_by", foreign_keys="[Case.created_by_id]")
        evidence_collected = relationship("Evidence", back_populates="collected_by", foreign_keys="[Evidence.collected_by_id]")
    
    class Case(Base):
        __tablename__ = "cases"
        
        id = Column(String, primary_key=True, index=True)
        title = Column(String, index=True, nullable=False)
        description = Column(Text)
        status = Column(Enum(CaseStatus), default=CaseStatus.OPEN, nullable=False)
        created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
        updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
        created_by_id = Column(String, ForeignKey("users.id"), nullable=False)
        
        # Relationships
        created_by = relationship("User", back_populates="cases_created", foreign_keys=[created_by_id])
        evidence = relationship("Evidence", back_populates="case")
        reports = relationship("Report", back_populates="case")
    
    class Evidence(Base):
        __tablename__ = "evidence"
        
        id = Column(String, primary_key=True, index=True)
        case_id = Column(String, ForeignKey("cases.id"), nullable=False)
        name = Column(String, index=True, nullable=False)
        description = Column(Text)
        evidence_type = Column(Enum(EvidenceType), nullable=False)
        source = Column(String)
        collected_by_id = Column(String, ForeignKey("users.id"), nullable=False)
        collection_date = Column(DateTime(timezone=True), nullable=False)
        notes = Column(Text)
        
        # Relationships
        case = relationship("Case", back_populates="evidence")
        collected_by = relationship("User", back_populates="evidence_collected", foreign_keys=[collected_by_id])
        analyses = relationship("Analysis", back_populates="evidence")
    
    class Analysis(Base):
        __tablename__ = "analyses"
        
        id = Column(String, primary_key=True, index=True)
        evidence_id = Column(String, ForeignKey("evidence.id"), nullable=False)
        status = Column(Enum(AnalysisStatus), default=AnalysisStatus.PENDING, nullable=False)
        started_at = Column(DateTime(timezone=True), nullable=False)
        completed_at = Column(DateTime(timezone=True))
        started_by_id = Column(String, ForeignKey("users.id"), nullable=False)
        results = Column(Text)
        
        # Relationships
        evidence = relationship("Evidence", back_populates="analyses")
        started_by = relationship("User")
    
    class Report(Base):
        __tablename__ = "reports"
        
        id = Column(String, primary_key=True, index=True)
        case_id = Column(String, ForeignKey("cases.id"), nullable=False)
        title = Column(String, index=True, nullable=False)
        content = Column(Text)
        status = Column(Enum(ReportStatus), default=ReportStatus.DRAFT, nullable=False)
        created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
        updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
        created_by_id = Column(String, ForeignKey("users.id"), nullable=False)
        
        # Relationships
        case = relationship("Case", back_populates="reports")
        created_by = relationship("User")
    
    # Create database engine and tables
    engine = create_engine(TEST_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
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
        print(f"✅ Created test evidence with ID: {test_evidence.id}")
        
        # Query test data
        print("\n🔍 Querying test data...")
        case = db.query(Case).filter(Case.id == test_case.id).first()
        print(f"✅ Queried case: {case.title} (ID: {case.id})")
        print(f"   - Evidence count: {len(case.evidence)}")
        
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
