""
Database Service

This module provides database operations for the CaseBuilder system.
"""

import os
import hashlib
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from ..models import (
    Base, Case, Subcase, File, FileMetadata, FileVersion, Tag, FileTag,
    get_db, init_db as init_database
)
from ..schemas import (
    CaseCreate, SubcaseCreate, FileCreate, FileMetadataCreate,
    FileVersionCreate, TagCreate, FileTagCreate
)
from ..utils.file_utils import calculate_file_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseService:
    """Service class for database operations."""
    
    def __init__(self, db: Session):
        """Initialize the database service with a database session."""
        self.db = db
    
    # Case Operations
    def get_case(self, case_id: str) -> Optional[Case]:
        """Get a case by ID."""
        return self.db.query(Case).filter(Case.id == case_id).first()
    
    def get_cases(self, skip: int = 0, limit: int = 100) -> List[Case]:
        """Get a list of cases with pagination."""
        return self.db.query(Case).offset(skip).limit(limit).all()
    
    def create_case(self, case: CaseCreate) -> Case:
        """Create a new case."""
        db_case = Case(**case.dict())
        self.db.add(db_case)
        self.db.commit()
        self.db.refresh(db_case)
        return db_case
    
    # File Operations
    def get_file(self, file_id: str) -> Optional[File]:
        """Get a file by ID with its metadata."""
        return (
            self.db.query(File)
            .options(joinedload(File.metadata))
            .filter(File.id == file_id)
            .first()
        )
    
    def get_files_by_case(
        self, 
        case_id: str, 
        subcase_id: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[File]:
        """Get files for a case (and optionally a subcase) with pagination."""
        query = self.db.query(File).filter(File.case_id == case_id)
        
        if subcase_id:
            query = query.filter(File.subcase_id == subcase_id)
            
        return query.offset(skip).limit(limit).all()
    
    def create_file(self, file_data: FileCreate) -> File:
        """Create a new file record in the database."""
        db_file = File(**file_data.dict(exclude={"metadata"}))
        self.db.add(db_file)
        self.db.commit()
        self.db.refresh(db_file)
        
        # Add metadata if provided
        if hasattr(file_data, 'metadata') and file_data.metadata:
            metadata_data = file_data.metadata.dict()
            metadata_data['file_id'] = db_file.id
            db_metadata = FileMetadata(**metadata_data)
            self.db.add(db_metadata)
            self.db.commit()
            db_file.metadata = db_metadata
        
        return db_file
    
    def update_file_metadata(
        self, 
        file_id: str, 
        metadata: FileMetadataCreate
    ) -> Optional[File]:
        """Update a file's metadata."""
        db_file = self.get_file(file_id)
        if not db_file:
            return None
            
        if not db_file.metadata:
            # Create new metadata if it doesn't exist
            metadata_data = metadata.dict()
            metadata_data['file_id'] = file_id
            db_metadata = FileMetadata(**metadata_data)
            self.db.add(db_metadata)
        else:
            # Update existing metadata
            for key, value in metadata.dict().items():
                if value is not None:  # Don't update with None values
                    setattr(db_file.metadata, key, value)
        
        self.db.commit()
        self.db.refresh(db_file)
        return db_file
    
    def add_file_version(self, version_data: FileVersionCreate) -> FileVersion:
        """Add a new version of a file."""
        # Get the next version number
        current_version = (
            self.db.query(FileVersion)
            .filter(FileVersion.file_id == version_data.file_id)
            .order_by(FileVersion.version_number.desc())
            .first()
        )
        
        version_number = 1
        if current_version:
            version_number = current_version.version_number + 1
        
        # Create the new version
        version_data_dict = version_data.dict()
        version_data_dict['version_number'] = version_number
        
        db_version = FileVersion(**version_data_dict)
        self.db.add(db_version)
        self.db.commit()
        self.db.refresh(db_version)
        
        return db_version
    
    # Tag Operations
    def get_or_create_tag(self, tag_data: TagCreate) -> Tag:
        """Get an existing tag or create it if it doesn't exist."""
        # Try to find an existing tag (case-insensitive)
        tag = (
            self.db.query(Tag)
            .filter(Tag.name.ilike(tag_data.name))
            .first()
        )
        
        if not tag:
            # Create a new tag
            tag = Tag(**tag_data.dict())
            self.db.add(tag)
            self.db.commit()
            self.db.refresh(tag)
        
        return tag
    
    def tag_file(
        self, 
        file_id: str, 
        tag_data: Union[str, TagCreate],
        value: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> Optional[FileTag]:
        """Add a tag to a file."""
        # If tag_data is a string, create a TagCreate object
        if isinstance(tag_data, str):
            tag_data = TagCreate(name=tag_data)
        
        # Get or create the tag
        tag = self.get_or_create_tag(tag_data)
        
        # Check if the file exists
        file = self.get_file(file_id)
        if not file:
            return None
        
        # Check if the tag is already assigned to the file
        existing = (
            self.db.query(FileTag)
            .filter(
                FileTag.file_id == file_id,
                FileTag.tag_id == tag.id
            )
            .first()
        )
        
        if existing:
            # Update existing tag
            if value is not None:
                existing.value = value
            if created_by is not None:
                existing.created_by = created_by
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # Create new file tag
        file_tag = FileTag(
            file_id=file_id,
            tag_id=tag.id,
            value=value,
            created_by=created_by
        )
        
        self.db.add(file_tag)
        self.db.commit()
        self.db.refresh(file_tag)
        
        return file_tag
    
    def get_file_tags(self, file_id: str) -> List[Dict[str, Any]]:
        """Get all tags for a file with their values."""
        return (
            self.db.query(Tag, FileTag.value)
            .join(FileTag, Tag.id == FileTag.tag_id)
            .filter(FileTag.file_id == file_id)
            .all()
        )
    
    # Search Operations
    def search_files(
        self,
        query: str,
        case_id: Optional[str] = None,
        subcase_id: Optional[str] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[File]:
        """Search for files based on various criteria."""
        from sqlalchemy import or_, and_
        
        search = f"%{query}%"
        
        # Start with a base query
        q = self.db.query(File).join(File.metadata, isouter=True)
        
        # Apply filters
        filters = []
        
        if case_id:
            filters.append(File.case_id == case_id)
        
        if subcase_id:
            filters.append(File.subcase_id == subcase_id)
        
        if category:
            filters.append(File.category == category)
        
        if tag:
            q = q.join(File.tags).filter(Tag.name.ilike(f"%{tag}%"))
        
        # Add search conditions
        search_conditions = [
            File.original_name.ilike(search),
            FileMetadata.title.ilike(search),
            FileMetadata.author.ilike(search),
            FileMetadata.subject.ilike(search),
            FileMetadata.extracted_text.ilike(search)
        ]
        
        # Apply all filters and search conditions
        q = q.filter(and_(*filters)).filter(or_(*search_conditions))
        
        # Execute the query with pagination
        return q.offset(skip).limit(limit).all()
    
    # File System Integration
    def sync_file_with_filesystem(
        self,
        file_path: str,
        case_id: str,
        subcase_id: Optional[str] = None,
        category: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[File]:
        """
        Sync a file from the filesystem with the database.
        
        If the file already exists (determined by path), it will be updated.
        Otherwise, a new file record will be created.
        """
        from pathlib import Path
        import os
        
        path = Path(file_path).resolve()
        
        if not path.exists() or not path.is_file():
            logger.error(f"File not found: {file_path}")
            return None
        
        # Calculate file hash
        try:
            file_hash = calculate_file_hash(str(path))
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return None
        
        # Check if file already exists in the database
        db_file = (
            self.db.query(File)
            .filter(File.stored_path == str(path))
            .first()
        )
        
        # Get file stats
        stat = path.stat()
        file_size = stat.st_size
        created_at = datetime.fromtimestamp(stat.st_ctime)
        modified_at = datetime.fromtimestamp(stat.st_mtime)
        
        if db_file:
            # File exists, check if it's been modified
            if db_file.file_hash != file_hash:
                # File has changed, create a new version
                version_data = FileVersionCreate(
                    file_id=db_file.id,
                    file_path=str(path),
                    file_size=file_size,
                    file_hash=file_hash,
                    changes="File modified"
                )
                self.add_file_version(version_data)
                
                # Update the file record
                db_file.file_size = file_size
                db_file.file_hash = file_hash
                db_file.file_modified = modified_at
                
                if category:
                    db_file.category = category
                
                self.db.commit()
                self.db.refresh(db_file)
                
                logger.info(f"Updated file: {path}")
            
            return db_file
        else:
            # Create a new file record
            file_data = FileCreate(
                id=file_hash,  # Use hash as ID for deduplication
                case_id=case_id,
                subcase_id=subcase_id,
                original_name=path.name,
                stored_path=str(path),
                file_size=file_size,
                file_hash=file_hash,
                mime_type=None,  # Will be detected by metadata extractor
                file_extension=path.suffix.lower().lstrip('.'),
                category=category or FileCategory.OTHER,
                file_created=created_at,
                file_modified=modified_at,
                metadata=metadata
            )
            
            return self.create_file(file_data)
    
    def sync_directory(
        self,
        directory: str,
        case_id: str,
        subcase_id: Optional[str] = None,
        category: Optional[str] = None,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Sync all files in a directory with the database.
        
        Returns a dictionary with sync statistics.
        """
        from pathlib import Path
        
        directory_path = Path(directory).resolve()
        
        if not directory_path.exists() or not directory_path.is_dir():
            return {
                "success": False,
                "error": f"Directory not found: {directory}",
                "processed": 0,
                "added": 0,
                "updated": 0,
                "errors": 0
            }
        
        # Get all files in the directory
        files_to_process = []
        
        if recursive:
            files_to_process = [str(p) for p in directory_path.rglob('*') if p.is_file()]
        else:
            files_to_process = [str(p) for p in directory_path.iterdir() if p.is_file()]
        
        # Process each file
        stats = {
            "processed": 0,
            "added": 0,
            "updated": 0,
            "errors": 0,
            "files": []
        }
        
        for file_path in files_to_process:
            try:
                result = self.sync_file_with_filesystem(
                    file_path=file_path,
                    case_id=case_id,
                    subcase_id=subcase_id,
                    category=category
                )
                
                if result:
                    if result in [f['path'] for f in stats['files']]:
                        stats['updated'] += 1
                    else:
                        stats['added'] += 1
                    
                    stats['files'].append({
                        'path': file_path,
                        'id': result.id,
                        'status': 'added' if stats['added'] > 0 else 'updated'
                    })
                else:
                    stats['errors'] += 1
                    stats['files'].append({
                        'path': file_path,
                        'status': 'error',
                        'error': 'Failed to process file'
                    })
                
                stats['processed'] += 1
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                stats['errors'] += 1
                stats['files'].append({
                    'path': file_path,
                    'status': 'error',
                    'error': str(e)
                })
        
        return stats

def init_db() -> None:
    """Initialize the database by creating all tables."""
    from sqlalchemy import create_engine
    from ..models.base import Base, engine
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")

def get_db_service() -> DatabaseService:
    """Get a database service instance with a new session."""
    from sqlalchemy.orm import Session
    from ..models.base import SessionLocal
    
    db = SessionLocal()
    try:
        yield DatabaseService(db)
    finally:
        db.close()
