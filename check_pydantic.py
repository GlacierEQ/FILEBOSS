"""
Script to check pydantic and pydantic-settings versions and compatibility.
"""
import sys
import pkg_resources

def get_package_version(package_name):
    """Get the version of an installed package."""
    try:
        return pkg_resources.get_distribution(package_name).version
    except pkg_resources.DistributionNotFound:
        return "Not installed"

def main():
    print("=" * 60)
    print("🔍 Checking pydantic and pydantic-settings")
    print("=" * 60)
    
    # Check Python version
    print(f"Python: {sys.version}\n")
    
    # Check pydantic version
    pydantic_version = get_package_version("pydantic")
    print(f"pydantic: {pydantic_version}")
    
    # Check pydantic-settings version
    pydantic_settings_version = get_package_version("pydantic-settings")
    print(f"pydantic-settings: {pydantic_settings_version}")
    
    # Check compatibility
    try:
        import pydantic
        import pydantic_settings
        
        print("\n✅ pydantic and pydantic-settings are importable")
        
        # Test basic functionality
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            name: str = "test"
            value: int = 42
            
        test = TestModel()
        print(f"✅ Basic pydantic model works: {test}")
        
        # Test pydantic-settings
        from pydantic_settings import BaseSettings
        
        class TestSettings(BaseSettings):
            test_setting: str = "default"
            
        settings = TestSettings()
        print(f"✅ Basic pydantic-settings works: {settings}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🏁 Check completed!")

if __name__ == "__main__":
    main()
