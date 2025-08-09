"""
Google Drive data source implementation.
Handles authentication, file listing, and content retrieval from Google Drive.
"""
import os
import json
import logging
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, AsyncGenerator, cast
from urllib.parse import urlparse, parse_qs

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

from .base import BaseSource, SourceConfig, SourceFileInfo, SourceConfigError, SourceConnectionError, SourcePermissionError
from core.models import Artifact, ArtifactSource, FileMetadata, ArtifactType
from config import settings

# Google Drive API scopes
SCOPES = [
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.file',
]

# Google MIME type mappings
GOOGLE_MIME_TYPES = {
    'application/vnd.google-apps.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'application/vnd.google-apps.drawing': 'image/png',
    'application/vnd.google-apps.script': 'application/vnd.google-apps.script+json',
    'application/vnd.google-apps.form': 'application/zip',
    'application/vnd.google-apps.folder': 'inode/directory',
}

class GoogleDriveConfig(SourceConfig):
    """Configuration for Google Drive source."""
    source_type: str = "google_drive"
    
    # Authentication
    client_secrets_file: str = Field(
        ...,
        description="Path to client_secrets.json file from Google Cloud Console"
    )
    token_file: str = Field(
        default="token.json",
        description="Path to store the OAuth2 token"
    )
    
    # Drive settings
    shared_drive_id: Optional[str] = Field(
        None,
        description="ID of a shared drive to scan (for G Suite accounts)"
    )
    include_team_drives: bool = Field(
        True,
        description="Include files from shared drives"
    )
    export_formats: Dict[str, str] = Field(
        default_factory=lambda: {
            'application/vnd.google-apps.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        },
        description="Mappings from Google MIME types to export formats"
    )
    
    # File filtering
    include_trashed: bool = False
    include_shared: bool = True
    
    @validator('client_secrets_file')
    def validate_client_secrets_file(cls, v):
        """Validate that the client secrets file exists."""
        path = Path(v).expanduser().absolute()
        if not path.exists():
            raise ValueError(f"Client secrets file not found: {v}")
        return str(path)
    
    @validator('token_file')
    def validate_token_file(cls, v):
        """Ensure token file path is absolute."""
        return str(Path(v).expanduser().absolute())

class GoogleDriveSource(BaseSource):
    """
    Data source implementation for Google Drive.
    
    Handles authentication, file listing, and content retrieval from Google Drive,
    including support for Google Workspace file formats and shared drives.
    """
    
    config: GoogleDriveConfig
    _service = None
    _root_id = None
    
    @classmethod
    def get_config_schema(cls) -> type[SourceConfig]:
        """Return the configuration model for this source type."""
        return GoogleDriveConfig
    
    async def _connect(self) -> None:
        """Authenticate with Google Drive and initialize the API client."""
        creds = None
        token_path = Path(self.config.token_file)
        
        # Load existing token if available
        if token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    str(token_path), SCOPES
                )
                self.logger.debug("Loaded credentials from token file")
            except Exception as e:
                self.logger.warning(f"Error loading credentials: {e}")
        
        # If no valid credentials, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self.logger.debug("Refreshed credentials")
                except Exception as e:
                    self.logger.warning(f"Error refreshing token: {e}")
                    creds = None
            
            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.config.client_secrets_file, SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    self.logger.info("Successfully authenticated with Google Drive")
                    
                    # Save the credentials for the next run
                    token_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(token_path, 'w') as token:
                        token.write(creds.to_json())
                    self.logger.debug(f"Saved credentials to {token_path}")
                except Exception as e:
                    raise SourceConnectionError(
                        f"Failed to authenticate with Google Drive: {str(e)}"
                    ) from e
        
        # Build the Drive API client
        try:
            self._service = build('drive', 'v3', credentials=creds, cache_discovery=False)
            
            # Get root folder ID
            about = self._service.about().get(fields='*').execute()
            self._root_id = about.get('rootFolderId')
            
            self.logger.info(
                f"Connected to Google Drive as {about.get('user', {}).get('emailAddress')}"
            )
            self.logger.debug(f"Root folder ID: {self._root_id}")
            
        except Exception as e:
            raise SourceConnectionError(
                f"Failed to initialize Google Drive client: {str(e)}"
            ) from e
    
    async def _disconnect(self) -> None:
        """Clean up resources."""
        self._service = None
        self._root_id = None
    
    async def list_files(
        self, 
        path: Optional[str] = None, 
        recursive: bool = False,
        include_metadata: bool = True
    ) -> List[SourceFileInfo]:
        """
        List files in the specified path.
        
        Args:
            path: Folder ID or path from root (e.g., 'root' or 'folder_id')
            recursive: If True, list files recursively
            include_metadata: If True, include file metadata
            
        Returns:
            List of file information objects
        """
        if not self._service:
            await self.connect()
        
        folder_id = path or self._root_id
        if not folder_id:
            folder_id = 'root'
        
        try:
            # If path is a path string, resolve it to a folder ID
            if path and not path.startswith(('http', 'drive.google.com')) and path != 'root':
                folder_id = await self._resolve_path(path)
            
            # Handle Google Drive links
            elif 'drive.google.com' in str(path):
                folder_id = self._extract_file_id_from_url(str(path))
            
            self.logger.debug(f"Listing files in folder ID: {folder_id}")
            
            # List files in the folder
            files = []
            page_token = None
            
            while True:
                query = f"'{folder_id}' in parents and trashed = false"
                if not self.config.include_trashed:
                    query += " and trashed = false"
                
                # Include shared files if configured
                if not self.config.include_shared:
                    query += " and 'me' in owners"
                
                # Build request
                request = self._service.files().list(
                    q=query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, modifiedTime, createdTime, size, md5Checksum, '
                           'webViewLink, webContentLink, fileExtension, originalFilename, owners, shared, '
                           'sharedWithMeTime, sharingUser, lastModifyingUser, capabilities, '
                           'version, headRevisionId, description, properties, appProperties, '
                           'contentHints, imageMediaMetadata, videoMediaMetadata, '
                           'exportLinks, parents, permissions, teamDriveId, driveId, '
                           'shortcutDetails, trashed, explicitlyTrashed, '
                           'spaces, isAppAuthorized, hasAugmentedPermissions, '
                           'viewedByMe, viewedByMeTime, viewersCanCopyContent, '
                           'writersCanShare, permissions, permissionIds, '
                           'hasThumbnail, thumbnailLink, thumbnailVersion, '
                           'modifiedByMe, modifiedByMeTime, quotaBytesUsed, '
                           'ownedByMe, isAppAuthorized, sharingUser, sharingUser',
                    supportsAllDrives=self.config.include_team_drives,
                    includeItemsFromAllDrives=self.config.include_team_drives,
                    pageToken=page_token,
                    pageSize=1000
                )
                
                try:
                    response = request.execute()
                    files.extend(response.get('files', []))
                    page_token = response.get('nextPageToken')
                    
                    if not page_token:
                        break
                        
                except HttpError as e:
                    error_details = json.loads(e.content).get('error', {})
                    if error_details.get('code') == 403 and 'rateLimitExceeded' in str(e):
                        self.logger.warning("Rate limit exceeded, waiting before retry...")
                        await asyncio.sleep(5)  # Wait 5 seconds before retry
                        continue
                    raise
                
            # Convert to SourceFileInfo objects
            result = []
            for file in files:
                try:
                    file_info = self._to_file_info(file)
                    if file_info:
                        result.append(file_info)
                        
                        # If recursive and this is a folder, process its contents
                        if recursive and file_info.is_dir:
                            try:
                                sub_files = await self.list_files(
                                    path=file['id'],
                                    recursive=True,
                                    include_metadata=include_metadata
                                )
                                result.extend(sub_files)
                            except Exception as e:
                                self.logger.warning(
                                    f"Error listing contents of {file.get('name')} ({file.get('id')}): {str(e)}"
                                )
                except Exception as e:
                    self.logger.warning(
                        f"Error processing file {file.get('name')} ({file.get('id')}): {str(e)}"
                    )
            
            return result
            
        except Exception as e:
            raise SourceConnectionError(
                f"Failed to list files in {path or 'root'}: {str(e)}"
            ) from e
    
    async def get_file(
        self, 
        file_id: str,
        download: bool = False
    ) -> Optional[Union[bytes, SourceFileInfo]]:
        """
        Get file content or metadata.
        
        Args:
            file_id: Google Drive file ID or URL
            download: If True, download file content. If False, return metadata only.
            
        Returns:
            File content as bytes if download=True, otherwise SourceFileInfo.
            Returns None if file not found.
        """
        if not self._service:
            await self.connect()
        
        try:
            # Extract file ID from URL if needed
            if 'drive.google.com' in file_id:
                file_id = self._extract_file_id_from_url(file_id)
            
            # Get file metadata
            file = self._service.files().get(
                fileId=file_id,
                supportsAllDrives=self.config.include_team_drives,
                fields='*'
            ).execute()
            
            if not file:
                return None
            
            file_info = self._to_file_info(file)
            
            if not download:
                return file_info
            
            # Download file content
            return await self._download_file(file)
            
        except HttpError as e:
            if e.resp.status == 404:
                return None
            raise SourceConnectionError(
                f"Failed to get file {file_id}: {str(e)}"
            ) from e
        except Exception as e:
            raise SourceConnectionError(
                f"Error getting file {file_id}: {str(e)}"
            ) from e
    
    async def _download_file(self, file: Dict[str, Any]) -> bytes:
        """Download file content from Google Drive."""
        mime_type = file.get('mimeType', '')
        file_id = file['id']
        
        # Handle Google Workspace files (Docs, Sheets, etc.)
        if mime_type.startswith('application/vnd.google-apps.') and mime_type != 'application/vnd.google-apps.folder':
            export_mime = self.config.export_formats.get(mime_type)
            if not export_mime:
                raise ValueError(f"No export format configured for {mime_type}")
            
            self.logger.debug(f"Exporting {file.get('name')} as {export_mime}")
            request = self._service.files().export_media(
                fileId=file_id,
                mimeType=export_mime
            )
        else:
            # Regular file download
            request = self._service.files().get_media(fileId=file_id)
        
        # Download to memory
        try:
            with tempfile.SpooledTemporaryFile(max_size=100*1024*1024) as fh:  # 100MB in memory
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                
                while not done:
                    status, done = downloader.next_chunk()
                    self.logger.debug(
                        f"Download {file.get('name')}: "
                        f"{int(status.progress() * 100)}%"
                    )
                
                fh.seek(0)
                return fh.read()
                
        except Exception as e:
            raise SourceConnectionError(
                f"Failed to download file {file.get('name')} ({file_id}): {str(e)}"
            ) from e
    
    def _to_file_info(self, file: Dict[str, Any]) -> Optional[SourceFileInfo]:
        """Convert Google Drive file metadata to SourceFileInfo."""
        try:
            file_id = file['id']
            name = file.get('name', 'Untitled')
            mime_type = file.get('mimeType', 'application/octet-stream')
            is_dir = mime_type == 'application/vnd.google-apps.folder'
            
            # Get file size (for Google Workspace files, use the exported size if available)
            size = int(file.get('size', 0))
            
            # Handle Google Workspace files
            if mime_type.startswith('application/vnd.google-apps.') and not is_dir:
                export_mime = self.config.export_formats.get(mime_type)
                if export_mime and 'exportLinks' in file and export_mime in file['exportLinks']:
                    # Use the export URL to get an estimate of the file size
                    # This is a placeholder - actual size may vary based on content
                    size = file.get('quotaBytesUsed', size)
            
            # Get timestamps
            created = self._parse_datetime(file.get('createdTime'))
            modified = self._parse_datetime(file.get('modifiedTime'))
            viewed = self._parse_datetime(file.get('viewedByMeTime'))
            
            # Build extra metadata
            extra = {
                'id': file_id,
                'mimeType': mime_type,
                'webViewLink': file.get('webViewLink'),
                'webContentLink': file.get('webContentLink'),
                'shared': file.get('shared', False),
                'ownedByMe': file.get('ownedByMe', False),
                'owners': [owner.get('emailAddress') for owner in file.get('owners', [])],
                'permissions': file.get('permissions', []),
                'capabilities': file.get('capabilities', {}),
                'version': file.get('version'),
                'headRevisionId': file.get('headRevisionId'),
                'md5Checksum': file.get('md5Checksum'),
                'quotaBytesUsed': file.get('quotaBytesUsed'),
                'teamDriveId': file.get('teamDriveId'),
                'driveId': file.get('driveId'),
                'trashed': file.get('trashed', False),
                'explicitlyTrashed': file.get('explicitlyTrashed', False),
                'viewedByMe': file.get('viewedByMe', False),
                'viewedByMeTime': viewed.isoformat() if viewed else None,
                'sharingUser': file.get('sharingUser', {}).get('emailAddress') if 'sharingUser' in file else None,
            }
            
            # Add media metadata if available
            if 'imageMediaMetadata' in file:
                extra['imageMediaMetadata'] = file['imageMediaMetadata']
            if 'videoMediaMetadata' in file:
                extra['videoMediaMetadata'] = file['videoMediaMetadata']
            
            # Create file info
            return SourceFileInfo(
                path=file_id,  # Using ID as path for now
                name=name,
                size=size,
                is_dir=is_dir,
                is_file=not is_dir,
                is_symlink=False,
                created=created,
                modified=modified,
                accessed=viewed or created,
                owner=file.get('owners', [{}])[0].get('emailAddress') if file.get('owners') else None,
                permissions=json.dumps(file.get('permissions', [])),
                mime_type=mime_type,
                etag=file.get('etag', ''),
                version=file.get('version'),
                extra=extra
            )
            
        except Exception as e:
            self.logger.error(f"Error converting Google Drive file to SourceFileInfo: {str(e)}")
            return None
    
    async def _resolve_path(self, path: str) -> str:
        """Resolve a path string to a Google Drive file ID."""
        if not path or path == '/':
            return self._root_id or 'root'
            
        parts = [p for p in path.strip('/').split('/') if p]
        current_id = self._root_id or 'root'
        
        for i, part in enumerate(parts):
            query = f"name = '{part}' and '{current_id}' in parents and trashed = false"
            if not self.config.include_trashed:
                query += " and trashed = false"
                
            results = self._service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType)',
                supportsAllDrives=self.config.include_team_drives,
                includeItemsFromAllDrives=self.config.include_team_drives,
                pageSize=1
            ).execute()
            
            files = results.get('files', [])
            if not files:
                raise FileNotFoundError(f"Path not found: {'/'.join(parts[:i+1])}")
                
            current_id = files[0]['id']
            
        return current_id
    
    def _extract_file_id_from_url(self, url: str) -> str:
        """Extract file ID from Google Drive URL."""
        # Handle different URL formats
        if 'drive.google.com' in url:
            if 'file/d/' in url:
                # Format: https://drive.google.com/file/d/FILE_ID/view?usp=sharing
                file_id = url.split('file/d/')[1].split('/')[0]
            elif 'open?id=' in url:
                # Format: https://drive.google.com/open?id=FILE_ID
                file_id = url.split('open?id=')[1].split('&')[0]
            elif 'uc?export=download' in url or 'uc?id=' in url:
                # Format: https://drive.google.com/uc?export=download&id=FILE_ID
                parsed = urlparse(url)
                params = parse_qs(parsed.query)
                file_id = params.get('id', [''])[0]
            else:
                raise ValueError(f"Unsupported Google Drive URL format: {url}")
        else:
            # Assume it's already a file ID
            file_id = url
            
        if not file_id:
            raise ValueError(f"Could not extract file ID from URL: {url}")
            
        return file_id
    
    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """Parse Google Drive datetime string to datetime object."""
        if not dt_str:
            return None
            
        try:
            # Format: '2023-01-01T12:00:00.000Z'
            return datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            try:
                # Fallback format
                return datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                return None
    
    async def to_artifact(self, file_info: SourceFileInfo) -> Optional[Artifact]:
        """Convert a source file to an Artifact."""
        try:
            # Skip directories for now (they're handled by the parent)
            if file_info.is_dir:
                return None
                
            # Create artifact source
            source = ArtifactSource(
                source_type=self.config.source_type,
                source_id=file_info.extra.get('id', file_info.path),
                path=file_info.path,
                original_name=file_info.name,
                source_created=file_info.created,
                source_modified=file_info.modified,
                source_metadata={
                    'size': file_info.size,
                    'mime_type': file_info.mime_type,
                    'owner': file_info.owner,
                    'shared': file_info.extra.get('shared', False),
                    'web_view_link': file_info.extra.get('webViewLink'),
                    'web_content_link': file_info.extra.get('webContentLink'),
                    **file_info.extra
                }
            )
            
            # Determine artifact type
            artifact_type = self._get_artifact_type(file_info)
            
            # Create base artifact
            artifact = Artifact(
                artifact_type=artifact_type,
                name=file_info.name,
                file_metadata=FileMetadata(
                    size_bytes=file_info.size,
                    created=file_info.created,
                    modified=file_info.modified,
                    accessed=file_info.accessed,
                    file_type=file_info.extra.get('fileExtension'),
                    mime_type=file_info.mime_type,
                    owner=file_info.owner,
                ),
                content_metadata=ContentMetadata(
                    title=file_info.extra.get('name'),
                    author=file_info.owner,
                    description=file_info.extra.get('description'),
                    has_embedded_files=bool(file_info.extra.get('hasThumbnail')),
                    is_encrypted=file_info.extra.get('capabilities', {}).get('canCopy', True) is False,
                )
            )
            
            # Add source
            artifact.add_source(source)
            
            # Add processing log
            artifact.add_processing_log(
                level="info",
                message=f"Imported from Google Drive",
                details={
                    'source': self.config.name,
                    'file_id': source.source_id,
                    'web_view_link': file_info.extra.get('webViewLink')
                }
            )
            
            return artifact
            
        except Exception as e:
            self.logger.error(f"Error creating artifact from {file_info.path}: {str(e)}", exc_info=True)
            return None
