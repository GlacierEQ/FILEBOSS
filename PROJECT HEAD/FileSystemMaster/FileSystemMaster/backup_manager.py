"""
Backup and restore functionality for safe file operations
"""

import json
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class BackupManager:
    """Manages backup creation and restoration for safe file operations"""
    
    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.backup_manifest_file = self.backup_dir / "backup_manifest.json"
        self._load_manifest()
    
    def _load_manifest(self):
        """Load backup manifest from disk"""
        try:
            if self.backup_manifest_file.exists():
                with open(self.backup_manifest_file, 'r', encoding='utf-8') as f:
                    self.manifest = json.load(f)
            else:
                self.manifest = {}
        except Exception as e:
            logger.warning(f"Could not load backup manifest: {e}")
            self.manifest = {}
    
    def _save_manifest(self):
        """Save backup manifest to disk"""
        try:
            with open(self.backup_manifest_file, 'w', encoding='utf-8') as f:
                json.dump(self.manifest, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Could not save backup manifest: {e}")
    
    def create_backup(self, source_dir: Path) -> str:
        """Create a backup of the source directory"""
        
        timestamp = int(time.time())
        backup_id = f"backup_{timestamp}"
        backup_path = self.backup_dir / backup_id
        
        logger.info(f"Creating backup: {backup_id}")
        
        try:
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copy files
            files_backed_up = []
            for root, dirs, files in source_dir.rglob('*'):
                if root.is_file():
                    relative_path = root.relative_to(source_dir)
                    backup_file_path = backup_path / relative_path
                    
                    # Create parent directories
                    backup_file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(root, backup_file_path)
                    files_backed_up.append({
                        'original': str(root),
                        'backup': str(backup_file_path),
                        'relative': str(relative_path)
                    })
            
            # Create backup metadata
            backup_metadata = {
                'id': backup_id,
                'timestamp': timestamp,
                'source_directory': str(source_dir),
                'backup_directory': str(backup_path),
                'files_count': len(files_backed_up),
                'files': files_backed_up,
                'status': 'completed'
            }
            
            # Save backup metadata
            metadata_file = backup_path / "backup_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(backup_metadata, f, indent=2)
            
            # Update manifest
            self.manifest[backup_id] = backup_metadata
            self._save_manifest()
            
            logger.info(f"Backup created successfully: {backup_id} ({len(files_backed_up)} files)")
            return backup_id
            
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            # Clean up partial backup
            if backup_path.exists():
                shutil.rmtree(backup_path, ignore_errors=True)
            raise Exception(f"Backup creation failed: {str(e)}")
    
    def restore_backup(self, backup_id: str) -> bool:
        """Restore files from a backup"""
        
        if backup_id not in self.manifest:
            logger.error(f"Backup not found: {backup_id}")
            return False
        
        backup_metadata = self.manifest[backup_id]
        backup_path = Path(backup_metadata['backup_directory'])
        
        if not backup_path.exists():
            logger.error(f"Backup directory not found: {backup_path}")
            return False
        
        logger.info(f"Restoring backup: {backup_id}")
        
        try:
            # Load backup metadata
            metadata_file = backup_path / "backup_metadata.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    detailed_metadata = json.load(f)
                files_to_restore = detailed_metadata.get('files', [])
            else:
                # Fallback: scan backup directory
                files_to_restore = []
                for backup_file in backup_path.rglob('*'):
                    if backup_file.is_file() and backup_file.name != 'backup_metadata.json':
                        relative_path = backup_file.relative_to(backup_path)
                        original_path = Path(backup_metadata['source_directory']) / relative_path
                        files_to_restore.append({
                            'original': str(original_path),
                            'backup': str(backup_file),
                            'relative': str(relative_path)
                        })
            
            # Restore files
            restored_count = 0
            for file_info in files_to_restore:
                try:
                    original_path = Path(file_info['original'])
                    backup_file_path = Path(file_info['backup'])
                    
                    if not backup_file_path.exists():
                        logger.warning(f"Backup file not found: {backup_file_path}")
                        continue
                    
                    # Create parent directories
                    original_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Restore file
                    shutil.copy2(backup_file_path, original_path)
                    restored_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to restore {file_info['original']}: {str(e)}")
            
            logger.info(f"Restore completed: {restored_count}/{len(files_to_restore)} files restored")
            return restored_count > 0
            
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            return False
    
    def list_backups(self) -> List[Dict]:
        """List all available backups"""
        backups = []
        for backup_id, metadata in self.manifest.items():
            backup_info = {
                'id': backup_id,
                'timestamp': metadata.get('timestamp'),
                'date': time.strftime('%Y-%m-%d %H:%M:%S', 
                                   time.localtime(metadata.get('timestamp', 0))),
                'source_directory': metadata.get('source_directory'),
                'files_count': metadata.get('files_count', 0),
                'status': metadata.get('status', 'unknown')
            }
            backups.append(backup_info)
        
        # Sort by timestamp (newest first)
        backups.sort(key=lambda x: x['timestamp'], reverse=True)
        return backups
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup"""
        
        if backup_id not in self.manifest:
            logger.error(f"Backup not found: {backup_id}")
            return False
        
        backup_metadata = self.manifest[backup_id]
        backup_path = Path(backup_metadata['backup_directory'])
        
        try:
            # Remove backup directory
            if backup_path.exists():
                shutil.rmtree(backup_path)
            
            # Remove from manifest
            del self.manifest[backup_id]
            self._save_manifest()
            
            logger.info(f"Backup deleted: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete backup {backup_id}: {str(e)}")
            return False
    
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """Clean up old backups, keeping only the most recent ones"""
        
        backups = self.list_backups()
        
        if len(backups) <= keep_count:
            return 0
        
        backups_to_delete = backups[keep_count:]
        deleted_count = 0
        
        for backup in backups_to_delete:
            if self.delete_backup(backup['id']):
                deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old backups")
        return deleted_count
    
    def get_backup_info(self, backup_id: str) -> Optional[Dict]:
        """Get detailed information about a backup"""
        
        if backup_id not in self.manifest:
            return None
        
        backup_metadata = self.manifest[backup_id]
        backup_path = Path(backup_metadata['backup_directory'])
        
        # Check if backup still exists
        if not backup_path.exists():
            logger.warning(f"Backup directory missing: {backup_path}")
            backup_metadata['status'] = 'missing'
        
        # Calculate backup size
        try:
            total_size = sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
            backup_metadata['size_bytes'] = total_size
            backup_metadata['size_human'] = self._format_size(total_size)
        except Exception:
            backup_metadata['size_bytes'] = 0
            backup_metadata['size_human'] = 'Unknown'
        
        return backup_metadata
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
