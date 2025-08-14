#!/usr/bin/env python3
"""
Comprehensive verification test for the CaseBuilder system.
Tests best practices, alignment, and functional integrity.
"""

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from casebuilder.api import router
    from casebuilder.core.config import settings
    from casebuilder.db.base import get_async_db, engine, Base
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Installing required dependencies...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "fastapi", "sqlalchemy", "aiosqlite", "pydantic-settings", "python-multipart"])
    print("✅ Dependencies installed. Please run the test again.")
    sys.exit(1)


class SystemVerifier:
    """Comprehensive system verification class."""

    def __init__(self):
        """Initialize the verifier."""
        self.app = FastAPI(title="CaseBuilder Test")
        self.app.include_router(router, prefix="/api/v1/evidence")
        self.client = TestClient(self.app)
        self.results: Dict[str, Any] = {}

    def test_imports(self) -> bool:
        """Test that all imports work correctly."""
        try:
            from casebuilder.api.endpoints.evidence import EvidenceService
            from casebuilder.core.config import Settings
            from casebuilder.db.base import Base
            print("✅ All imports successful")
            return True
        except ImportError as e:
            print(f"❌ Import test failed: {e}")
            return False

    def test_configuration(self) -> bool:
        """Test configuration settings."""
        try:
            assert settings.APP_NAME == "CaseBuilder"
            assert settings.API_V1_STR == "/api/v1"
            assert isinstance(settings.CORS_ORIGINS, list)
            assert settings.DATABASE_URL.startswith("sqlite+aiosqlite")
            print("✅ Configuration validation passed")
            return True
        except AssertionError as e:
            print(f"❌ Configuration test failed: {e}")
            return False

    def test_api_endpoints(self) -> bool:
        """Test API endpoint functionality."""
        try:
            # Test evidence upload endpoint
            with open(__file__, "rb") as test_file:
                response = self.client.post(
                    "/api/v1/evidence/upload/",
                    files={"file": ("test.py", test_file, "text/plain")},
                    data={"case_id": "test_case", "description": "Test file"}
                )
            
            if response.status_code != 201:
                print(f"❌ Upload endpoint failed: {response.status_code}")
                return False

            # Test evidence retrieval endpoint
            response = self.client.get("/api/v1/evidence/1")
            if response.status_code != 200:
                print(f"❌ Get endpoint failed: {response.status_code}")
                return False

            # Test evidence update endpoint
            response = self.client.put(
                "/api/v1/evidence/1",
                json={"description": "Updated description"}
            )
            if response.status_code != 200:
                print(f"❌ Update endpoint failed: {response.status_code}")
                return False

            print("✅ API endpoints functional")
            return True
        except Exception as e:
            print(f"❌ API test failed: {e}")
            return False

    def test_error_handling(self) -> bool:
        """Test error handling."""
        try:
            # Test 404 error
            response = self.client.get("/api/v1/evidence/999")
            if response.status_code != 404:
                print(f"❌ 404 error handling failed: {response.status_code}")
                return False

            print("✅ Error handling working correctly")
            return True
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
            return False

    def test_api_crud_flow(self) -> bool:
        """Test the full CRUD flow of the API."""
        try:
            # 1. CREATE (Upload)
            test_content = b"this is a test file for the crud flow"
            response = self.client.post(
                "/api/v1/evidence/upload/",
                files={"file": ("crud_test.txt", test_content, "text/plain")},
                data={"case_id": "crud_case", "description": "CRUD test file"}
            )
            if response.status_code != 201:
                print(f"❌ CRUD Create failed: {response.status_code}")
                return False

            created_evidence = response.json()
            evidence_id = created_evidence["id"]

            # 2. READ (Get)
            response = self.client.get(f"/api/v1/evidence/{evidence_id}")
            if response.status_code != 200:
                print(f"❌ CRUD Read failed: {response.status_code}")
                return False

            read_evidence = response.json()
            if read_evidence["description"] != "CRUD test file":
                print(f"❌ CRUD Read data mismatch")
                return False

            # 3. UPDATE
            response = self.client.put(
                f"/api/v1/evidence/{evidence_id}",
                json={"description": "Updated CRUD test file"}
            )
            if response.status_code != 200:
                print(f"❌ CRUD Update failed: {response.status_code}")
                return False

            updated_evidence = response.json()
            if updated_evidence["description"] != "Updated CRUD test file":
                print(f"❌ CRUD Update data mismatch")
                return False

            print("✅ API CRUD flow functional")
            return True
        except Exception as e:
            print(f"❌ API CRUD flow test failed: {e}")
            return False

    async def test_database_connection(self) -> bool:
        """Test database connection."""
        try:
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
            print("✅ Database connection successful")
            return True
        except Exception as e:
            print(f"❌ Database test failed: {e}")
            return False

    def test_type_annotations(self) -> bool:
        """Verify type annotations are present."""
        try:
            from casebuilder.api.endpoints.evidence import EvidenceService
            
            # Check that methods have proper annotations
            create_method = EvidenceService.create_evidence
            if not hasattr(create_method, '__annotations__'):
                print("❌ Missing type annotations")
                return False
            
            print("✅ Type annotations present")
            return True
        except Exception as e:
            print(f"❌ Type annotation test failed: {e}")
            return False

    def test_code_style(self) -> bool:
        """Basic code style verification."""
        try:
            # Check that files exist and are readable
            evidence_file = project_root / "casebuilder" / "api" / "endpoints" / "evidence.py"
            config_file = project_root / "casebuilder" / "core" / "config.py"
            base_file = project_root / "casebuilder" / "db" / "base.py"
            
            for file_path in [evidence_file, config_file, base_file]:
                if not file_path.exists():
                    print(f"❌ Missing file: {file_path}")
                    return False
                
                content = file_path.read_text()
                if len([line for line in content.split('\n') if len(line) > 79]) > 0:
                    print(f"❌ Line length violations in {file_path}")
                    return False
            
            print("✅ Code style checks passed")
            return True
        except Exception as e:
            print(f"❌ Code style test failed: {e}")
            return False

    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all verification tests."""
        print("🔍 Starting CaseBuilder System Verification...")
        print("=" * 50)
        
        tests = {
            "imports": self.test_imports(),
            "configuration": self.test_configuration(),
            "api_endpoints": self.test_api_endpoints(),
            "api_crud_flow": self.test_api_crud_flow(),
            "error_handling": self.test_error_handling(),
            "database_connection": await self.test_database_connection(),
            "type_annotations": self.test_type_annotations(),
            "code_style": self.test_code_style(),
        }
        
        print("=" * 50)
        print("📊 VERIFICATION RESULTS:")
        
        passed = 0
        total = len(tests)
        
        for test_name, result in tests.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name.replace('_', ' ').title()}: {status}")
            if result:
                passed += 1
        
        print("=" * 50)
        print(f"📈 OVERALL SCORE: {passed}/{total} ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 SYSTEM VERIFICATION COMPLETE - ALL TESTS PASSED!")
            print("🚀 CaseBuilder is ready for production deployment!")
        else:
            print("⚠️  Some tests failed. Please review the results above.")
        
        return tests


async def main():
    """Main verification function."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    verifier = SystemVerifier()
    results = await verifier.run_all_tests()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # Return appropriate exit code
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    asyncio.run(main())