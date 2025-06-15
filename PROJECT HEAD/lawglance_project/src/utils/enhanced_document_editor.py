"""
Enhanced document editor with repair functionality and better error handling.
This module extends the base document editor with scanning and repair features.
"""
import os
import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from docx import Document

from src.utils.document_editor import DocumentEditor
from src.utils.document_repair import DocumentRepair, RepairReport

# Constants
LOGGER_NAME = "lawglance.enhanced_editor"


class EnhancedDocumentEditor(DocumentEditor):
    """
    Enhanced document editor with repair capabilities.
    Extends the base DocumentEditor with scanning and repair functionality.
    """
    
    def __init__(self):
        """Initialize the enhanced document editor."""
        super().__init__()
        self.logger = logging.getLogger(LOGGER_NAME)
        self.repair_tool = DocumentRepair()
        
        # Add the scan_for_repairs operation to edit_operations
        self.edit_operations["scan_for_repairs"] = self._scan_for_repairs
        self.edit_operations["repair"] = self._repair_document
    
    def _parse_instructions(self, instructions):
        """
        Parse natural language instructions into operation and parameters.
        Extends the base method with repair operation patterns.
        """
        operation, params = super()._parse_instructions(instructions)
        
        # If we didn't find an operation, check for repair patterns
        if operation == "replace" and not params.get("old_text"):
            instructions = instructions.lower()
            
            # Check for scan/repair operations
            repair_patterns = [
                r"(?:scan\s+for\s+repairs|find\s+and\s+fix\s+errors|repair\s+document)",
                r"(?:check\s+for\s+errors|validate\s+document|fix\s+issues)",
                r"(?:format\s+check|structure\s+check|check\s+consistency)"
            ]
            
            for pattern in repair_patterns:
                match = re.search(pattern, instructions)
                if match:
                    # Check if this is an automatic repair request
                    if "fix" in instructions or "repair" in instructions:
                        return "repair", {"auto_fix": True}
                    else:
                        return "scan_for_repairs", {}
        
        return operation, params
    
    def _scan_for_repairs(self, doc, **kwargs):
        """
        Scan document for issues that need repair.
        
        Args:
            doc: Document to scan
            **kwargs: Additional parameters
            
        Returns:
            Status message with scan results
        """
        self.logger.info("Scanning document for potential issues")
        
        try:
            # Use the repair tool to scan the document
            report = self.repair_tool.scan_document(doc)
            
            if report.total_issues == 0:
                return "No issues found in the document."
            
            # Create a report message
            message = f"Found {report.total_issues} potential issues:\n\n"
            
            # Group issues by type
            issues_by_type = {}
            for issue in report.issues_found:
                issue_type = issue.issue_type.value
                if issue_type not in issues_by_type:
                    issues_by_type[issue_type] = []
                issues_by_type[issue_type].append(issue)
            
            # Add each type of issue to the message
            for issue_type, issues in issues_by_type.items():
                message += f"- {issue_type}: {len(issues)} issues\n"
                # Add up to 3 examples
                for i, issue in enumerate(issues[:3]):
                    message += f"  {i+1}. {issue.description} at {issue.location}\n"
                if len(issues) > 3:
                    message += f"  ... and {len(issues) - 3} more\n"
                message += "\n"
            
            # Add guidance
            message += "Use 'repair document' to attempt automatic fixes."
            return message
            
        except Exception as e:
            self.logger.error(f"Error during document scan: {e}")
            return f"Error during document scan: {str(e)}"
    
    def _repair_document(self, doc, **kwargs):
        """
        Repair issues in the document.
        
        Args:
            doc: Document to repair
            **kwargs: Additional parameters
            
        Returns:
            Status message with repair results
        """
        auto_fix = kwargs.get("auto_fix", False)
        self.logger.info(f"Attempting to repair document (auto_fix={auto_fix})")
        
        try:
            # Set auto_fix mode on the repair tool
            self.repair_tool.auto_fix = auto_fix
            
            # Scan and repair
            report = self.repair_tool.repair_document(doc)
            
            if report.total_issues == 0:
                return "No issues found in the document."
            
            # Create a report message
            message = f"Repaired {report.total_issues} issues:\n\n"
            
            # Group issues by type
            issues_by_type = {}
            for issue in report.issues_fixed:
                issue_type = issue.issue_type.value
                if issue_type not in issues_by_type:
                    issues_by_type[issue_type] = []
                issues_by_type[issue_type].append(issue)
            
            # Add each type of issue to the message
            for issue_type, issues in issues_by_type.items():
                message += f"- {issue_type}: {len(issues)} issues\n"
                # Add up to 3 examples
                for i, issue in enumerate(issues[:3]):
                    message += f"  {i+1}. {issue.description} at {issue.location}\n"
                if len(issues) > 3:
                    message += f"  ... and {len(issues) - 3} more\n"
                message += "\n"
            
            return message
            
        except Exception as e:
            self.logger.error(f"Error during document repair: {e}")
            return f"Error during document repair: {str(e)}"
