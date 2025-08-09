"""
Simple script to check PostgreSQL installation and status.
"""
import os
import sys
import platform
import subprocess

def check_postgres_installed():
    """Check if PostgreSQL is installed."""
    print("🔍 Checking if PostgreSQL is installed...")
    
    # Common installation paths
    pg_paths = [
        r"C:\Program Files\PostgreSQL",
        r"C:\Program Files (x86)\PostgreSQL"
    ]
    
    for path in pg_paths:
        if os.path.exists(path):
            print(f"✅ Found PostgreSQL installation at: {path}")
            # List versions
            try:
                versions = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d)) and d[0].isdigit()]
                if versions:
                    print(f"   Versions found: {', '.join(sorted(versions))}")
                    return True
            except Exception as e:
                print(f"   Error checking versions: {e}")
    
    print("❌ PostgreSQL installation not found in common locations.")
    return False

def check_postgres_running():
    """Check if PostgreSQL service is running."""
    print("\n🔍 Checking if PostgreSQL service is running...")
    
    try:
        # Try to get list of running processes
        if platform.system() == "Windows":
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq postgres.exe'],
                capture_output=True,
                text=True
            )
            
            if "postgres.exe" in result.stdout:
                print("✅ PostgreSQL processes are running:")
                print(result.stdout)
                return True
            else:
                print("❌ No PostgreSQL processes found.")
                return False
        else:
            # For Unix-like systems
            result = subprocess.run(
                ['ps', 'aux', '|', 'grep', 'postgres'],
                capture_output=True,
                text=True,
                shell=True
            )
            if result.returncode == 0 and 'postgres' in result.stdout:
                print("✅ PostgreSQL processes are running:")
                print(result.stdout)
                return True
            else:
                print("❌ No PostgreSQL processes found.")
                return False
                
    except Exception as e:
        print(f"❌ Error checking PostgreSQL processes: {e}")
        return False

def check_postgres_connection():
    """Check if we can connect to PostgreSQL."""
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
            print("✅ Successfully connected to PostgreSQL!")
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
    """Run all checks."""
    print("="*80)
    print("POSTGRESQL STATUS CHECK")
    print("="*80)
    
    # Run all checks
    installed = check_postgres_installed()
    running = check_postgres_running()
    connected = check_postgres_connection()
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"✅ PostgreSQL installed: {'Yes' if installed else 'No'}")
    print(f"✅ PostgreSQL running: {'Yes' if running else 'No'}")
    print(f"✅ PostgreSQL connection successful: {'Yes' if connected else 'No'}")
    
    if not (installed and running and connected):
        print("\n❌ Some checks failed. Here's what to do next:")
        if not installed:
            print("1. Install PostgreSQL from: https://www.postgresql.org/download/")
        elif not running:
            print("1. Start PostgreSQL service:")
            if platform.system() == "Windows":
                print("   - Open 'Services' (press Win+R, type 'services.msc', press Enter)")
                print("   - Find 'postgresql' service")
                print("   - Right-click and select 'Start'")
            else:
                print("   - Run: sudo service postgresql start")
        elif not connected:
            print("1. Check PostgreSQL connection settings:")
            print("   - Verify username/password")
            print("   - Check if PostgreSQL is configured to accept connections")
            print("   - Make sure the server is running on port 5432")
    else:
        print("\n✅ Everything looks good! You can now run the database migrations.")

if __name__ == "__main__":
    main()
