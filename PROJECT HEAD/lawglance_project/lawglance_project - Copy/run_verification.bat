@echo off
echo Setting up verification environment...

REM Create necessary directory for tests
if not exist "tests" mkdir tests

REM Write system_verification.py to the current directory
echo import os > system_verification.py
echo import sys >> system_verification.py
echo import logging >> system_verification.py
echo import json >> system_verification.py
echo import tempfile >> system_verification.py
echo from pathlib import Path >> system_verification.py
echo. >> system_verification.py

echo # Configure basic logging >> system_verification.py
echo logging.basicConfig(level=logging.INFO, >> system_verification.py
echo                    format='%%(asctime)s - %%(name)s - %%(levelname)s - %%(message)s') >> system_verification.py
echo logger = logging.getLogger("verification") >> system_verification.py
echo. >> system_verification.py

echo def verify_configuration(): >> system_verification.py
echo     """Verify that configuration loading works properly.""" >> system_verification.py
echo     logger.info("Verifying configuration system...") >> system_verification.py
echo     try: >> system_verification.py
echo         from config import Config, DEFAULT_CONFIG >> system_verification.py
echo         logger.info("✓ Configuration module imported successfully") >> system_verification.py
echo         return True >> system_verification.py
echo     except ImportError: >> system_verification.py
echo         logger.error("× Configuration module import failed") >> system_verification.py
echo         return False >> system_verification.py
echo. >> system_verification.py

echo def verify_document_cache(): >> system_verification.py
echo     """Verify that document caching works properly.""" >> system_verification.py
echo     logger.info("Verifying document cache system...") >> system_verification.py
echo     try: >> system_verification.py
echo         from document_cache import DocumentCache >> system_verification.py
echo         logger.info("✓ Document cache module imported successfully") >> system_verification.py
echo         return True >> system_verification.py
echo     except ImportError: >> system_verification.py
echo         logger.error("× Document cache module import failed") >> system_verification.py
echo         return False >> system_verification.py
echo. >> system_verification.py

echo def verify_document_processor(): >> system_verification.py
echo     """Verify that document processor works properly.""" >> system_verification.py
echo     logger.info("Verifying document processor...") >> system_verification.py
echo     try: >> system_verification.py
echo         from document_processor import DocumentProcessor >> system_verification.py
echo         logger.info("✓ Document processor module imported successfully") >> system_verification.py
echo         return True >> system_verification.py
echo     except ImportError: >> system_verification.py
echo         logger.error("× Document processor module import failed") >> system_verification.py
echo         return False >> system_verification.py
echo. >> system_verification.py

echo def verify_lawglance_integration(): >> system_verification.py
echo     """Verify that lawglance integration works properly.""" >> system_verification.py
echo     logger.info("Verifying lawglance integration...") >> system_verification.py
echo     try: >> system_verification.py
echo         from lawglance_integration import LawglanceIntegration >> system_verification.py
echo         logger.info("✓ Lawglance integration module imported successfully") >> system_verification.py
echo         return True >> system_verification.py
echo     except ImportError: >> system_verification.py
echo         logger.error("× Lawglance integration module import failed") >> system_verification.py
echo         return False >> system_verification.py
echo. >> system_verification.py

echo def run_verification(): >> system_verification.py
echo     """Run all verification tests.""" >> system_verification.py
echo     print("\nLawglance System Verification") >> system_verification.py
echo     print("=" * 60) >> system_verification.py
echo     results = {} >> system_verification.py
echo     results["config"] = verify_configuration() >> system_verification.py
echo     results["cache"] = verify_document_cache() >> system_verification.py
echo     results["processor"] = verify_document_processor() >> system_verification.py
echo     results["integration"] = verify_lawglance_integration() >> system_verification.py
echo     print("\nVerification Results:") >> system_verification.py
echo     print("-" * 60) >> system_verification.py
echo     for test, result in results.items(): >> system_verification.py
echo         status = "✓ PASSED" if result else "× FAILED" >> system_verification.py
echo         print(f"{test.ljust(15)} {status}") >> system_verification.py
echo     print("=" * 60) >> system_verification.py
echo     if all(results.values()): >> system_verification.py
echo         print("\nSystem verification completed successfully!") >> system_verification.py
echo         return True >> system_verification.py
echo     else: >> system_verification.py
echo         print("\nSystem verification failed! See logs for details.") >> system_verification.py
echo         return False >> system_verification.py
echo. >> system_verification.py

echo if __name__ == "__main__": >> system_verification.py
echo     run_verification() >> system_verification.py

echo Files created successfully!
echo.
echo Now running verification...
echo.

python system_verification.py

echo.
echo If module import tests failed, make sure all files are in the current directory.
echo You can create the necessary files with these commands:
echo.
echo copy config.py .
echo copy document_cache.py .
echo copy document_processor.py .
echo copy lawglance_integration.py .
echo.
echo Then run the verification script again:
echo python system_verification.py
echo.

pause
