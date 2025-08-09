"""
Legal Document Processor

This module provides functionality for processing legal documents,
extracting case references, and handling legal document organization.
"""

import os
import re
import spacy
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set
from pathlib import Path
from datetime import datetime
import json

# Legal document extensions
LEGAL_DOC_EXTENSIONS = {
    '.motion', '.pleading', '.affidavit', '.declaration', 
    '.brief', '.memorandum', '.order', '.judgment', '.opinion'
}

# Common legal document patterns
CASE_CITATION_PATTERN = r'\b\d+\s+[A-Za-z\.]+\s+\d+\b'
COURT_NAME_PATTERNS = [
    r'\b(?:Supreme|Appellate|District|Circuit|Superior|County|Municipal|Federal)\s+Court\b',
    r'\bCourt\s+of\s+[A-Za-z\s]+\b'
]

@dataclass
class LegalDocument:
    """Represents a legal document with extracted metadata."""
    file_path: str
    doc_type: str
    case_references: List[Dict[str, str]]
    parties: Dict[str, List[str]]
    filing_date: Optional[str] = None
    court: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert the LegalDocument to a dictionary."""
        return {
            'file_path': self.file_path,
            'doc_type': self.doc_type,
            'case_references': self.case_references,
            'parties': self.parties,
            'filing_date': self.filing_date,
            'court': self.court,
            'title': self.title,
            'summary': self.summary
        }

class LegalDocumentProcessor:
    """Processes legal documents to extract metadata and organize them."""
    
    def __init__(self, nlp_model: str = 'en_core_web_sm'):
        """Initialize the legal document processor.
        
        Args:
            nlp_model: The spaCy model to use for NLP processing
        """
        try:
            self.nlp = spacy.load(nlp_model)
        except OSError:
            print(f"Downloading spaCy model: {nlp_model}")
            import spacy.cli
            spacy.cli.download(nlp_model)
            self.nlp = spacy.load(nlp_model)
    
    def is_legal_document(self, file_path: str, content: Optional[str] = None) -> bool:
        """Determine if a file is a legal document.
        
        Args:
            file_path: Path to the file
            content: Optional content of the file (if already read)
            
        Returns:
            bool: True if the file appears to be a legal document
        """
        # Check file extension
        ext = os.path.splitext(file_path)[1].lower()
        if ext in LEGAL_DOC_EXTENSIONS:
            return True
            
        # Check content if provided
        if content:
            # Simple heuristic: look for common legal document patterns
            if any(re.search(pattern, content, re.IGNORECASE) for pattern in [
                'in the (?:\w+ )*court',
                'case no\.?\s*[:\[].*\d',
                'plaintiff.*v\.?\s*defendant',
                'complainant.*v\.?\s*respondent',
                'in re:',
                'motion to',
                'memorandum of (law|points and authorities)'
            ]):
                return True
                
        return False
    
    def extract_case_references(self, text: str) -> List[Dict[str, str]]:
        """Extract case references from text.
        
        Args:
            text: The text to analyze
            
        Returns:
            List of dictionaries containing case reference information
        """
        doc = self.nlp(text)
        case_refs = []
        
        # Look for case citations
        for match in re.finditer(CASE_CITATION_PATTERN, text):
            case_refs.append({
                'type': 'citation',
                'text': match.group(0),
                'start': match.start(),
                'end': match.end()
            })
            
        # Look for court names
        for pattern in COURT_NAME_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                case_refs.append({
                    'type': 'court',
                    'text': match.group(0),
                    'start': match.start(),
                    'end': match.end()
                })
                
        return case_refs
    
    def extract_parties(self, text: str) -> Dict[str, List[str]]:
        """Extract parties from legal document text.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary of party types to lists of party names
        """
        doc = self.nlp(text[:5000])  # Only analyze first 5000 chars for parties
        parties = {
            'plaintiffs': [],
            'defendants': [],
            'petitioners': [],
            'respondents': []
        }
        
        # Simple pattern matching for party identification
        for ent in doc.ents:
            if ent.label_ == 'PERSON' or ent.label_ == 'ORG':
                if 'plaintiff' in text.lower()[:ent.start_char]:
                    parties['plaintiffs'].append(ent.text)
                elif 'defendant' in text.lower()[:ent.start_char]:
                    parties['defendants'].append(ent.text)
                elif 'petitioner' in text.lower()[:ent.start_char]:
                    parties['petitioners'].append(ent.text)
                elif 'respondent' in text.lower()[:ent.start_char]:
                    parties['respondents'].append(ent.text)
                    
        return parties
    
    def determine_document_type(self, text: str) -> str:
        """Determine the type of legal document.
        
        Args:
            text: The text to analyze
            
        Returns:
            str: The determined document type
        """
        text_lower = text.lower()
        
        if any(term in text_lower for term in ['motion to', 'motion for']):
            return 'motion'
        elif any(term in text_lower for term in ['complaint', 'petition']):
            return 'pleading'
        elif any(term in text_lower for term in ['affidavit', 'declaration']):
            return 'affidavit'
        elif any(term in text_lower for term in ['order of the court', 'it is ordered']):
            return 'order'
        elif any(term in text_lower for term in ['memorandum opinion', 'opinion of the court']):
            return 'opinion'
        elif any(term in text_lower for term in ['brief', 'memorandum of law']):
            return 'brief'
            
        return 'legal_document'
    
    def process_legal_document(self, file_path: str, content: Optional[str] = None) -> LegalDocument:
        """Process a legal document and extract metadata.
        
        Args:
            file_path: Path to the legal document
            content: Optional content of the file (if already read)
            
        Returns:
            LegalDocument: Processed document with extracted metadata
        """
        if content is None:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        
        # Extract document metadata
        doc_type = self.determine_document_type(content)
        case_refs = self.extract_case_references(content)
        parties = self.extract_parties(content)
        
        # Create LegalDocument instance
        legal_doc = LegalDocument(
            file_path=file_path,
            doc_type=doc_type,
            case_references=case_refs,
            parties=parties
        )
        
        return legal_doc

def process_legal_document(file_path: str, content: Optional[str] = None) -> LegalDocument:
    """Convenience function to process a legal document.
    
    Args:
        file_path: Path to the legal document
        content: Optional content of the file (if already read)
        
    Returns:
        LegalDocument: Processed document with extracted metadata
    """
    processor = LegalDocumentProcessor()
    return processor.process_legal_document(file_path, content)

def is_legal_document(file_path: str, content: Optional[str] = None) -> bool:
    """Convenience function to check if a file is a legal document.
    
    Args:
        file_path: Path to the file
        content: Optional content of the file (if already read)
        
    Returns:
        bool: True if the file appears to be a legal document
    """
    processor = LegalDocumentProcessor()
    return processor.is_legal_document(file_path, content)

def extract_case_references(text: str) -> List[Dict[str, str]]:
    """Convenience function to extract case references from text.
    
    Args:
        text: The text to analyze
        
    Returns:
        List of dictionaries containing case reference information
    """
    processor = LegalDocumentProcessor()
    return processor.extract_case_references(text)
