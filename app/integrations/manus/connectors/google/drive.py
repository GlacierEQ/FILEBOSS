""
Google Drive connector for APEX MANUS.
"""
import os
import io
import mimetypes
from typing import Dict, List, Optional, Union, BinaryIO, Any
from datetime import datetime
import logging

from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

from .base import GoogleWorkspaceConnector, GoogleWorkspaceConfig
from ...models.base import BaseResource, ResourceType, SyncStatus
from ...utils import normalize_url, sanitize_dict

logger = logging.getLogger(__name__)

class GoogleDriveConfig(GoogleWorkspaceConfig):
    """Configuration for Google Drive integration."""
    sync_root_folder_id: str = "root"
    sync_include_shared: bool = True
    sync_mime_types: List[str] = [
        # Google Docs
        'application/vnd.google-apps.document',
        # Google Sheets
        'application/vnd.google-apps.spreadsheet',
        # Google Slides
        'application/vnd.google-apps.presentation',
        # Google Forms
        'application/vnd.google-apps.form',
        # Google Drawings
        'application/vnd.google-apps.drawing',
        # Google Apps Scripts
        'application/vnd.google-apps.script',
        # PDF
        'application/pdf',
        # Microsoft Word
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        # Microsoft Excel
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        # Microsoft PowerPoint
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        # Plain Text
        'text/plain',
    ]
    sync_exclude_folders: List[str] = [
        'node_modules',
        'venv',
        '__pycache__',
        '.git',
        '.idea',
        '.vscode',
    ]
    
    class Config:
        env_prefix = "GOOGLE_DRIVE_"

class GoogleDriveConnector(GoogleWorkspaceConnector):
    """
    Google Drive connector for APEX MANUS.
    
    Handles file and folder operations, including:
    - Listing files and folders
    - Uploading and downloading files
    - Creating and updating files
    - Managing file permissions
    - Syncing with local filesystem
    """
    
    def __init__(self, config: Optional[GoogleDriveConfig] = None):
        """Initialize the Google Drive connector."""
        super().__init__(config or GoogleDriveConfig())
        self.service_name = "Google Drive"
        self._drive_service = None
    
    @property
    def config(self) -> GoogleDriveConfig:
        """Get the configuration."""
        return self._config
    
    @config.setter
    def config(self, value: GoogleDriveConfig) -> None:
        """Set the configuration."""
        self._config = value
    
    async def get_drive_service(self):
        """Get the Google Drive service client."""
        if not self._drive_service:
            self._drive_service = await self.get_service('drive', 'v3')
        return self._drive_service
    
    async def list_files(
        self,
        query: str = None,
        folder_id: str = None,
        include_shared: bool = None,
        mime_types: List[str] = None,
        page_size: int = 100,
        fields: str = "files(id, name, mimeType, modifiedTime, createdTime, size, webViewLink, parents, shared, owners, permissions, capabilities)",
    ) -> List[Dict[str, Any]]:
        """
        List files in Google Drive.
        
        Args:
            query: Search query (see https://developers.google.com/drive/api/v3/ref-search-terms)
            folder_id: ID of the folder to list files from (default: root)
            include_shared: Whether to include shared files
            mime_types: List of MIME types to filter by
            page_size: Number of files to return per page
            fields: Fields to include in the response
            
        Returns:
            List of file metadata dictionaries
        """
        drive = await self.get_drive_service()
        
        # Build query
        query_parts = []
        
        # Folder filter
        if folder_id:
            query_parts.append(f"'{folder_id}' in parents")
        
        # MIME type filter
        if mime_types:
            mime_quotes = [f"'{mime}'" for mime in mime_types]
            query_parts.append(f"mimeType in ({','.join(mime_quotes)})")
        
        # Add user's query if provided
        if query:
            query_parts.append(f"({query})")
        
        # Combine query parts
        full_query = " and ".join(query_parts) if query_parts else None
        
        # Execute query
        try:
            results = []
            page_token = None
            
            while True:
                # Prepare parameters
                params = {
                    'q': full_query,
                    'pageSize': page_size,
                    'fields': f"nextPageToken, {fields}",
                    'supportsAllDrives': True,
                    'includeItemsFromAllDrives': include_shared or self.config.sync_include_shared,
                }
                
                if page_token:
                    params['pageToken'] = page_token
                
                # Execute API call
                response = drive.files().list(**params).execute()
                files = response.get('files', [])
                results.extend(files)
                
                # Check for more pages
                page_token = response.get('nextPageToken')
                if not page_token or not files:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            raise
    
    async def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        """
        Get metadata for a file.
        
        Args:
            file_id: ID of the file
            
        Returns:
            File metadata dictionary
        """
        drive = await self.get_drive_service()
        
        try:
            return drive.files().get(
                fileId=file_id,
                fields="*",
                supportsAllDrives=True
            ).execute()
        except Exception as e:
            logger.error(f"Error getting file metadata for {file_id}: {e}")
            raise
    
    async def download_file(
        self, 
        file_id: str, 
        mime_type: str = None,
        export: bool = False
    ) -> bytes:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: ID of the file to download
            mime_type: MIME type to export as (for Google Workspace files)
            export: Whether to export the file (for Google Workspace files)
            
        Returns:
            File content as bytes
        """
        drive = await self.get_drive_service()
        
        try:
            if export or (mime_type and mime_type.startswith('application/vnd.google-apps.')):
                # Export Google Workspace files
                if not mime_type:
                    file_metadata = await self.get_file_metadata(file_id)
                    mime_type = file_metadata.get('mimeType')
                
                # Map Google MIME type to export format
                export_mime = self._get_export_mime_type(mime_type)
                
                request = drive.files().export_media(
                    fileId=file_id,
                    mimeType=export_mime
                )
            else:
                # Download regular files
                request = drive.files().get_media(fileId=file_id)
            
            # Download the file
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                logger.debug(f"Download {int(status.progress() * 100)}%")
            
            return fh.getvalue()
            
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            raise
    
    async def upload_file(
        self,
        name: str,
        content: Union[bytes, str, BinaryIO],
        mime_type: str = None,
        parent_id: str = None,
        file_id: str = None,
        description: str = None,
    ) -> Dict[str, Any]:
        """
        Upload or update a file in Google Drive.
        
        Args:
            name: Name of the file
            content: File content as bytes, string, or file-like object
            mime_type: MIME type of the file
            parent_id: ID of the parent folder
            file_id: ID of the file to update (if updating)
            description: File description
            
        Returns:
            Dictionary containing file metadata
        """
        drive = await self.get_drive_service()
        
        # Determine MIME type if not provided
        if not mime_type:
            mime_type = mimetypes.guess_type(name)[0] or 'application/octet-stream'
        
        # Prepare file metadata
        file_metadata = {
            'name': name,
            'mimeType': mime_type,
        }
        
        if description:
            file_metadata['description'] = description
        
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        try:
            # Convert string content to bytes if needed
            if isinstance(content, str):
                content = content.encode('utf-8')
            
            # Handle file-like objects
            if hasattr(content, 'read'):
                content = content.read()
            
            # Create file-like object from content
            fh = io.BytesIO(content)
            media = MediaIoBaseUpload(
                fh,
                mimetype=mime_type,
                resumable=True
            )
            
            if file_id:
                # Update existing file
                file = drive.files().update(
                    fileId=file_id,
                    body=file_metadata,
                    media_body=media,
                    fields='*',
                    supportsAllDrives=True
                ).execute()
            else:
                # Create new file
                file = drive.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='*',
                    supportsAllDrives=True
                ).execute()
            
            return file
            
        except Exception as e:
            logger.error(f"Error uploading file {name}: {e}")
            raise
    
    async def create_folder(
        self,
        name: str,
        parent_id: str = None,
        description: str = None,
    ) -> Dict[str, Any]:
        """
        Create a folder in Google Drive.
        
        Args:
            name: Name of the folder
            parent_id: ID of the parent folder
            description: Folder description
            
        Returns:
            Dictionary containing folder metadata
        """
        drive = await self.get_drive_service()
        
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder',
        }
        
        if description:
            file_metadata['description'] = description
        
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        try:
            return drive.files().create(
                body=file_metadata,
                fields='*',
                supportsAllDrives=True
            ).execute()
        except Exception as e:
            logger.error(f"Error creating folder {name}: {e}")
            raise
    
    async def delete_file(self, file_id: str) -> bool:
        """
        Delete a file or folder from Google Drive.
        
        Args:
            file_id: ID of the file or folder to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        drive = await self.get_drive_service()
        
        try:
            drive.files().delete(
                fileId=file_id,
                supportsAllDrives=True
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            return False
    
    async def search_files(
        self,
        query: str,
        page_size: int = 100,
        fields: str = "files(id, name, mimeType, modifiedTime, webViewLink)",
    ) -> List[Dict[str, Any]]:
        """
        Search for files in Google Drive.
        
        Args:
            query: Search query (see https://developers.google.com/drive/api/v3/ref-search-terms)
            page_size: Number of results per page
            fields: Fields to include in the response
            
        Returns:
            List of file metadata dictionaries
        """
        return await self.list_files(
            query=query,
            page_size=page_size,
            fields=fields
        )
    
    def _get_export_mime_type(self, mime_type: str) -> str:
        """
        Get the export MIME type for a Google Workspace file.
        
        Args:
            mime_type: Google Workspace MIME type
            
        Returns:
            str: Export MIME type
        """
        export_formats = {
            # Google Docs
            'application/vnd.google-apps.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            # Google Sheets
            'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            # Google Slides
            'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            # Google Drawings
            'application/vnd.google-apps.drawing': 'image/png',
            # Google Apps Scripts
            'application/vnd.google-apps.script': 'application/vnd.google-apps.script+json',
        }
        
        return export_formats.get(mime_type, 'application/pdf')
