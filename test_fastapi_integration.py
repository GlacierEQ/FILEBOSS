"""
Test script to verify FastAPI application with project's database models.
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=" * 60)
print("🚀 Testing FastAPI Application with Project Models")
print("=" * 60)

# Set up test database URL
TEST_DATABASE_URL = "sqlite:///./test_fastapi.db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["CORS_ORIGINS"] = "*"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "true"

# Import FastAPI and project modules
try:
    import uvicorn
    from fastapi import FastAPI, Depends, HTTPException
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import Session
    
    from casebuilder.api.app import app
    from casebuilder.db.base import Base, engine, SessionLocal
    from casebuilder.db.models import (
        User, Case, Evidence, Analysis, Report,
        CaseStatus, EvidenceType, AnalysisStatus, ReportStatus
    )
    
    print("✅ Successfully imported project modules")
    
    # Create test database tables
    print("\n🔄 Creating test database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Test database tables created")
    
    # Create a test client
    client = TestClient(app)
    
    # Helper function to get a test database session
    def get_test_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    # Override the get_db dependency for testing
    app.dependency_overrides[app.dependency_overrides.get("get_db")] = get_test_db
    
    # Test data
    test_user_data = {
        "email": "test@example.com",
        "password": "testpassword",
        "full_name": "Test User"
    }
    
    test_case_data = {
        "title": "Test Case",
        "description": "A test case description",
        "status": "open"
    }
    
    # Test endpoints
    print("\n🔍 Testing API endpoints...")
    
    # Test root endpoint
    print("\n🔍 Testing root endpoint...")
    response = client.get("/")
    print(f"GET / -> Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test health check endpoint
    print("\n🔍 Testing health check endpoint...")
    response = client.get("/health")
    print(f"GET /health -> Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Test creating a user
    print("\n🔍 Testing user creation...")
    response = client.post("/api/v1/users/", json=test_user_data)
    print(f"POST /api/v1/users/ -> Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        user_data = response.json()
        user_id = user_data["id"]
        
        # Test getting the user
        print(f"\n🔍 Testing get user (ID: {user_id})...")
        response = client.get(f"/api/v1/users/{user_id}")
        print(f"GET /api/v1/users/{user_id} -> Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        # Test creating a case
        print("\n🔍 Testing case creation...")
        response = client.post(
            "/api/v1/cases/",
            json=test_case_data,
            headers={"Authorization": f"Bearer test-token"}
        )
        print(f"POST /api/v1/cases/ -> Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            case_data = response.json()
            case_id = case_data["id"]
            
            # Test getting the case
            print(f"\n🔍 Testing get case (ID: {case_id})...")
            response = client.get(f"/api/v1/cases/{case_id}")
            print(f"GET /api/v1/cases/{case_id} -> Status: {response.status_code}")
            print(f"Response: {response.json()}")
    
    # Clean up
    print("\n🧹 Cleaning up test database...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Test database cleaned up")
    
    print("\n🏁 All tests completed!")
    
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    
    # Print Python path for debugging
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
    find_package("casebuilder.api")
    find_package("casebuilder.db")
    
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
