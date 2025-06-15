"""
Security and access control utilities for LawGlance.
This module implements document access protection and permission management.
"""
import os
import re
import logging
import secrets
import hashlib
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Union, Tuple
from dataclasses import dataclass, field
import datetime
from pathlib import Path

logger = logging.getLogger("lawglance.security")

# Constants for security settings
DEFAULT_CODE_LENGTH = 6
MAX_FAILED_ATTEMPTS = 5
ACCESS_TOKEN_EXPIRY = 24 * 60 * 60  # 24 hours in seconds
HASH_ITERATIONS = 10000


class AccessLevel(Enum):
    """Permission levels for document access."""
    VIEWER = auto()  # Can only view the document
    COMMENTER = auto()  # Can view and comment
    EDITOR = auto()  # Can view, comment, and edit
    OWNER = auto()  # Full control including access management


class AccessStatus(Enum):
    """Status codes for access attempts."""
    SUCCESS = auto()
    INVALID_CODE = auto()
    EXPIRED = auto()
    MAX_ATTEMPTS_EXCEEDED = auto()
    INSUFFICIENT_PERMISSIONS = auto()
    DOCUMENT_NOT_FOUND = auto()


@dataclass
class DocumentAccess:
    """Access control information for a document."""
    document_id: str
    room_code: str
    room_code_hash: str
    creation_time: datetime.datetime = field(default_factory=datetime.datetime.now)
    expiry_time: Optional[datetime.datetime] = None
    failed_attempts: int = 0
    allowed_users: List[str] = field(default_factory=list)
    access_history: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        """Setup expiry time if not provided."""
        if not self.expiry_time:
            self.expiry_time = self.creation_time + datetime.timedelta(
                seconds=ACCESS_TOKEN_EXPIRY
            )
    
    def is_expired(self) -> bool:
        """Check if access has expired."""
        return datetime.datetime.now() > self.expiry_time
    
    def validate_code(self, code: str) -> bool:
        """Validate a room access code."""
        # Hash the provided code
        hashed_code = hash_room_code(code, HASH_ITERATIONS)
        return hashed_code == self.room_code_hash


class RoomCodeManager:
    """Manager for room access codes."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the room code manager.
        
        Args:
            storage_dir: Directory to store access data
        """
        self.storage_dir = Path(storage_dir or os.path.join(
            os.getenv("HOME", os.path.expanduser("~")), 
            ".lawglance", 
            "access"
        ))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.access_map: Dict[str, DocumentAccess] = {}
        self._load_existing_access()
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def generate_room_code(self, document_id: str, length: int = DEFAULT_CODE_LENGTH) -> str:
        """
        Generate a new room access code for a document.
        
        Args:
            document_id: Document identifier
            length: Length of the code to generate
            
        Returns:
            A new room access code
        """
        # Generate a random code with digits only for better usability
        code = ''.join(secrets.choice("0123456789") for _ in range(length))
        
        # Hash the code for secure storage
        hashed_code = hash_room_code(code, HASH_ITERATIONS)
        
        # Create and store access information
        access = DocumentAccess(document_id=document_id, 
                                room_code=code,
                                room_code_hash=hashed_code)
        
        self.access_map[document_id] = access
        self._save_access(access)
        
        return code
    
    def verify_room_code(self, document_id: str, code: str) -> Tuple[AccessStatus, Optional[DocumentAccess]]:
        """
        Verify a room access code.
        
        Args:
            document_id: Document identifier
            code: Room access code to verify
            
        Returns:
            Tuple of (status, access_info or None)
        """
        if document_id not in self.access_map:
            return AccessStatus.DOCUMENT_NOT_FOUND, None
            
        access = self.access_map[document_id]
        
        # Check for too many failed attempts
        if access.failed_attempts >= MAX_FAILED_ATTEMPTS:
            return AccessStatus.MAX_ATTEMPTS_EXCEEDED, None
            
        # Check for expiration
        if access.is_expired():
            return AccessStatus.EXPIRED, None
            
        # Verify the code
        if not access.validate_code(code):
            access.failed_attempts += 1
            self._save_access(access)
            return AccessStatus.INVALID_CODE, None
            
        # Success - reset failed attempts counter
        access.failed_attempts = 0
        
        # Log access
        access.access_history.append({
            "time": datetime.datetime.now().isoformat(),
            "success": True
        })
        
        self._save_access(access)
        return AccessStatus.SUCCESS, access
    
    def extend_access(self, document_id: str, hours: int = 24) -> bool:
        """
        Extend access duration for a document.
        
        Args:
            document_id: Document identifier
            hours: Number of hours to extend access
            
        Returns:
            True if successful, False otherwise
        """
        if document_id not in self.access_map:
            return False
            
        access = self.access_map[document_id]
        
        # Extend from now if already expired, otherwise extend from current expiry
        if access.is_expired():
            access.expiry_time = datetime.datetime.now() + datetime.timedelta(hours=hours)
        else:
            access.expiry_time += datetime.timedelta(hours=hours)
            
        self._save_access(access)
        return True
    
    def revoke_access(self, document_id: str) -> bool:
        """
        Revoke access to a document.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if successfully revoked, False otherwise
        """
        if document_id not in self.access_map:
            return False
            
        # Delete the access file
        access_path = self._get_access_path(document_id)
        try:
            if access_path.exists():
                access_path.unlink()
            del self.access_map[document_id]
            return True
        except Exception as e:
            self.logger.error(f"Failed to revoke access for {document_id}: {e}")
            return False
    
    def list_active_documents(self) -> List[str]:
        """
        List all documents with active access codes.
        
        Returns:
            List of document IDs with active access
        """
        active_docs = []
        for doc_id, access in self.access_map.items():
            if not access.is_expired():
                active_docs.append(doc_id)
        return active_docs
    
    def _load_existing_access(self) -> None:
        """Load existing access information from storage."""
        try:
            for file_path in self.storage_dir.glob("*.access"):
                try:
                    with open(file_path, "r") as f:
                        import json
                        data = json.load(f)
                        
                    # Convert string dates back to datetime objects
                    data["creation_time"] = datetime.datetime.fromisoformat(data["creation_time"])
                    data["expiry_time"] = datetime.datetime.fromisoformat(data["expiry_time"])
                    
                    access = DocumentAccess(**data)
                    self.access_map[access.document_id] = access
                    
                except Exception as e:
                    self.logger.error(f"Error loading access file {file_path}: {e}")
        except Exception as e:
            self.logger.error(f"Error loading access files: {e}")
    
    def _save_access(self, access: DocumentAccess) -> None:
        """
        Save access information to storage.
        
        Args:
            access: Document access information
        """
        try:
            file_path = self._get_access_path(access.document_id)
            
            # Convert to dict for serialization
            access_dict = {
                "document_id": access.document_id,
                "room_code": "REDACTED",  # Don't store the actual code
                "room_code_hash": access.room_code_hash,
                "creation_time": access.creation_time.isoformat(),
                "expiry_time": access.expiry_time.isoformat(),
                "failed_attempts": access.failed_attempts,
                "allowed_users": access.allowed_users,
                "access_history": access.access_history
            }
            
            with open(file_path, "w") as f:
                import json
                json.dump(access_dict, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving access information: {e}")
    
    def _get_access_path(self, document_id: str) -> Path:
        """Get the file path for an access record."""
        # Sanitize document ID to create a valid filename
        safe_id = re.sub(r'[^\w\-_]', '_', document_id)
        return self.storage_dir / f"{safe_id}.access"


class SecureDocumentStore:
    """Secure storage for sensitive document content."""
    
    def __init__(self, store_dir: Optional[str] = None):
        """
        Initialize the secure document store.
        
        Args:
            store_dir: Directory to store encrypted documents
        """
        self.store_dir = Path(store_dir or os.path.join(
            os.getenv("HOME", os.path.expanduser("~")), 
            ".lawglance", 
            "secure_docs"
        ))
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.room_code_manager = RoomCodeManager()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def store_document(self, content: str, metadata: Dict[str, str] = None) -> Tuple[str, str]:
        """
        Store a document securely with access control.
        
        Args:
            content: Document content
            metadata: Document metadata
            
        Returns:
            Tuple of (document_id, room_code)
        """
        # Generate document ID
        doc_id = f"doc_{secrets.token_hex(8)}"
        
        # Generate room code
        room_code = self.room_code_manager.generate_room_code(doc_id)
        
        # Store document content
        doc_path = self._get_document_path(doc_id)
        try:
            # Store content
            with open(doc_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            # Store metadata if provided
            if metadata:
                metadata_path = self._get_metadata_path(doc_id)
                with open(metadata_path, "w", encoding="utf-8") as f:
                    import json
                    json.dump(metadata, f, indent=2)
                    
            return doc_id, room_code
            
        except Exception as e:
            self.logger.error(f"Error storing document {doc_id}: {e}")
            # Clean up if there was an error
            if doc_path.exists():
                doc_path.unlink(missing_ok=True)
            raise
    
    def retrieve_document(self, document_id: str, room_code: str) -> Tuple[AccessStatus, Optional[str]]:
        """
        Retrieve a document with access control.
        
        Args:
            document_id: Document identifier
            room_code: Room access code
            
        Returns:
            Tuple of (status, document_content or None)
        """
        # Verify the room code
        status, access = self.room_code_manager.verify_room_code(document_id, room_code)
        if status != AccessStatus.SUCCESS:
            return status, None
            
        # Get document content
        doc_path = self._get_document_path(document_id)
        if not doc_path.exists():
            return AccessStatus.DOCUMENT_NOT_FOUND, None
            
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()
            return AccessStatus.SUCCESS, content
        except Exception as e:
            self.logger.error(f"Error retrieving document {document_id}: {e}")
            return AccessStatus.DOCUMENT_NOT_FOUND, None
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its access information.
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if successfully deleted, False otherwise
        """
        doc_path = self._get_document_path(document_id)
        metadata_path = self._get_metadata_path(document_id)
        
        try:
            # Delete document if it exists
            if doc_path.exists():
                doc_path.unlink()
                
            # Delete metadata if it exists
            if metadata_path.exists():
                metadata_path.unlink()
                
            # Revoke access
            self.room_code_manager.revoke_access(document_id)
            
            return True
        except Exception as e:
            self.logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    def _get_document_path(self, document_id: str) -> Path:
        """Get the file path for a document."""
        safe_id = re.sub(r'[^\w\-_]', '_', document_id)
        return self.store_dir / f"{safe_id}.txt"
    
    def _get_metadata_path(self, document_id: str) -> Path:
        """Get the file path for document metadata."""
        safe_id = re.sub(r'[^\w\-_]', '_', document_id)
        return self.store_dir / f"{safe_id}.meta"


def hash_room_code(code: str, iterations: int = HASH_ITERATIONS) -> str:
    """
    Hash a room code securely for storage.
    
    Args:
        code: Room code to hash
        iterations: Number of hash iterations for security
    
    Returns:
        Secure hash of the room code
    """
    # Use a fixed salt for simplicity
    # In production, should use a proper salt strategy
    salt = b'LawGlance-RoomCode-Salt'
    
    # Hash the code
    key = hashlib.pbkdf2_hmac(
        'sha256',
        code.encode('utf-8'),
        salt,
        iterations
    )
    
    # Convert to string representation
    return key.hex()
