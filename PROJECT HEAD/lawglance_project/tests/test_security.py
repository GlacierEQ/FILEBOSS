"""Unit tests for the security module."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
import shutil

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.utils.security import (
    RoomCodeManager, 
    SecureDocumentStore,
    AccessStatus,
    hash_room_code
)

class TestRoomCodeManager(unittest.TestCase):
    """Test cases for the RoomCodeManager class."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = RoomCodeManager(storage_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary files after tests."""
        shutil.rmtree(self.temp_dir)
    
    def test_generate_room_code(self):
        """Test generation of room access codes."""
        document_id = "test_doc_1"
        code = self.manager.generate_room_code(document_id)
        
        # Code should be a string of digits with correct length
        self.assertIsInstance(code, str)
        self.assertEqual(len(code), 6)  # Default length
        
        # Document should be in access map
        self.assertIn(document_id, self.manager.access_map)
    
    def test_verify_room_code(self):
        """Test verification of room codes."""
        document_id = "test_doc_2"
        code = self.manager.generate_room_code(document_id)
        
        # Test valid code
        status, access = self.manager.verify_room_code(document_id, code)
        self.assertEqual(status, AccessStatus.SUCCESS)
        self.assertIsNotNone(access)
        
        # Test invalid code
        status, access = self.manager.verify_room_code(document_id, "000000")
        self.assertEqual(status, AccessStatus.INVALID_CODE)
        self.assertIsNone(access)
        
        # Test non-existent document
        status, access = self.manager.verify_room_code("non_existent", code)
        self.assertEqual(status, AccessStatus.DOCUMENT_NOT_FOUND)
        self.assertIsNone(access)
    
    def test_failed_attempts_limit(self):
        """Test max failed attempts functionality."""
        document_id = "test_doc_3"
        code = self.manager.generate_room_code(document_id)
        
        # Try incorrect code multiple times
        for _ in range(5):
            status, _ = self.manager.verify_room_code(document_id, "wrong")
            self.assertEqual(status, AccessStatus.INVALID_CODE)
        
        # Next attempt should be blocked
        status, _ = self.manager.verify_room_code(document_id, "wrong")
        self.assertEqual(status, AccessStatus.MAX_ATTEMPTS_EXCEEDED)
        
        # Even correct code should be blocked now
        status, _ = self.manager.verify_room_code(document_id, code)
        self.assertEqual(status, AccessStatus.MAX_ATTEMPTS_EXCEEDED)
    
    def test_extend_access(self):
        """Test extending access duration."""
        document_id = "test_doc_4"
        self.manager.generate_room_code(document_id)
        
        # Check extension
        result = self.manager.extend_access(document_id, hours=48)
        self.assertTrue(result)
        
        # Check extension for non-existent document
        result = self.manager.extend_access("non_existent", hours=48)
        self.assertFalse(result)
    
    def test_revoke_access(self):
        """Test revoking access to a document."""
        document_id = "test_doc_5"
        self.manager.generate_room_code(document_id)
        
        # Revoke access
        result = self.manager.revoke_access(document_id)
        self.assertTrue(result)
        self.assertNotIn(document_id, self.manager.access_map)
        
        # Check revocation for non-existent document
        result = self.manager.revoke_access("non_existent")
        self.assertFalse(result)


class TestSecureDocumentStore(unittest.TestCase):
    """Test cases for the SecureDocumentStore class."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.store = SecureDocumentStore(store_dir=self.temp_dir)
    
    def tearDown(self):
        """Clean up temporary files after tests."""
        shutil.rmtree(self.temp_dir)
    
    def test_store_and_retrieve_document(self):
        """Test storing and retrieving a document."""
        # Store a test document
        doc_content = "This is a test document with secure access."
        metadata = {"title": "Test Document", "author": "Test User"}
        
        doc_id, room_code = self.store.store_document(doc_content, metadata)
        self.assertIsNotNone(doc_id)
        self.assertIsNotNone(room_code)
        
        # Retrieve with correct code
        status, content = self.store.retrieve_document(doc_id, room_code)
        self.assertEqual(status, AccessStatus.SUCCESS)
        self.assertEqual(content, doc_content)
        
        # Retrieve with incorrect code
        status, content = self.store.retrieve_document(doc_id, "wrong")
        self.assertEqual(status, AccessStatus.INVALID_CODE)
        self.assertIsNone(content)
        
        # Retrieve non-existent document
        status, content = self.store.retrieve_document("non_existent", room_code)
        self.assertEqual(status, AccessStatus.DOCUMENT_NOT_FOUND)
        self.assertIsNone(content)
    
    def test_delete_document(self):
        """Test document deletion."""
        # Store a test document
        doc_content = "This document will be deleted."
        doc_id, room_code = self.store.store_document(doc_content)
        
        # Verify it exists
        status, _ = self.store.retrieve_document(doc_id, room_code)
        self.assertEqual(status, AccessStatus.SUCCESS)
        
        # Delete it
        result = self.store.delete_document(doc_id)
        self.assertTrue(result)
        
        # Verify it's gone
        doc_path = self.store._get_document_path(doc_id)
        self.assertFalse(doc_path.exists())
        
        # Attempt to retrieve it (should fail)
        status, _ = self.store.retrieve_document(doc_id, room_code)
        self.assertEqual(status, AccessStatus.DOCUMENT_NOT_FOUND)


class TestHashRoomCode(unittest.TestCase):
    """Test cases for the hash_room_code function."""
    
    def test_hash_consistency(self):
        """Test that hashing is consistent."""
        code = "123456"
        hash1 = hash_room_code(code)
        hash2 = hash_room_code(code)
        self.assertEqual(hash1, hash2)
    
    def test_different_codes_different_hashes(self):
        """Test that different codes produce different hashes."""
        hash1 = hash_room_code("123456")
        hash2 = hash_room_code("654321")
        self.assertNotEqual(hash1, hash2)


if __name__ == "__main__":
    unittest.main()
