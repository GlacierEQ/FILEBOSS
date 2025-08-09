"""
Script to check system information and PostgreSQL installation status.
"""
import os
import sys
import platform
import subprocess
from pathlib import Path

def get_system_info():
    """Gather basic system information."""
    print("\n" + "="*80)
    print("SYSTEM INFORMATION")
    print("="*80)
    
    # Basic system info
    print(f"\n💻 System: {platform.system()} {platform.release()} ({platform.version()})")
    print(f"🔢 Python: {platform.python_version()}")
    print(f"📁 Current directory: {os.getcwd()}")
    
    # Check for PostgreSQL in common locations
    pg_paths = [
        "C:\\Program Files\\PostgreSQL",
        "C:\\Program Files (x86)\\PostgreSQL",
        "/usr/local/var/postgres",
        "/var/lib/postgresql"
    ]
    
    print("\n🔍 Checking for PostgreSQL installation...")
    pg_installed = False
    
    for path in pg_paths:
        if os.path.exists(path):
            print(f"✅ Found PostgreSQL installation at: {path}")
            pg_installed = True
            
            # Try to find version
            try:
                versions = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d)) and d[0].isdigit()]
                if versions:
                    print(f"   Detected versions: {', '.join(sorted(versions))}")
            except Exception as e:
                print(f"   Could not list versions: {e}")
    
    if not pg_installed:
        print("❌ PostgreSQL installation not found in common locations.")
    
    return pg_installed

def check_postgres_service():
    """Check PostgreSQL service status on Windows."""
    print("\n🔍 Checking PostgreSQL service status...")
    
    try:
        # Try to get PostgreSQL service status
        result = subprocess.run(
            ["sc", "query", "postgresql"],
            capture_output=True,
            text=True,
            shell=True
        )
        
        if "The specified service does not exist" in result.stdout + result.stderr:
            print("❌ PostgreSQL service is not installed.")
            return False
            
        if "RUNNING" in result.stdout:
            print("✅ PostgreSQL service is running.")
            return True
        else:
            print(f"ℹ️ PostgreSQL service status:\n{result.stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking PostgreSQL service: {e}")
        return False

def check_postgres_connection():
    """Attempt to connect to PostgreSQL."""
    print("\n🔌 Testing PostgreSQL connection...")
    
    try:
        import psycopg2
        
        try:
            conn = psycopg2.connect(
                dbname="postgres",
                user="postgres",
                password="postgres",
                host="localhost",
                port=5432
            )
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"✅ Successfully connected to PostgreSQL!")
            print(f"   {version[0]}")
            cursor.close()
            conn.close()
            return True
            
        except psycopg2.OperationalError as e:
            print(f"❌ Could not connect to PostgreSQL: {e}")
            return False
            
    except ImportError:
        print("❌ psycopg2 is not installed. Install it with: pip install psycopg2-binary")
        return False

def main():
    """Main function to run all checks."""
    print("🔍 Starting system check...")
    
    # Run all checks
    pg_installed = get_system_info()
    
    if platform.system() == "Windows":
        service_running = check_postgres_service()
    else:
        print("\n⚠️ Non-Windows system detected. Some checks may not be applicable.")
        service_running = False
    
    connection_ok = check_postgres_connection()
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ PostgreSQL installed: {'Yes' if pg_installed else 'No'}")
    print(f"✅ PostgreSQL service running: {'Yes' if service_running else 'No'}")
    print(f"✅ PostgreSQL connection successful: {'Yes' if connection_ok else 'No'}")
    
    if not (pg_installed and service_running and connection_ok):
        print("\n❌ Some checks failed. Here's what to do next:")
        if not pg_installed:
            print("1. Install PostgreSQL from: https://www.postgresql.org/download/")
        elif not service_running:
            print("1. Start PostgreSQL service:")
            print("   - Open 'Services' (press Win+R, type 'services.msc', press Enter)")
            print("   - Find 'postgresql' service")
            print("   - Right-click and select 'Start'")
        elif not connection_ok:
            print("1. Check PostgreSQL connection settings:")
            print("   - Verify username/password")
            print("   - Check if PostgreSQL is configured to accept connections")
            print("   - Make sure the server is running on port 5432")
    else:
        print("\n✅ Everything looks good! You can now run the database migrations.")

if __name__ == "__main__":
    main()
