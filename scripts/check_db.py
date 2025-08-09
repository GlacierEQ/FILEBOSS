"""
Script to check database connection and list tables using raw SQL.
"""
import os
import sys
import logging
from pathlib import Path

# Set up logging to both console and file
log_file = Path("db_check.log")
log_file.unlink(missing_ok=True)  # Remove previous log file if it exists

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, mode='w')
    ]
)
logger = logging.getLogger("db_check")

def check_database():
    """Check database connection and list tables."""
    try:
        # Add project root to Python path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        # Import SQLAlchemy
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import SQLAlchemyError
        
        # Get database URL from environment or use default
        db_url = os.getenv("DATABASE_URL") or "postgresql://postgres:postgres@localhost:5432/fileboss"
        
        logger.info("=" * 80)
        logger.info("DATABASE CONNECTION CHECK")
        logger.info("=" * 80)
        logger.info(f"Connecting to: {db_url}")
        
        # Create engine with echo=True for detailed SQL logging
        engine = create_engine(db_url, echo=True)
        
        # Test connection
        with engine.connect() as conn:
            # Get database version
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"\n✅ Connected to database:")
            logger.info(f"   {version}")
            
            # Get current database
            result = conn.execute(text("SELECT current_database(), current_user, current_schema()"))
            db_info = result.fetchone()
            logger.info(f"\nDatabase Info:")
            logger.info(f"  - Database: {db_info[0]}")
            logger.info(f"  - User: {db_info[1]}")
            logger.info(f"  - Schema: {db_info[2]}")
            
            # List all tables
            logger.info("\n📋 Listing all tables:")
            logger.info("-" * 40)
            
            # Get all tables in the public schema
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            
            tables = [row[0] for row in result.fetchall()]
            
            if not tables:
                logger.warning("No tables found in the database!")
                return False
                
            logger.info(f"Found {len(tables)} tables:")
            for table in tables:
                logger.info(f"  - {table}")
                
                # Get table info
                try:
                    # Get column info
                    col_result = conn.execute(text(f"""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns
                        WHERE table_name = :table_name
                        ORDER BY ordinal_position
                    """), {"table_name": table})
                    
                    for col in col_result:
                        nullable = "NULL" if col[2] == 'YES' else "NOT NULL"
                        default = f" DEFAULT {col[3]}" if col[3] else ""
                        logger.info(f"    {col[0]}: {col[1]} {nullable}{default}")
                    
                    # Get primary key info
                    pk_result = conn.execute(text("""
                        SELECT a.attname
                        FROM pg_index i
                        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
                        WHERE i.indrelid = :table_name::regclass
                        AND i.indisprimary
                    """), {"table_name": table})
                    
                    pks = [row[0] for row in pk_result]
                    if pks:
                        logger.info(f"    Primary Key: {', '.join(pks)}")
                    
                    # Get foreign key info
                    fk_result = conn.execute(text("""
                        SELECT
                            kcu.column_name,
                            ccu.table_name AS foreign_table_name,
                            ccu.column_name AS foreign_column_name
                        FROM
                            information_schema.table_constraints AS tc
                            JOIN information_schema.key_column_usage AS kcu
                                ON tc.constraint_name = kcu.constraint_name
                                AND tc.table_schema = kcu.table_schema
                            JOIN information_schema.constraint_column_usage AS ccu
                                ON ccu.constraint_name = tc.constraint_name
                                AND ccu.table_schema = tc.table_schema
                        WHERE tc.constraint_type = 'FOREIGN KEY' 
                        AND tc.table_name = :table_name
                    """), {"table_name": table})
                    
                    fks = list(fk_result)
                    if fks:
                        logger.info("    Foreign Keys:")
                        for fk in fks:
                            logger.info(f"      {fk[0]} -> {fk[1]}.{fk[2]}")
                    
                    logger.info("")  # Add empty line between tables
                    
                except Exception as e:
                    logger.error(f"    Error getting table info: {e}")
                    continue
        
        logger.info("\n✅ Database check completed successfully!")
        return True
        
    except SQLAlchemyError as e:
        logger.error(f"❌ Database error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}", exc_info=True)
        return False
    finally:
        logger.info(f"\nLog saved to: {log_file.absolute()}")

if __name__ == "__main__":
    logger.info("Starting database check...")
    if check_database():
        logger.info("✅ Check completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Check failed! See the log file for details.")
        sys.exit(1)
