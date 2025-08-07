# 👨‍💻 Development Guide

Complete development guide for contributing to and extending the CaseBuilder evidence management system.

## 🏗️ Development Environment Setup

### Prerequisites
- Python 3.11+
- Git
- Docker (optional)
- IDE/Editor (VS Code recommended)

### Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd casebuilder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Install pre-commit hooks
pre-commit install

# Run initial tests
python test_casebuilder_verification.py
```

### Development Dependencies
```txt
# requirements-dev.txt
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
black>=23.11.0
flake8>=6.1.0
mypy>=1.7.0
pre-commit>=3.5.0
isort>=5.12.0
bandit>=1.7.5
```

---

## 🏛️ Project Architecture

### Directory Structure
```
casebuilder/
├── main.py                          # Application entry point
├── requirements.txt                 # Production dependencies
├── requirements-dev.txt             # Development dependencies
├── Dockerfile                       # Container configuration
├── docker-compose.yml              # Local development stack
├── .pre-commit-config.yaml         # Code quality hooks
├── pytest.ini                      # Test configuration
├── mypy.ini                        # Type checking configuration
├── .gitignore                       # Git ignore rules
├── casebuilder/                     # Main application package
│   ├── __init__.py
│   ├── api/                         # API layer
│   │   ├── __init__.py
│   │   └── endpoints/               # API endpoints
│   │       ├── __init__.py
│   │       └── evidence.py          # Evidence endpoints
│   ├── core/                        # Core functionality
│   │   ├── __init__.py
│   │   ├── config.py                # Configuration management
│   │   └── security.py             # Security utilities
│   ├── db/                          # Database layer
│   │   ├── __init__.py
│   │   ���── base.py                  # Database configuration
│   │   └── models.py                # Database models
│   ├── services/                    # Business logic layer
│   │   ├── __init__.py
│   │   └── evidence_processing.py   # Evidence processing service
│   └── schemas/                     # Pydantic schemas
│       ├── __init__.py
│       └── evidence.py              # Evidence schemas
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                  # Test configuration
│   ├── test_api/                    # API tests
│   ├── test_services/               # Service tests
│   └── test_db/                     # Database tests
└── docs/                            # Documentation
    ├── README.md
    ├── api-reference.md
    ├── deployment.md
    └── development.md
```

### Architecture Principles

1. **Layered Architecture**: Clear separation between API, business logic, and data layers
2. **Dependency Injection**: Services are injected through FastAPI's dependency system
3. **Async/Await**: Full async support for database operations and I/O
4. **Type Safety**: 100% type annotations with MyPy validation
5. **Configuration Management**: Environment-based configuration with Pydantic
6. **Error Handling**: Comprehensive error handling with proper HTTP status codes

---

## 🔧 Development Workflow

### Code Style and Quality

#### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
```

#### Code Formatting
```bash
# Format code with Black
black casebuilder/ tests/

# Sort imports with isort
isort casebuilder/ tests/

# Check code style with flake8
flake8 casebuilder/ tests/

# Type checking with MyPy
mypy casebuilder/
```

### Testing Strategy

#### Test Configuration
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --cov=casebuilder
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=90
asyncio_mode = auto
```

#### Test Structure
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from casebuilder.db.base import Base, get_async_db
from main import app

# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest.fixture
def client(db_session):
    def override_get_db():
        return db_session
    
    app.dependency_overrides[get_async_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
```

#### Writing Tests
```python
# tests/test_api/test_evidence.py
import pytest
from fastapi.testclient import TestClient

class TestEvidenceAPI:
    def test_upload_evidence(self, client: TestClient):
        """Test evidence file upload."""
        with open("test_file.txt", "w") as f:
            f.write("test content")
        
        with open("test_file.txt", "rb") as f:
            response = client.post(
                "/api/v1/evidence/upload/",
                files={"file": ("test.txt", f, "text/plain")},
                data={"case_id": "test_case", "description": "Test file"}
            )
        
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["case_id"] == "test_case"

    def test_get_evidence(self, client: TestClient):
        """Test evidence retrieval."""
        response = client.get("/api/v1/evidence/1")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "filename" in data

    def test_get_nonexistent_evidence(self, client: TestClient):
        """Test 404 for nonexistent evidence."""
        response = client.get("/api/v1/evidence/999")
        assert response.status_code == 404
```

#### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=casebuilder --cov-report=html

# Run specific test file
pytest tests/test_api/test_evidence.py

# Run specific test
pytest tests/test_api/test_evidence.py::TestEvidenceAPI::test_upload_evidence

# Run tests in parallel
pytest -n auto
```

---

## 🔨 Adding New Features

### Adding a New API Endpoint

1. **Define Pydantic Schema**
```python
# casebuilder/schemas/case.py
from pydantic import BaseModel
from typing import Optional

class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "open"

class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class Case(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: str
    
    class Config:
        from_attributes = True
```

2. **Create Database Model**
```python
# casebuilder/db/models.py
from sqlalchemy import Column, Integer, String, Text
from casebuilder.db.base import Base

class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default="open")
```

3. **Create Service Layer**
```python
# casebuilder/services/case_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from casebuilder.db.models import Case
from casebuilder.schemas.case import CaseCreate, CaseUpdate

class CaseService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_case(self, case_data: CaseCreate) -> Case:
        case = Case(**case_data.dict())
        self.db.add(case)
        await self.db.commit()
        await self.db.refresh(case)
        return case
    
    async def get_case(self, case_id: int) -> Optional[Case]:
        result = await self.db.execute(select(Case).where(Case.id == case_id))
        return result.scalar_one_or_none()
    
    async def list_cases(self, skip: int = 0, limit: int = 100) -> List[Case]:
        result = await self.db.execute(select(Case).offset(skip).limit(limit))
        return result.scalars().all()
```

4. **Create API Endpoints**
```python
# casebuilder/api/endpoints/case.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from casebuilder.db.base import get_async_db
from casebuilder.schemas.case import Case, CaseCreate, CaseUpdate
from casebuilder.services.case_service import CaseService

router = APIRouter()

def get_case_service(db: AsyncSession = Depends(get_async_db)) -> CaseService:
    return CaseService(db)

@router.post("/", response_model=Case, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_data: CaseCreate,
    case_service: CaseService = Depends(get_case_service)
) -> Case:
    return await case_service.create_case(case_data)

@router.get("/{case_id}", response_model=Case)
async def get_case(
    case_id: int,
    case_service: CaseService = Depends(get_case_service)
) -> Case:
    case = await case_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case

@router.get("/", response_model=List[Case])
async def list_cases(
    skip: int = 0,
    limit: int = 100,
    case_service: CaseService = Depends(get_case_service)
) -> List[Case]:
    return await case_service.list_cases(skip=skip, limit=limit)
```

5. **Register Router**
```python
# main.py
from casebuilder.api.endpoints.case import router as case_router

app.include_router(
    case_router,
    prefix=f"{settings.API_V1_STR}/cases",
    tags=["cases"]
)
```

6. **Write Tests**
```python
# tests/test_api/test_case.py
def test_create_case(client):
    response = client.post(
        "/api/v1/cases/",
        json={"title": "Test Case", "description": "Test description"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Case"
```

### Database Migrations

For production applications, implement proper database migrations:

```python
# migrations/env.py
from alembic import context
from sqlalchemy import engine_from_config, pool
from casebuilder.db.base import Base
from casebuilder.db.models import *  # Import all models

target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        context.config.get_section(context.config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()
```

---

## 🐛 Debugging

### Logging Configuration
```python
# casebuilder/core/logging.py
import logging
import sys
from casebuilder.core.config import settings

def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("app.log") if not settings.DEBUG else logging.NullHandler()
        ]
    )
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

### Debug Mode
```python
# main.py
if settings.DEBUG:
    import debugpy
    debugpy.listen(("0.0.0.0", 5678))
    print("Waiting for debugger attach...")
    debugpy.wait_for_client()
```

### Performance Profiling
```python
# profiling.py
import cProfile
import pstats
from functools import wraps

def profile(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        result = func(*args, **kwargs)
        pr.disable()
        
        stats = pstats.Stats(pr)
        stats.sort_stats('cumulative')
        stats.print_stats(10)
        
        return result
    return wrapper

# Usage
@profile
async def slow_function():
    # Function to profile
    pass
```

---

## 📊 Monitoring and Observability

### Application Metrics
```python
# casebuilder/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Active database connections')

class MetricsMiddleware:
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            start_time = time.time()
            
            # Process request
            await self.app(scope, receive, send)
            
            # Record metrics
            duration = time.time() - start_time
            REQUEST_DURATION.observe(duration)
            REQUEST_COUNT.labels(
                method=scope["method"],
                endpoint=scope["path"],
                status="200"  # Simplified
            ).inc()
```

### Health Checks
```python
# casebuilder/api/endpoints/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from casebuilder.db.base import get_async_db

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_async_db)):
    checks = {
        "database": await check_database(db),
        "disk_space": await check_disk_space(),
        "memory": await check_memory_usage()
    }
    
    overall_status = "healthy" if all(checks.values()) else "unhealthy"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.utcnow()
    }
```

---

## 🔒 Security Best Practices

### Input Validation
```python
# casebuilder/core/validation.py
from pydantic import validator
import re

class EvidenceCreate(BaseModel):
    filename: str
    case_id: str
    
    @validator('filename')
    def validate_filename(cls, v):
        # Prevent path traversal
        if '..' in v or '/' in v or '\\' in v:
            raise ValueError('Invalid filename')
        return v
    
    @validator('case_id')
    def validate_case_id(cls, v):
        # Only alphanumeric and hyphens
        if not re.match(r'^[a-zA-Z0-9-]+$', v):
            raise ValueError('Invalid case ID format')
        return v
```

### Authentication Middleware
```python
# casebuilder/core/auth.py
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

---

## 📚 Documentation

### API Documentation
FastAPI automatically generates OpenAPI documentation. Enhance it with:

```python
@router.post(
    "/upload/",
    response_model=EvidenceSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Evidence File",
    description="Upload a new evidence file to the system with metadata",
    responses={
        201: {"description": "Evidence uploaded successfully"},
        400: {"description": "Invalid file or parameters"},
        413: {"description": "File too large"},
        415: {"description": "Unsupported file type"}
    }
)
async def upload_evidence(
    file: UploadFile = File(..., description="Evidence file to upload"),
    case_id: str = Form(..., description="Case identifier"),
    description: Optional[str] = Form(None, description="Evidence description")
):
    """
    Upload a new evidence file with the following features:
    
    - **File validation**: Checks file type and size
    - **Metadata extraction**: Extracts file metadata
    - **Secure storage**: Stores file securely with access controls
    - **Audit logging**: Logs all upload activities
    """
    pass
```

### Code Documentation
```python
class EvidenceService:
    """
    Service class for evidence management operations.
    
    This service handles all business logic related to evidence processing,
    including file uploads, metadata extraction, and database operations.
    
    Attributes:
        db: Async database session for data operations
        
    Example:
        >>> service = EvidenceService(db_session)
        >>> evidence = await service.create_evidence(file, case_id="case_001")
    """
    
    async def create_evidence(
        self, 
        file: UploadFile, 
        case_id: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new evidence record from uploaded file.
        
        Args:
            file: The uploaded file object
            case_id: Unique identifier for the case
            description: Optional description of the evidence
            
        Returns:
            Dictionary containing evidence metadata and ID
            
        Raises:
            ValueError: If file validation fails
            DatabaseError: If database operation fails
            
        Example:
            >>> evidence = await service.create_evidence(
            ...     file=uploaded_file,
            ...     case_id="case_001",
            ...     description="Contract document"
            ... )
        """
        pass
```

---

## 🚀 Performance Optimization

### Database Optimization
```python
# Efficient queries
async def get_evidence_with_case(evidence_id: int):
    result = await db.execute(
        select(Evidence)
        .options(selectinload(Evidence.case))
        .where(Evidence.id == evidence_id)
    )
    return result.scalar_one_or_none()

# Batch operations
async def create_multiple_evidence(evidence_list: List[EvidenceCreate]):
    evidence_objects = [Evidence(**evidence.dict()) for evidence in evidence_list]
    db.add_all(evidence_objects)
    await db.commit()
    return evidence_objects
```

### Caching
```python
# Redis caching
from redis import asyncio as aioredis
import json

class CacheService:
    def __init__(self):
        self.redis = aioredis.from_url("redis://localhost")
    
    async def get(self, key: str):
        value = await self.redis.get(key)
        return json.loads(value) if value else None
    
    async def set(self, key: str, value: dict, expire: int = 3600):
        await self.redis.set(key, json.dumps(value), ex=expire)
```

### Async Optimization
```python
# Concurrent operations
import asyncio

async def process_multiple_files(files: List[UploadFile]):
    tasks = [process_single_file(file) for file in files]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

---

## 🤝 Contributing Guidelines

### Pull Request Process

1. **Fork and Clone**
   ```bash
   git fork <repository-url>
   git clone <your-fork-url>
   cd casebuilder
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Follow code style guidelines
   - Add tests for new functionality
   - Update documentation

4. **Run Quality Checks**
   ```bash
   # Format code
   black casebuilder/ tests/
   isort casebuilder/ tests/
   
   # Run tests
   pytest --cov=casebuilder
   
   # Type checking
   mypy casebuilder/
   
   # Security check
   bandit -r casebuilder/
   ```

5. **Commit and Push**
   ```bash
   git add .
   git commit -m "feat: add new evidence search functionality"
   git push origin feature/your-feature-name
   ```

6. **Create Pull Request**
   - Provide clear description
   - Link related issues
   - Include test results

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New functionality has tests
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance impact considered
- [ ] Backward compatibility maintained

---

**Development guide complete! Ready to build amazing features.**

Next: [Architecture Overview](architecture.md)