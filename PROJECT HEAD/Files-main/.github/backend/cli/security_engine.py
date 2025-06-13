#!/usr/bin/env python3
"""
CodexFlō Security Engine
Handles security, access control, and compliance requirements
"""

import logging
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class SecurityComplianceEngine:
    """Handles security, access control, and compliance requirements"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.access_log = []
        self.ethical_walls = config.get("legal", {}).get("ethical_walls", {}).get("enabled", False)
        self.strict_mode = config.get("legal", {}).get("ethical_walls", {}).get("strict_mode", False)
        self.encryption_enabled = config.get("security", {}).get("encryption_enabled", False)
        self.privilege_detection = config.get("security", {}).get("privilege_detection", False)
        self.access_rules = {}
        
        # Initialize access rules
        self._init_access_rules()
        
    def _init_access_rules(self):
        """Initialize access control rules"""
        # In a real implementation, this would load rules from a database or config file
        self.access_rules = {
            "default": {
                "roles": {
                    "admin": {"level": 100, "can_access_all": True},
                    "attorney": {"level": 80, "privilege_access": True},
                    "paralegal": {"level": 60, "privilege_access": False},
                    "client": {"level": 40, "privilege_access": False},
                    "guest": {"level": 20, "privilege_access": False}
                },
                "privilege_levels": {
                    "public": 0,
                    "confidential": 40,
                    "restricted": 60,
                    "work_product": 80,
                    "attorney_client": 100
                }
            }
        }
        
    async def process_document(self, file_path: Path) -> Dict[str, Any]:
        """Process a document for security compliance"""
        result = {
            "file_path": str(file_path),
            "encryption_status": None,
            "privilege_detected": False,
            "privilege_level": "unknown",
            "access_control": {},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Check for encryption requirement
            if self.encryption_enabled:
                encryption_result = await self.encrypt_document(file_path)
                result["encryption_status"] = encryption_result
            
            # Check for privilege content if enabled
            if self.privilege_detection:
                privilege_result = await self._detect_privilege_content(file_path)
                result["privilege_detected"] = privilege_result["detected"]
                result["privilege_level"] = privilege_result["level"]
                result["privilege_confidence"] = privilege_result["confidence"]
            
            # Set access control metadata
            result["access_control"] = {
                "min_role_level": self._get_min_role_level(result["privilege_level"]),
                "ethical_wall_required": result["privilege_level"] in ["attorney_client", "work_product"]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing document security: {e}")
            result["error"] = str(e)
            return result
    
    async def check_access_permission(self, user_id: str, document_id: str) -> Dict[str, Any]:
        """Check if user has permission to access document"""
        result = {
            'allowed': False,
            'reason': '',
            'logged': False
        }
        
        # Get document metadata
        doc_metadata = await self._get_document_metadata(document_id)
        if not doc_metadata:
            result['reason'] = 'Document not found'
            return result
            
        # Check ethical walls
        if self.ethical_walls and doc_metadata.get('case_id'):
            wall_check = await self._check_ethical_wall(user_id, doc_metadata.get('case_id'))
            if not wall_check['allowed']:
                result['reason'] = wall_check['reason']
                await self._log_access_attempt(user_id, document_id, False, result['reason'])
                result['logged'] = True
                return result
                
        # Check privilege level
        privilege_check = await self._check_privilege_access(user_id, doc_metadata)
        if not privilege_check['allowed']:
            result['reason'] = privilege_check['reason']
            await self._log_access_attempt(user_id, document_id, False, result['reason'])
            result['logged'] = True
            return result
            
        # Access allowed
        result['allowed'] = True
        await self._log_access_attempt(user_id, document_id, True, 'Access granted')
        result['logged'] = True
        return result
        
    async def encrypt_document(self, file_path: Path) -> Dict[str, Any]:
        """Encrypt document for secure storage"""
        if not self.encryption_enabled:
            return {'encrypted': False, 'reason': 'Encryption disabled'}
            
        try:
            # Implementation would use appropriate encryption library
            encrypted_path = file_path.with_suffix(file_path.suffix + '.enc')
            # Placeholder for actual encryption
            return {
                'encrypted': True,
                'original_path': str(file_path),
                'encrypted_path': str(encrypted_path)
            }
        except Exception as e:
            return {'encrypted': False, 'reason': str(e)}
            
    async def generate_audit_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Generate compliance audit report"""
        report = {
            'period': f"{start_date} to {end_date}",
            'access_events': 0,
            'denied_access_events': 0,
            'privilege_warnings': 0,
            'ethical_wall_enforcements': 0,
            'details': []
        }
        
        # Filter logs by date range
        for log in self.access_log:
            log_date = log.get('timestamp', '').split('T')[0]
            if start_date <= log_date <= end_date:
                report['access_events'] += 1
                if not log.get('allowed', True):
                    report['denied_access_events'] += 1
                    if 'ethical wall' in log.get('reason', '').lower():
                        report['ethical_wall_enforcements'] += 1
                    if 'privilege' in log.get('reason', '').lower():
                        report['privilege_warnings'] += 1
                report['details'].append(log)
                
        return report
    
    async def _detect_privilege_content(self, file_path: Path) -> Dict[str, Any]:
        """Detect privileged content in document"""
        result = {
            "detected": False,
            "level": "public",
            "confidence": 0.0,
            "matches": []
        }
        
        try:
            # Only process text files
            if not self._is_text_file(file_path):
                return result
                
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(10000)  # First 10K chars
                
            # Simple pattern matching for privilege indicators
            privilege_patterns = {
                "attorney_client": [
                    "attorney-client privilege",
                    "privileged and confidential",
                    "attorney-client communication",
                    "legal advice"
                ],
                "work_product": [
                    "attorney work product",
                    "prepared in anticipation of litigation",
                    "work product doctrine"
                ],
                "restricted": [
                    "highly confidential",
                    "for attorneys' eyes only",
                    "do not distribute"
                ],
                "confidential": [
                    "confidential",
                    "not for distribution",
                    "internal use only"
                ]
            }
            
            # Check for matches
            content_lower = content.lower()
            for level, patterns in privilege_patterns.items():
                for pattern in patterns:
                    if pattern.lower() in content_lower:
                        result["matches"].append(pattern)
                        result["detected"] = True
                        # Set highest privilege level found
                        level_value = self.access_rules["default"]["privilege_levels"].get(level, 0)
                        current_level_value = self.access_rules["default"]["privilege_levels"].get(result["level"], 0)
                        if level_value > current_level_value:
                            result["level"] = level
                            result["confidence"] = 0.8  # Simple confidence score
            
            return result
            
        except Exception as e:
            logger.error(f"Error detecting privilege content: {e}")
            return result
    
    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is a text file"""
        text_extensions = ['.txt', '.md', '.csv', '.json', '.xml', '.html', '.htm', '.py', '.js', '.c', '.cpp', '.h', '.java']
        return file_path.suffix.lower() in text_extensions
    
    def _get_min_role_level(self, privilege_level: str) -> int:
        """Get minimum role level required for privilege level"""
        privilege_value = self.access_rules["default"]["privilege_levels"].get(privilege_level, 0)
        
        # Find minimum role that can access this privilege level
        min_role_level = 100  # Default to highest level
        for role, role_data in self.access_rules["default"]["roles"].items():
            if role_data.get("privilege_access", False) or role_data.get("level", 0) >= privilege_value:
                min_role_level = min(min_role_level, role_data.get("level", 100))
                
        return min_role_level
        
    async def _get_document_metadata(self, document_id: str) -> Dict[str, Any]:
        """Retrieve document metadata"""
        # Implementation would fetch from database
        # Placeholder implementation
        return {}
        
    async def _check_ethical_wall(self, user_id: str, case_id: str) -> Dict[str, bool]:
        """Check if ethical wall prevents access"""
        # Implementation would check against ethical wall rules
        # Placeholder implementation
        return {'allowed': True, 'reason': ''}
        
    async def _check_privilege_access(self, user_id: str, metadata: Dict[str, Any]) -> Dict[str, bool]:
        """Check if user has appropriate privilege level"""
        # Implementation would check user's role against document privilege
        # Placeholder implementation
        return {'allowed': True, 'reason': ''}
        
    async def _log_access_attempt(self, user_id: str, document_id: str, allowed: bool, reason: str) -> None:
        """Log access attempt for audit purposes"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'document_id': document_id,
            'allowed': allowed,
            'reason': reason
        }
        self.access_log.append(log_entry)