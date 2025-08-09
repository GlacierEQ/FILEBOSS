"""
FileBoss Integration

This module provides integration between the FileOrganizer and the FileBoss system,
allowing for seamless file management and organization within the FileBoss environment.
"""

import logging
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from ..services.file_organizer import FileOrganizer, FileCategory
from ..models.case import Case, Subcase  # Assuming these models exist
from ..db.session import SessionLocal  # Database session

# Configure logging
logger = logging.getLogger(__name__)

class FileBossIntegration:
    """Handle integration between FileOrganizer and FileBoss."""
    
    def __init__(self, base_path: Optional[Path] = None):
        """Initialize the FileBoss integration.
        
        Args:
            base_path: Base path for file operations. If None, uses the default from settings.
        """
        self.organizer = FileOrganizer(base_path)
        self.db = SessionLocal()
    
    def __del__(self):
        """Ensure database session is closed when the object is destroyed."""
        self.db.close()
    
    def organize_case_files(
        self,
        case_id: str,
        source_path: Union[str, Path],
        subcase_id: Optional[str] = None,
        recursive: bool = True,
        move_files: bool = True
    ) -> Dict[str, Any]:
        """Organize files for a specific case.
        
        Args:
            case_id: The case identifier
            source_path: Path to the source directory or file
            subcase_id: Optional subcase identifier
            recursive: Whether to process subdirectories
            move_files: If True, move files; if False, copy them
            
        Returns:
            Dictionary with organization results
        """
        source_path = Path(source_path)
        results = {
            'case_id': case_id,
            'subcase_id': subcase_id,
            'source': str(source_path),
            'files_processed': 0,
            'files_organized': [],
            'errors': []
        }
        
        try:
            # Verify case exists in database
            case = self.db.query(Case).filter(Case.id == case_id).first()
            if not case:
                raise ValueError(f"Case not found: {case_id}")
            
            # Verify subcase if provided
            if subcase_id:
                subcase = self.db.query(Subcase).filter(
                    Subcase.id == subcase_id,
                    Subcase.case_id == case_id
                ).first()
                if not subcase:
                    raise ValueError(f"Subcase not found: {subcase_id} for case {case_id}")
            
            # Process files
            if source_path.is_file():
                try:
                    target_path = self.organizer.organize_file(
                        source_path, case_id, subcase_id)
                    results['files_organized'].append({
                        'source': str(source_path),
                        'target': str(target_path),
                        'status': 'moved' if move_files else 'copied'
                    })
                    results['files_processed'] += 1
                except Exception as e:
                    logger.error(f"Error processing file {source_path}: {e}")
                    results['errors'].append({
                        'file': str(source_path),
                        'error': str(e)
                    })
            else:
                # Process directory
                for file_path in source_path.rglob('*') if recursive else source_path.glob('*'):
                    if file_path.is_file():
                        try:
                            target_path = self.organizer.organize_file(
                                file_path, case_id, subcase_id)
                            results['files_organized'].append({
                                'source': str(file_path),
                                'target': str(target_path),
                                'status': 'moved' if move_files else 'copied'
                            })
                            results['files_processed'] += 1
                        except Exception as e:
                            logger.error(f"Error processing file {file_path}: {e}")
                            results['errors'].append({
                                'file': str(file_path),
                                'error': str(e)
                            })
        
        except Exception as e:
            logger.error(f"Error in organize_case_files: {e}")
            results['errors'].append({
                'file': 'system',
                'error': str(e)
            })
        
        return results
    
    def get_case_structure(self, case_id: str) -> Dict[str, Any]:
        """Get the file structure for a case.
        
        Args:
            case_id: The case identifier
            
        Returns:
            Dictionary representing the file structure
        """
        case_path = self.organizer.base_path / case_id
        
        if not case_path.exists():
            return {
                'case_id': case_id,
                'exists': False,
                'message': f'Case directory not found: {case_path}'
            }
        
        def build_tree(path: Path) -> Dict[str, Any]:
            """Recursively build a tree structure from a directory."""
            if path.is_file():
                return {
                    'name': path.name,
                    'type': 'file',
                    'size': path.stat().st_size,
                    'modified': datetime.fromtimestamp(path.stat().st_mtime).isoformat()
                }
            
            tree = {
                'name': path.name,
                'type': 'directory',
                'children': []
            }
            
            for child in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                tree['children'].append(build_tree(child))
            
            return tree
        
        return {
            'case_id': case_id,
            'exists': True,
            'path': str(case_path),
            'structure': build_tree(case_path)
        }
    
    def search_case_files(
        self,
        case_id: str,
        query: str,
        file_types: Optional[List[str]] = None,
        modified_after: Optional[datetime] = None,
        modified_before: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Search for files within a case.
        
        Args:
            case_id: The case identifier
            query: Search query (searches in filenames and content)
            file_types: Optional list of file extensions to filter by (e.g., ['.pdf', '.docx'])
            modified_after: Only include files modified after this date
            modified_before: Only include files modified before this date
            
        Returns:
            List of matching files with metadata
        """
        case_path = self.organizer.base_path / case_id
        results = []
        
        if not case_path.exists():
            logger.warning(f"Case directory not found: {case_path}")
            return []
        
        # Normalize file extensions
        if file_types:
            file_types = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                         for ext in file_types]
        
        # Search through files
        for file_path in case_path.rglob('*'):
            if not file_path.is_file():
                continue
                
            # Check file type filter
            if file_types and file_path.suffix.lower() not in file_types:
                continue
                
            # Check modification time filters
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if modified_after and mtime < modified_after:
                continue
            if modified_before and mtime > modified_before:
                continue
            
            # Check if filename or content matches query
            if (query.lower() in file_path.name.lower() or
                self._file_contains(file_path, query)):
                
                results.append({
                    'path': str(file_path.relative_to(case_path)),
                    'name': file_path.name,
                    'size': file_path.stat().st_size,
                    'modified': mtime.isoformat(),
                    'type': file_path.suffix.lower()
                })
        
        return results
    
    def _file_contains(self, file_path: Path, search_text: str) -> bool:
        """Check if a file contains the search text."""
        try:
            # For text files, read directly
            if file_path.suffix.lower() in ['.txt', '.log', '.md', '.csv', '.json', '.yaml', '.yml']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return search_text.lower() in f.read().lower()
            
            # For other files, use the metadata extractor
            from ..services.metadata_extractors import extract_text_content
            text_content = extract_text_content(file_path)
            return search_text.lower() in text_content.lower()
            
        except Exception as e:
            logger.debug(f"Could not search content of {file_path}: {e}")
            return False
    
    def sync_with_database(self, case_id: str) -> Dict[str, Any]:
        """Sync the filesystem state with the database for a case.
        
        This ensures the database has an accurate record of all files in the case.
        """
        case_path = self.organizer.base_path / case_id
        
        if not case_path.exists():
            return {
                'success': False,
                'message': f'Case directory not found: {case_path}',
                'files_processed': 0,
                'files_added': 0,
                'files_removed': 0,
                'errors': []
            }
        
        # Get all files in the case directory
        files_in_fs = set()
        for file_path in case_path.rglob('*'):
            if file_path.is_file():
                rel_path = str(file_path.relative_to(case_path))
                files_in_fs.add(rel_path)
        
        # Get all files in the database for this case
        files_in_db = set()
        # TODO: Implement database query to get files for this case
        
        # Find new and removed files
        new_files = files_in_fs - files_in_db
        removed_files = files_in_db - files_in_fs
        
        # TODO: Update database with new and removed files
        
        return {
            'success': True,
            'files_processed': len(files_in_fs),
            'files_added': len(new_files),
            'files_removed': len(removed_files),
            'errors': []
        }
