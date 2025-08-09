""
Base Google Workspace connector for APEX MANUS.
"""
import os
import json
from typing import Any, Dict, List, Optional, Set, Union
from datetime import datetime, timedelta
import logging

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

from ...core.base_integration import BaseIntegration, IntegrationConfig
from ...connectors.base_connector import BaseConnector
from ...models.base import BaseResource, ResourceType, SyncStatus
from ...utils import retry_async, normalize_url, sanitize_dict

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the token.json file
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.modify',
]

class GoogleWorkspaceConfig(IntegrationConfig):
    """Configuration for Google Workspace integration."""
    client_secrets_file: str = "client_secrets.json"
    token_file: str = "token.json"
    scopes: List[str] = SCOPES
    default_domain: Optional[str] = None
    user_email: Optional[str] = None
    impersonate_user: Optional[str] = None
    subject: Optional[str] = None
    quota_project_id: Optional[str] = None
    
    class Config:
        env_prefix = "GOOGLE_WORKSPACE_"

class GoogleWorkspaceConnector(BaseConnector):
    """
    Base connector for Google Workspace services.
    
    Handles authentication and provides common functionality for all
    Google Workspace APIs.
    """
    
    def __init__(self, config: Optional[GoogleWorkspaceConfig] = None):
        """Initialize the Google Workspace connector."""
        super().__init__(config or GoogleWorkspaceConfig())
        self.service_name = "Google Workspace"
        self.base_url = "https://www.googleapis.com"
        self.auth_type = "oauth2"
        self.rate_limit = 100  # Google's quota is typically 1000 requests per 100 seconds
        self._services: Dict[str, Resource] = {}
        self._creds: Optional[Credentials] = None
    
    @property
    def config(self) -> GoogleWorkspaceConfig:
        """Get the configuration."""
        return self._config
    
    @config.setter
    def config(self, value: GoogleWorkspaceConfig) -> None:
        """Set the configuration."""
        self._config = value
    
    async def connect(self, **kwargs) -> bool:
        """
        Authenticate with Google Workspace.
        
        Args:
            **kwargs: Additional connection parameters
            
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        try:
            self._creds = await self._get_credentials()
            return True
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Workspace: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Disconnect from Google Workspace."""
        self._services.clear()
        self._creds = None
    
    async def test_connection(self) -> bool:
        """
        Test the connection to Google Workspace.
        
        Returns:
            bool: True if the connection is working, False otherwise
        """
        try:
            if not self._creds or not self._creds.valid:
                await self.connect()
                
            service = await self.get_service('drive', 'v3')
            about = service.about().get(fields='user').execute()
            logger.info(f"Connected to Google Workspace as {about.get('user', {}).get('emailAddress')}")
            return True
        except Exception as e:
            logger.error(f"Google Workspace connection test failed: {e}")
            return False
    
    async def get_service(self, service_name: str, version: str, **kwargs) -> Resource:
        """
        Get a Google API service client.
        
        Args:
            service_name: Name of the Google API service (e.g., 'drive', 'docs')
            version: API version (e.g., 'v3', 'v1')
            **kwargs: Additional arguments to pass to the service builder
            
        Returns:
            Resource: The Google API service client
            
        Raises:
            Exception: If the service cannot be created
        """
        cache_key = f"{service_name}:{version}"
        
        if cache_key not in self._services:
            try:
                if not self._creds or not self._creds.valid:
                    await self.connect()
                
                self._services[cache_key] = build(
                    service_name,
                    version,
                    credentials=self._creds,
                    cache_discovery=False,
                    **kwargs
                )
            except Exception as e:
                logger.error(f"Failed to create {service_name} service: {e}")
                raise
        
        return self._services[cache_key]
    
    async def _get_credentials(self) -> Credentials:
        """
        Get valid user credentials from storage or prompt for login.
        
        Returns:
            Credentials: The obtained credentials
            
        Raises:
            Exception: If credentials cannot be obtained
        """
        creds = None
        
        # Load existing credentials if they exist
        if os.path.exists(self.config.token_file):
            try:
                creds = Credentials.from_authorized_user_file(
                    self.config.token_file, 
                    self.config.scopes
                )
            except Exception as e:
                logger.warning(f"Error loading credentials: {e}")
        
        # If there are no (valid) credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Error refreshing credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.config.client_secrets_file):
                    raise FileNotFoundError(
                        f"Client secrets file not found: {self.config.client_secrets_file}"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.config.client_secrets_file,
                    self.config.scopes
                )
                
                # Note: This will open a browser window for authentication
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.config.token_file, 'w') as token:
                token.write(creds.to_json())
        
        return creds
    
    async def _execute_api_call(
        self, 
        service_name: str,
        version: str,
        method: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute a Google API call with retry logic.
        
        Args:
            service_name: Name of the Google API service
            version: API version
            method: Method to call on the service (e.g., 'files.list')
            **kwargs: Arguments to pass to the method
            
        Returns:
            Dict containing the API response
            
        Raises:
            Exception: If the API call fails after retries
        """
        service = await self.get_service(service_name, version)
        
        # Split method into service and method (e.g., 'files.list' -> service.files().list())
        parts = method.split('.')
        resource = service
        
        for part in parts[:-1]:
            resource = getattr(resource, part)()
        
        method_call = getattr(resource, parts[-1])
        
        # Execute the API call with retry logic
        async def _call() -> Dict[str, Any]:
            try:
                request = method_call(**kwargs)
                return await self._execute_request(request)
            except HttpError as e:
                if e.resp.status == 404:
                    logger.warning(f"Resource not found: {e.uri}")
                    return {}
                raise
        
        return await retry_async(
            _call,
            max_attempts=3,
            delay=1.0,
            backoff=2.0,
            exceptions=(HttpError,)
        )
    
    async def _execute_request(self, request) -> Dict[str, Any]:
        """
        Execute a Google API request.
        
        Args:
            request: The Google API request to execute
            
        Returns:
            Dict containing the API response
            
        Raises:
            Exception: If the request fails
        """
        response = request.execute()
        return response if response is not None else {}
    
    async def _paginate_api_call(
        self,
        service_name: str,
        version: str,
        method: str,
        items_key: str = 'items',
        page_size: int = 100,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Execute a paginated Google API call.
        
        Args:
            service_name: Name of the Google API service
            version: API version
            method: Method to call on the service
            items_key: Key in the response that contains the items
            page_size: Number of items per page
            **kwargs: Additional arguments to pass to the method
            
        Returns:
            List of items from all pages
        """
        all_items = []
        page_token = None
        
        while True:
            try:
                response = await self._execute_api_call(
                    service_name=service_name,
                    version=version,
                    method=method,
                    pageSize=page_size,
                    pageToken=page_token,
                    **kwargs
                )
                
                items = response.get(items_key, [])
                all_items.extend(items)
                
                page_token = response.get('nextPageToken')
                if not page_token or not items:
                    break
                    
            except HttpError as e:
                if e.resp.status == 404:
                    break
                raise
        
        return all_items
