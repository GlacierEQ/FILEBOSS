"""
Local filesystem data source implementation.
Handles scanning and processing of files from local disk.
"""
import os
import stat
import mimetypes
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from pydantic import validator, Field

from .base import (
    BaseSource, SourceConfig, SourceFileInfo,
    SourceConfigError, SourceConnectionError, SourcePermissionError
)
from config.settings import settings

class LocalFSConfig(SourceConfig):
    """Configuration for local filesystem source."""
    source_type: str = "local_fs"
    
    # Override base path to be required for local FS
    base_path: str = Field(..., description="Base directory path to scan")
    
    # Symlink handling
    follow_symlinks: bool = False
    
    # Special handling for system files
    skip_system_files: bool = True
    skip_temp_files: bool = True
    
    # File attributes to read
    read_file_attributes: bool = True
    
    @validator('base_path')
    def validate_base_path(cls, v):
        """Validate that base_path exists and is readable."""
        path = Path(v).expanduser().absolute()
        if not path.exists():
            raise ValueError(f"Base path does not exist: {v}")
        if not path.is_dir():
            raise ValueError(f"Base path is not a directory: {v}")
        try:
            # Test read access
            next(path.iterdir())
        except (PermissionError, OSError) as e:
            raise ValueError(f"Cannot read base path {v}: {str(e)}")
        return str(path)

class LocalFilesystemSource(BaseSource):
    """
    Data source implementation for local filesystem.
    
    Handles scanning and processing of files from local disk with support for
    various file attributes, symlinks, and system file filtering.
    """
    
    config: LocalFSConfig
    
    @classmethod
    def get_config_schema(cls) -> type[SourceConfig]:
        """Return the configuration model for this source type."""
        return LocalFSConfig
    
    async def _connect(self) -> None:
        """No connection needed for local filesystem."""
        self.base_path = Path(self.config.base_path).expanduser().absolute()
        self.logger.info(f"Initialized local filesystem source at {self.base_path}")
    
    async def _disconnect(self) -> None:
        """No disconnection needed for local filesystem."""
        pass
    
    async def list_files(
        self, 
        path: Optional[str] = None, 
        recursive: bool = False,
        include_metadata: bool = True
    ) -> List[SourceFileInfo]:
        """
        List files in the specified path.
        
        Args:
            path: Path relative to base_path. If None, uses base_path.
            recursive: If True, list files recursively.
            include_metadata: If True, include file metadata.
            
        Returns:
            List of file information objects.
        """
        if not self.connected:
            await self.connect()
            
        full_path = self._resolve_path(path)
        results = []
        
        try:
            if recursive:
                for root, dirs, files in os.walk(full_path, followlinks=self.config.follow_symlinks):
                    # Skip system and temporary directories if configured
                    if self._should_skip_directory(Path(root).name):
                        dirs[:] = []  # Don't recurse into this directory
                        continue
                        
                    for name in files:
                        file_path = Path(root) / name
                        try:
                            file_info = await self._get_file_info(file_path, include_metadata)
                            if file_info:
                                results.append(file_info)
                        except (PermissionError, OSError) as e:
                            self.logger.warning(f"Skipping inaccessible file {file_path}: {str(e)}")
            else:
                if not full_path.exists():
                    raise FileNotFoundError(f"Path not found: {full_path}")
                    
                for entry in full_path.iterdir():
                    try:
                        if entry.is_file() or (entry.is_symlink() and self.config.follow_symlinks):
                            file_info = await self._get_file_info(entry, include_metadata)
                            if file_info:
                                results.append(file_info)
                    except (PermissionError, OSError) as e:
                        self.logger.warning(f"Skipping inaccessible file {entry}: {str(e)}")
                        
            return results
            
        except Exception as e:
            self.logger.error(f"Error listing files in {path}: {str(e)}")
            raise
    
    async def get_file(
        self, 
        path: str,
        download: bool = False
    ) -> Optional[bytes | SourceFileInfo]:
        """
        Get file content or metadata.
        
        Args:
            path: Path relative to base_path.
            download: If True, return file content as bytes. If False, return metadata only.
            
        Returns:
            File content as bytes if download=True, otherwise SourceFileInfo.
            Returns None if file not found or inaccessible.
        """
        if not self.connected:
            await self.connect()
            
        full_path = self._resolve_path(path)
        
        try:
            if not full_path.exists():
                return None
                
            if download:
                try:
                    return full_path.read_bytes()
                except (PermissionError, OSError) as e:
                    self.logger.error(f"Cannot read file {path}: {str(e)}")
                    raise SourcePermissionError(f"Cannot read file {path}: {str(e)}")
            else:
                return await self._get_file_info(full_path, include_metadata=True)
                
        except Exception as e:
            self.logger.error(f"Error getting file {path}: {str(e)}")
            raise
    
    def _resolve_path(self, path: Optional[str]) -> Path:
        """Resolve a path relative to the base path."""
        if path is None:
            return self.base_path
            
        # Prevent directory traversal
        try:
            resolved = (self.base_path / path).resolve()
            # Ensure the resolved path is still within the base path
            if self.base_path not in resolved.parents and resolved != self.base_path:
                raise ValueError(f"Path {path} resolves outside base directory")
            return resolved
        except (ValueError, RuntimeError) as e:
            raise ValueError(f"Invalid path: {path}") from e
    
    async def _get_file_info(
        self, 
        path: Path,
        include_metadata: bool = True
    ) -> Optional[SourceFileInfo]:
        """
        Get file information for a single file.
        
        Args:
            path: Path to the file.
            include_metadata: If True, include file metadata.
            
        Returns:
            SourceFileInfo or None if the file should be skipped.
        """
        try:
            # Skip files that don't exist or are broken symlinks
            if not path.exists():
                return None
                
            # Get file stats
            stat_info = path.stat()
            is_symlink = path.is_symlink()
            
            # Skip system/temporary files if configured
            if self._should_skip_file(path.name):
                return None
                
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(str(path))
            
            # Get file metadata
            extra = {}
            if include_metadata and self.config.read_file_attributes:
                try:
                    extra.update(self._get_extended_attributes(path))
                except Exception as e:
                    self.logger.debug(f"Could not read extended attributes for {path}: {str(e)}")
            
            # Create file info
            file_info = SourceFileInfo(
                path=str(path.relative_to(self.base_path)),
                name=path.name,
                size=stat_info.st_size,
                is_dir=path.is_dir(),
                is_file=path.is_file(),
                is_symlink=is_symlink,
                created=datetime.fromtimestamp(stat_info.st_ctime),
                modified=datetime.fromtimestamp(stat_info.st_mtime),
                accessed=datetime.fromtimestamp(stat_info.st_atime),
                owner=self._get_owner(stat_info.st_uid),
                group=self._get_group(stat_info.st_gid),
                permissions=oct(stat_info.st_mode)[-3:],
                mime_type=mime_type,
                etag=f"{stat_info.st_ino}-{int(stat_info.st_mtime)}",
                version=None,
                extra=extra
            )
            
            # Skip files that don't match filters
            if not self._should_process_file(file_info):
                return None
                
            return file_info
            
        except (PermissionError, OSError) as e:
            self.logger.warning(f"Cannot access file {path}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting file info for {path}: {str(e)}")
            return None
    
    def _get_extended_attributes(self, path: Path) -> Dict[str, Any]:
        """Get extended file attributes if available."""
        attrs = {}
        
        try:
            # Get file flags (Unix-like systems)
            if hasattr(os, 'statvfs'):
                statvfs = os.statvfs(path)
                attrs['flags'] = statvfs.f_flag
                
            # Get Windows file attributes
            if hasattr(os, 'stat') and hasattr(os.stat_result, 'st_file_attributes'):
                stat_info = os.stat(path)
                if hasattr(stat_info, 'st_file_attributes'):
                    attrs['win_attributes'] = stat_info.st_file_attributes
                    
            # Get additional metadata using stat
            stat_info = os.stat(path)
            attrs.update({
                'inode': stat_info.st_ino,
                'device': stat_info.st_dev,
                'nlink': stat_info.st_nlink,
                'mode': stat.S_IMODE(stat_info.st_mode),
            })
            
        except Exception as e:
            self.logger.debug(f"Could not get extended attributes for {path}: {str(e)}")
            
        return attrs
    
    def _get_owner(self, uid: int) -> str:
        """Get username from UID."""
        try:
            import pwd
            return pwd.getpwuid(uid).pw_name
        except (ImportError, KeyError):
            return str(uid)
    
    def _get_group(self, gid: int) -> str:
        """Get group name from GID."""
        try:
            import grp
            return grp.getgrgid(gid).gr_name
        except (ImportError, KeyError):
            return str(gid)
    
    def _should_skip_file(self, filename: str) -> bool:
        """Determine if a file should be skipped based on its name."""
        # Skip system files
        if self.config.skip_system_files and filename.startswith(('.', '~$')):
            return True
            
        # Skip temporary files
        if self.config.skip_temp_files and (
            filename.endswith(('.tmp', '.temp', '.swp', '.swp', '.swx', '~')) or
            filename.startswith('~$') or
            (filename.startswith('._') and len(filename) > 2)
        ):
            return True
            
        return False
    
    def _should_skip_directory(self, dirname: str) -> bool:
        """Determine if a directory should be skipped."""
        # Skip system directories
        if self.config.skip_system_files and dirname.startswith(('.', '~')):
            return True
            
        # Skip common temporary/system directories
        skip_dirs = {
            'node_modules', '__pycache__', '.git', '.svn', '.hg', '.idea',
            '.vscode', 'venv', 'env', '.env', 'temp', 'tmp', 'cache',
            'thumbs.db', 'desktop.ini', '.DS_Store', 'Thumbs.db'
        }
        
        return dirname.lower() in skip_dirs
