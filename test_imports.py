"""
Test script to verify project imports and module structure.
"""
import os
import sys
from pathlib import Path
import importlib
import traceback

# Add project root to path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print("=" * 60)
print("🔍 Testing Project Imports")
print("=" * 60)

# List of modules to test
MODULES_TO_TEST = [
    "casebuilder.core.config",
    "casebuilder.db.base",
    "casebuilder.db.models",
    "casebuilder.api.deps",
    "casebuilder.api.v1.api",
    "casebuilder.api.app"
]

def test_import(module_name):
    """Test importing a module and print the result."""
    try:
        print(f"\n🔍 Testing import: {module_name}")
        module = importlib.import_module(module_name)
        print(f"✅ Successfully imported {module_name}")
        print(f"   - Location: {getattr(module, '__file__', 'Unknown')}")
        return True
    except ImportError as e:
        print(f"❌ ImportError: {e}")
        print("   - This usually means a module or dependency is missing.")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Error importing {module_name}: {e}")
        traceback.print_exc()
        return False

# Test each module
results = {}
for module_name in MODULES_TO_TEST:
    results[module_name] = test_import(module_name)

# Print summary
print("\n" + "=" * 60)
print("📊 Import Test Summary")
print("=" * 60)

success_count = sum(1 for result in results.values() if result)
failure_count = len(results) - success_count

print(f"\n✅ Successfully imported: {success_count}/{len(results)} modules")
print(f"❌ Failed to import: {failure_count}/{len(results)} modules")

if failure_count > 0:
    print("\nFailed imports:")
    for module, success in results.items():
        if not success:
            print(f"  - {module}")

print("\n🏁 Import test completed!")
