#!/usr/bin/env python3
"""
CodexFlō Legal Intelligence Pipeline
Provides comprehensive legal document processing, analysis, and case building
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import hashlib
from enum import Enum
import re

# Setup logging
logger = logging.getLogger(__name__)

class PrivilegeLevel(str, Enum):
    """Document privilege classification"""
    ATTORNEY_CLIENT = "attorney_client"
    WORK_PRODUCT = "work_product"
    CONFIDENTIAL = "confidential"
    SENSITIVE = "sensitive"
    PUBLIC = "public"
    UNKNOWN = "unknown"

class LegalClaim:
    """Represents a legal claim with elements and evidence"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.elements = []
        self.evidence = {}
        self.contradictions = []

class LegalPipeline:
    """Main legal intelligence pipeline for document processing"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the legal pipeline with configuration"""
        self.config = config
        self.legal_config = config.get("legal", {})
        self.enabled = self.legal_config.get("enabled", False)
        self.jurisdiction = self.legal_config.get("jurisdiction", "US")
        self.case_data = {}
        self.document_index = {}
        self.timeline_events = []
        
    async def process_document(self, doc_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Process a legal document through the pipeline"""
        if not self.enabled:
            return metadata
        
        try:
            # 1. Privilege detection
            if self.legal_config.get("privilege_detection", False):
                privilege_info = await self.detect_privilege(doc_path, metadata)
                metadata["legal_metadata"]["privilege"] = privilege_info
            
            # 2. Extract citations
            if self.legal_config.get("citation_extraction", False):
                citations = await self.extract_citations(doc_path, metadata)
                metadata["legal_metadata"]["citations"] = citations
            
            # 3. Extract deadlines
            if self.legal_config.get("deadline_tracking", False):
                deadlines = await self.extract_deadlines(doc_path, metadata)
                metadata["legal_metadata"]["deadlines"] = deadlines
            
            # 4. Update document index
            doc_id = metadata.get("signature", "")
            if doc_id:
                self.document_index[doc_id] = {
                    "path": str(doc_path),
                    "type": metadata.get("type", "unknown"),
                    "metadata": metadata
                }
            
            # 5. Update timeline if applicable
            await self.update_timeline(metadata)
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error in legal pipeline processing: {e}")
            return metadata
    
    async def detect_privilege(self, doc_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Detect privilege and confidentiality in document"""
        # Simple pattern-based detection for demonstration
        privilege_level = PrivilegeLevel.UNKNOWN
        confidence = 0.0
        reasons = []
        
        try:
            # Only process text files for now
            if metadata.get("metadata", {}).get("binary", True):
                return {
                    "level": privilege_level.value,
                    "confidence": confidence,
                    "reasons": ["Binary file - cannot analyze for privilege"]
                }
            
            # Read file content
            with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(10000)  # First 10K chars
            
            # Simple pattern matching
            patterns = {
                PrivilegeLevel.ATTORNEY_CLIENT: [
                    r"attorney.client\s+privilege",
                    r"privileged\s+and\s+confidential",
                    r"legal\s+advice",
                    r"attorney.client\s+communication"
                ],
                PrivilegeLevel.WORK_PRODUCT: [
                    r"attorney\s+work\s+product",
                    r"prepared\s+in\s+anticipation\s+of\s+litigation",
                    r"work\s+product\s+doctrine"
                ],
                PrivilegeLevel.CONFIDENTIAL: [
                    r"confidential",
                    r"not\s+for\s+distribution",
                    r"do\s+not\s+forward",
                    r"internal\s+use\s+only"
                ]
            }
            
            # Check patterns
            for level, level_patterns in patterns.items():
                for pattern in level_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        reasons.append(f"Found '{matches[0]}' indicating {level.value}")
                        if confidence < 0.7:  # Only upgrade if more confident
                            privilege_level = level
                            confidence = 0.7
            
            return {
                "level": privilege_level.value,
                "confidence": confidence,
                "reasons": reasons
            }
            
        except Exception as e:
            logger.error(f"Error in privilege detection: {e}")
            return {
                "level": PrivilegeLevel.UNKNOWN.value,
                "confidence": 0.0,
                "reasons": [f"Error: {str(e)}"]
            }
    
    async def extract_citations(self, doc_path: Path, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract legal citations from document"""
        citations = []
        
        try:
            # Only process text files
            if metadata.get("metadata", {}).get("binary", True):
                return citations
            
            # Read file content
            with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(10000)
            
            # US Case citation pattern (simplified)
            case_pattern = r'(\d+)\s+([A-Za-z\.]+)\s+(\d+)'
            statute_pattern = r'(\d+)\s+U\.?S\.?C\.?\s+[§s]\s*(\d+)'
            
            # Extract case citations
            case_matches = re.finditer(case_pattern, content)
            for match in case_matches:
                citations.append({
                    "type": "case",
                    "citation": match.group(0),
                    "volume": match.group(1),
                    "reporter": match.group(2),
                    "page": match.group(3)
                })
            
            # Extract statute citations
            statute_matches = re.finditer(statute_pattern, content)
            for match in statute_matches:
                citations.append({
                    "type": "statute",
                    "citation": match.group(0),
                    "title": match.group(1),
                    "section": match.group(2)
                })
            
            return citations
            
        except Exception as e:
            logger.error(f"Error extracting citations: {e}")
            return citations
    
    async def extract_deadlines(self, doc_path: Path, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract legal deadlines from document"""
        deadlines = []
        
        try:
            # Only process text files
            if metadata.get("metadata", {}).get("binary", True):
                return deadlines
            
            # Read file content
            with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(10000)
            
            # Simple deadline patterns
            deadline_patterns = [
                r'due\s+(?:on|by)?\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                r'deadline\s+(?:of|on|is)?\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                r'(?:not\s+later\s+than|before)\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
                r'(\d{1,2}/\d{1,2}/\d{2,4})\s+deadline'
            ]
            
            for pattern in deadline_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    date_str = match.group(1)
                    context = content[max(0, match.start() - 50):min(len(content), match.end() + 50)]
                    
                    deadlines.append({
                        "date_text": date_str,
                        "context": context.strip(),
                        "source_document": str(doc_path.name)
                    })
            
            return deadlines
            
        except Exception as e:
            logger.error(f"Error extracting deadlines: {e}")
            return deadlines
    
    async def update_timeline(self, metadata: Dict[str, Any]) -> None:
        """Update case timeline with document information"""
        try:
            # Extract dates from metadata
            dates = metadata.get("legal_metadata", {}).get("dates", [])
            
            # Add document creation date
            created_date = metadata.get("metadata", {}).get("created")
            if created_date:
                event = {
                    "date": created_date,
                    "event_type": "document_created",
                    "description": f"Document created: {metadata['metadata']['filename']}",
                    "document_id": metadata.get("signature", ""),
                    "document_type": metadata.get("type", "unknown")
                }
                self.timeline_events.append(event)
            
            # Add extracted dates as events
            for date_str in dates:
                try:
                    event = {
                        "date": date_str,
                        "event_type": "mentioned_date",
                        "description": f"Date mentioned in {metadata['metadata']['filename']}",
                        "document_id": metadata.get("signature", ""),
                        "document_type": metadata.get("type", "unknown")
                    }
                    self.timeline_events.append(event)
                except:
                    pass
                    
            # Sort timeline by date
            self.timeline_events.sort(key=lambda x: x.get("date", ""))
            
        except Exception as e:
            logger.error(f"Error updating timeline: {e}")
    
    async def ai_rename_and_sort(self, file_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        AI-driven renaming and sorting of files based on legal significance and pipeline prompt.
        Applies rules from AI_PIPELINE_PROMPT for standardized naming and categorization.
        """
        try:
            prompt_text = self.config.get('ai_pipeline_prompt', '')  # Assume prompt is in config or global
            if not prompt_text:
                prompt_text = "Fallback prompt structure"  # Use or load AI_PIPELINE_PROMPT if defined elsewhere
            
            # Extract renaming convention (e.g., date-type-ID)
            new_name = f"{datetime.now().strftime('%Y%m%d')}-{metadata.get('doc_type', 'unknown')}_{file_path.stem}_v1.{file_path.suffix}"
            sorted_path = file_path.parent / new_name
            file_path.rename(sorted_path)
            
            # Update metadata with new path and sort into categories
            metadata['organized_path'] = str(sorted_path)
            await self.advanced_organization(metadata)  # Assume or add call to existing method
            return metadata
        except Exception as e:
            logger.error(f"Error in ai_rename_and_sort: {e}")
            return {"error": str(e)}

    async def build_case(self, case_id: str) -> Dict[str, Any]:
        """Build case analysis from processed documents"""
        if not self.enabled or not self.legal_config.get("case_building", {}).get("enabled", False):
            return {"error": "Case building not enabled"}
        
        try:
            # Collect all documents for this case
            case_docs = [doc for doc in self.document_index.values() 
                        if doc.get("metadata", {}).get("legal_metadata", {}).get("case_numbers", []) 
                        and case_id in doc.get("metadata", {}).get("legal_metadata", {}).get("case_numbers", [])]
            
            if not case_docs:
                return {"error": f"No documents found for case {case_id}"}
            
            # Build case structure
            case = {
                "case_id": case_id,
                "documents": len(case_docs),
                "timeline": self.get_case_timeline(case_id),
                "entities": self.extract_case_entities(case_docs),
                "evidence_map": self.build_evidence_map(case_docs),
                "contradictions": self.find_contradictions(case_docs),
                "deadlines": self.collect_case_deadlines(case_docs)
            }
            
            return case
            
        except Exception as e:
            logger.error(f"Error building case {case_id}: {e}")
            return {"error": f"Error building case: {str(e)}"}
    
    def get_case_timeline(self, case_id: str) -> List[Dict[str, Any]]:
        """Get timeline events for a specific case"""
        # Filter timeline events for this case
        case_events = [event for event in self.timeline_events 
                      if event.get("document_id") in self.document_index
                      and case_id in self.document_index[event.get("document_id", "")].get("metadata", {})
                                .get("legal_metadata", {}).get("case_numbers", [])]
        
        # Sort by date
        case_events.sort(key=lambda x: x.get("date", ""))
        return case_events
    
    def extract_case_entities(self, case_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract and categorize entities from case documents"""
        entities = {
            "people": set(),
            "organizations": set(),
            "locations": set()
        }
        
        for doc in case_docs:
            doc_entities = doc.get("metadata", {}).get("legal_metadata", {}).get("entities", [])
            for entity in doc_entities:
                # Simple categorization - in real implementation would use NER
                if entity.lower().startswith("v.") or entity.lower().startswith("vs."):
                    continue
                elif any(word in entity.lower() for word in ["inc", "corp", "llc", "ltd", "company"]):
                    entities["organizations"].add(entity)
                elif any(word in entity.lower() for word in ["street", "avenue", "road", "county", "district"]):
                    entities["locations"].add(entity)
                else:
                    entities["people"].add(entity)
        
        # Convert sets to lists for JSON serialization
        return {k: list(v) for k, v in entities.items()}
    
    def build_evidence_map(self, case_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build evidence map from case documents"""
        evidence_map = {}
        
        # Group documents by type
        for doc in case_docs:
            doc_type = doc.get("type", "unknown")
            if doc_type not in evidence_map:
                evidence_map[doc_type] = []
            
            evidence_map[doc_type].append({
                "id": doc.get("metadata", {}).get("signature", ""),
                "filename": doc.get("metadata", {}).get("metadata", {}).get("filename", ""),
                "path": doc.get("path", ""),
                "entities": doc.get("metadata", {}).get("legal_metadata", {}).get("entities", []),
                "dates": doc.get("metadata", {}).get("legal_metadata", {}).get("dates", [])
            })
        
        return evidence_map
    
    def find_contradictions(self, case_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find potential contradictions between documents"""
        # This is a placeholder - real implementation would use NLP
        contradictions = []
        
        # In a real implementation, we would:
        # 1. Extract factual statements from documents
        # 2. Compare statements for logical contradictions
        # 3. Return pairs of contradicting statements with context
        
        return contradictions
    
    def collect_case_deadlines(self, case_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Collect all deadlines from case documents"""
        all_deadlines = []
        
        for doc in case_docs:
            deadlines = doc.get("metadata", {}).get("legal_metadata", {}).get("deadlines", [])
            for deadline in deadlines:
                deadline["source_document"] = doc.get("metadata", {}).get("metadata", {}).get("filename", "")
                all_deadlines.append(deadline)
        
        # Sort by date
        try:
            from dateutil import parser
            all_deadlines.sort(key=lambda x: parser.parse(x.get("date_text", "")))
        except:
            pass
            
        return all_deadlines

# Export the main class
__all__ = ['LegalPipeline']