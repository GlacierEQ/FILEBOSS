"""
Script to check if PostgreSQL server is running and accessible.
"""
import sys
import psycopg2
from psycopg2 import OperationalError

def check_postgres():
    """Check if PostgreSQL server is running and accessible."""
    print("🔍 Checking PostgreSQL server status...")
    
    # Common connection parameters
    connection_params = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'postgres',
        'dbname': 'postgres'  # Connect to default 'postgres' database
    }
    
    try:
        # Attempt to connect to the database
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()
        
        # Execute a simple query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        
        print("✅ PostgreSQL is running!")
        print(f"   Version: {version[0]}")
        
        # List all databases
        cursor.execute("""
            SELECT datname 
            FROM pg_database 
            WHERE datistemplate = false
            ORDER BY datname;
        """)
        
        print("\n📋 Available databases:")
        print("-" * 40)
        for db in cursor.fetchall():
            print(f"   - {db[0]}")
        
        # Close the connection
        cursor.close()
        conn.close()
        return True
        
    except OperationalError as e:
        print("❌ Could not connect to PostgreSQL server:")
        print(f"   Error: {e}")
        print("\nTroubleshooting steps:")
        print("1. Make sure PostgreSQL is installed")
        print("2. Check if the PostgreSQL service is running")
        print("3. Verify the connection parameters (host, port, username, password)" 
              " in the script match your PostgreSQL setup")
        print("4. Check if PostgreSQL is configured to accept connections "
              "(check pg_hba.conf and postgresql.conf files)")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return False

if __name__ == "__main__":
    if check_postgres():
        sys.exit(0)
    else:
        sys.exit(1)
