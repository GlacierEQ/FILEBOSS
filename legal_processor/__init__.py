"""
Legal Document Processor for FILEBOSS

This module provides functionality for processing legal documents, including
detection, classification, and organization of legal files.
"""

from .legal_document_processor import (
    process_legal_document,
    extract_case_references,
    is_legal_document,
    LegalDocument
)

__all__ = [
    'process_legal_document',
    'extract_case_references',
    'is_legal_document',
    'LegalDocument'
]
