"""
Example of using the LawGlance security module for room code protection.
This demonstrates secure document access control.
"""
import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.utils.security import (
    RoomCodeManager, 
    SecureDocumentStore, 
    AccessStatus
)

def main():
    """Run the security example."""
    print("LawGlance Security Example - Room Code Protection")
    print("=" * 50)
    
    # Initialize the secure document store
    doc_store = SecureDocumentStore()
    
    # Sample document content
    document_content = """
    CONFIDENTIAL LEGAL DOCUMENT
    
    This document contains sensitive legal information that should only be 
    accessed by authorized personnel with the correct room code.
    
    The content is protected by LawGlance's room code security system.
    """
    
    # Store the document and get a room code
    document_id, room_code = doc_store.store_document(
        document_content, 
        metadata={"title": "Confidential Document", "author": "LawGlance Security"}
    )
    
    print(f"\nDocument stored successfully!")
    print(f"Document ID: {document_id}")
    print(f"Room Code: {room_code}")
    
    # Demonstrate successful access
    print("\n--- Accessing document with correct room code ---")
    status, content = doc_store.retrieve_document(document_id, room_code)
    if status == AccessStatus.SUCCESS:
        print("Access granted! Document content:")
        print("-" * 30)
        print(content.strip())
        print("-" * 30)
    else:
        print(f"Access denied: {status}")
    
    # Demonstrate unsuccessful access
    print("\n--- Attempting access with incorrect room code ---")
    wrong_code = "000000"
    status, content = doc_store.retrieve_document(document_id, wrong_code)
    print(f"Access status: {status}")
    if status != AccessStatus.SUCCESS:
        print("Access correctly denied for wrong code.")
    
    # Clean up - delete the test document
    print("\n--- Cleaning up ---")
    deleted = doc_store.delete_document(document_id)
    print(f"Document deleted: {deleted}")
    
    print("\nExample completed successfully!")

if __name__ == "__main__":
    main()
