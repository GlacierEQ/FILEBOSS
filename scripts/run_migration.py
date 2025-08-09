"""
Script to run database migrations using Alembic.
This script ensures the environment is properly set up before running migrations.
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def run_migration():
    """Run the database migration using Alembic."""
    # Set up environment variables
    os.environ["PYTHONPATH"] = str(project_root)
    
    # Import settings to ensure environment variables are loaded
    from app.core.config import settings
    
    # Set the database URL for Alembic
    os.environ["SQLALCHEMY_DATABASE_URI"] = str(settings.SQLALCHEMY_DATABASE_URI)
    
    # Run the Alembic command
    from alembic.config import main as alembic_main
    
    print("Running database migrations...")
    print(f"Database URL: {settings.SQLALCHEMY_DATABASE_URI}")
    
    # Generate the initial migration
    print("\nGenerating initial migration...")
    alembic_main(["revision", "--autogenerate", "-m", "Initial migration"])
    
    # Apply the migration
    print("\nApplying migrations...")
    alembic_main(["upgrade", "head"])
    
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    run_migration()
