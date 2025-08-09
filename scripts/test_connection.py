"""
Script to test PostgreSQL connection with different configurations.
"""
import psycopg2
from psycopg2 import OperationalError

def test_connection(host, port, dbname, user, password):
    """Test PostgreSQL connection with given parameters."""
    print(f"\n🔌 Testing connection to {user}@{host}:{port}/{dbname}...")
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Successfully connected to PostgreSQL!")
        print(f"   {version[0]}")
        
        # Get current database and user
        cursor.execute("SELECT current_database(), current_user, current_schema();")
        db_info = cursor.fetchone()
        print(f"\n📊 Database Info:")
        print(f"   - Database: {db_info[0]}")
        print(f"   - User: {db_info[1]}")
        print(f"   - Schema: {db_info[2]}")
        
        # List all databases
        cursor.execute("""
            SELECT datname 
            FROM pg_database 
            WHERE datistemplate = false
            ORDER BY datname;
        """)
        
        print("\n📋 Available databases:")
        print("-" * 80)
        for db in cursor.fetchall():
            print(f"   - {db[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except OperationalError as e:
        print(f"❌ Connection failed: {e}")
        return False

def main():
    """Test multiple connection configurations."""
    print("="*80)
    print("POSTGRESQL CONNECTION TESTER")
    print("="*80)
    
    # Common connection configurations to try
    configs = [
        # Default configuration
        {
            "host": "localhost",
            "port": 5432,
            "dbname": "postgres",
            "user": "postgres",
            "password": "postgres"
        },
        # Common alternative port
        {
            "host": "localhost",
            "port": 5433,
            "dbname": "postgres",
            "user": "postgres",
            "password": "postgres"
        },
        # No password (might be required for some local setups)
        {
            "host": "localhost",
            "port": 5432,
            "dbname": "postgres",
            "user": "postgres",
            "password": ""
        },
        # Try with empty database name
        {
            "host": "localhost",
            "port": 5432,
            "dbname": "",
            "user": "postgres",
            "password": "postgres"
        },
        # Try with 'template1' database
        {
            "host": "localhost",
            "port": 5432,
            "dbname": "template1",
            "user": "postgres",
            "password": "postgres"
        }
    ]
    
    success = False
    for config in configs:
        if test_connection(**config):
            success = True
            break
    
    if not success:
        print("\n❌ Could not connect to PostgreSQL with any configuration.")
        print("\nTroubleshooting steps:")
        print("1. Make sure PostgreSQL is running")
        print("2. Check the port number (common ports: 5432, 5433)")
        print("3. Verify the username and password")
        print("4. Check if PostgreSQL is configured to accept connections")
        print("   - Look for pg_hba.conf and postgresql.conf files")
        print("   - Make sure 'listen_addresses' includes 'localhost' or '*'") 
        print("   - Check 'port' setting in postgresql.conf")
        print("5. Check the PostgreSQL service logs for errors")
        print("\nOn Windows, you can check the service status with:")
        print("   sc query postgresql")
        print("Or start it with:")
        print("   net start postgresql-x64-15")
        print("   net start postgresql-x64-17")

if __name__ == "__main__":
    main()
