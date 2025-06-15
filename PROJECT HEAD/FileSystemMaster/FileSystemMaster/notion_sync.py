"""
Notion Integration and Sync Module
Connects with Notion databases for enhanced memory and workflow integration
"""

import os
import json
import logging
from typing import Dict, List, Optional
from notion_client import Client
from datetime import datetime
import time

logger = logging.getLogger(__name__)

class NotionIntegration:
    """Enhanced Notion integration for file automation and memory sync"""
    
    def __init__(self, token: str = None):
        self.token = token or os.getenv("NOTION_INTEGRATION_SECRET")
        if not self.token:
            raise ValueError("Notion token required. Please provide NOTION_INTEGRATION_SECRET.")
        
        self.client = Client(auth=self.token)
        
        # Database IDs - these will be configured based on your setup
        self.databases = {
            "personal_reflections": os.getenv("NOTION_DB_PERSONAL"),
            "psysoc_x": os.getenv("NOTION_DB_PSYSOC"),
            "master_dossier": os.getenv("NOTION_DB_MASTER"),
            "court_communications": os.getenv("NOTION_DB_COURT"),
            "strategy_hub": os.getenv("NOTION_DB_STRATEGY"),
            "file_automation": os.getenv("NOTION_DB_FILES")  # For our file processing logs
        }
        
    def setup_file_automation_database(self) -> str:
        """Create or configure the file automation database in Notion"""
        
        try:
            # Database properties for file automation tracking
            properties = {
                "File Name": {"title": {}},
                "Original Path": {"rich_text": {}},
                "New Path": {"rich_text": {}},
                "Category": {"select": {"options": [
                    {"name": "Legal Documents", "color": "red"},
                    {"name": "Business Documents", "color": "blue"},
                    {"name": "Financial Reports", "color": "green"},
                    {"name": "Compliance", "color": "yellow"},
                    {"name": "Contracts", "color": "purple"},
                    {"name": "General", "color": "gray"}
                ]}},
                "Confidence Score": {"number": {"format": "percent"}},
                "Processing Date": {"date": {}},
                "Legal Classification": {"select": {"options": [
                    {"name": "Contract", "color": "red"},
                    {"name": "Compliance", "color": "yellow"},
                    {"name": "Litigation", "color": "orange"},
                    {"name": "Corporate", "color": "blue"},
                    {"name": "Employment", "color": "green"},
                    {"name": "Financial", "color": "purple"},
                    {"name": "General", "color": "gray"}
                ]}},
                "Sensitivity Level": {"select": {"options": [
                    {"name": "Public", "color": "green"},
                    {"name": "Internal", "color": "blue"},
                    {"name": "Confidential", "color": "yellow"},
                    {"name": "Restricted", "color": "orange"},
                    {"name": "Classified", "color": "red"}
                ]}},
                "Business Priority": {"select": {"options": [
                    {"name": "Low", "color": "gray"},
                    {"name": "Normal", "color": "blue"},
                    {"name": "High", "color": "yellow"},
                    {"name": "Critical", "color": "red"}
                ]}},
                "Tags": {"multi_select": {"options": []}},
                "AI Analysis": {"rich_text": {}},
                "Retention Period": {"rich_text": {}},
                "Compliance Requirements": {"multi_select": {"options": [
                    {"name": "SOX", "color": "red"},
                    {"name": "GDPR", "color": "blue"},
                    {"name": "HIPAA", "color": "green"},
                    {"name": "PCI DSS", "color": "yellow"},
                    {"name": "ISO 27001", "color": "purple"}
                ]}},
                "Status": {"select": {"options": [
                    {"name": "Processed", "color": "green"},
                    {"name": "Review Required", "color": "yellow"},
                    {"name": "Error", "color": "red"},
                    {"name": "Manual Override", "color": "blue"}
                ]}}
            }
            
            logger.info("File automation database schema configured")
            return "Database schema ready for file automation tracking"
            
        except Exception as e:
            logger.error(f"Failed to setup database: {e}")
            return None
    
    def log_file_processing(self, file_info: Dict, analysis_result: Dict) -> bool:
        """Log file processing results to Notion"""
        
        if not self.databases.get("file_automation"):
            logger.warning("File automation database not configured")
            return False
        
        try:
            page_data = {
                "parent": {"database_id": self.databases["file_automation"]},
                "properties": {
                    "File Name": {
                        "title": [{"text": {"content": file_info.get("name", "Unknown")}}]
                    },
                    "Original Path": {
                        "rich_text": [{"text": {"content": file_info.get("original_path", "")}}]
                    },
                    "New Path": {
                        "rich_text": [{"text": {"content": file_info.get("new_path", "")}}]
                    },
                    "Category": {
                        "select": {"name": analysis_result.get("category", "General")}
                    },
                    "Confidence Score": {
                        "number": analysis_result.get("confidence", 0.0)
                    },
                    "Processing Date": {
                        "date": {"start": datetime.now().isoformat()}
                    },
                    "Legal Classification": {
                        "select": {"name": analysis_result.get("legal_classification", "General").title()}
                    },
                    "Sensitivity Level": {
                        "select": {"name": analysis_result.get("sensitivity_level", "Internal").title()}
                    },
                    "Business Priority": {
                        "select": {"name": analysis_result.get("business_priority", "Normal").title()}
                    },
                    "AI Analysis": {
                        "rich_text": [{"text": {"content": analysis_result.get("reasoning", "")}}]
                    },
                    "Retention Period": {
                        "rich_text": [{"text": {"content": f"{analysis_result.get('retention_period', '3')} years"}}]
                    },
                    "Status": {
                        "select": {"name": "Processed" if analysis_result.get("confidence", 0) > 0.7 else "Review Required"}
                    }
                }
            }
            
            # Add tags as multi-select
            if analysis_result.get("tags"):
                page_data["properties"]["Tags"] = {
                    "multi_select": [{"name": tag} for tag in analysis_result["tags"][:10]]
                }
            
            # Add compliance requirements
            if analysis_result.get("compliance_requirements"):
                page_data["properties"]["Compliance Requirements"] = {
                    "multi_select": [{"name": req.upper()} for req in analysis_result["compliance_requirements"]]
                }
            
            response = self.client.pages.create(**page_data)
            logger.info(f"Logged file processing to Notion: {response['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log to Notion: {e}")
            return False
    
    def fetch_all_pages(self, database_id: str) -> List[Dict]:
        """Fetch all pages from a Notion database"""
        
        if not database_id:
            return []
        
        results = []
        start_cursor = None
        
        try:
            while True:
                query_params = {"database_id": database_id}
                if start_cursor:
                    query_params["start_cursor"] = start_cursor
                
                response = self.client.databases.query(**query_params)
                results.extend(response["results"])
                
                if not response.get("has_more"):
                    break
                start_cursor = response["next_cursor"]
                
            return results
            
        except Exception as e:
            logger.error(f"Failed to fetch pages from {database_id}: {e}")
            return []
    
    def extract_learning_data(self, database_name: str) -> List[Dict]:
        """Extract learning data from specific Notion database"""
        
        database_id = self.databases.get(database_name)
        if not database_id:
            logger.warning(f"Database {database_name} not configured")
            return []
        
        pages = self.fetch_all_pages(database_id)
        learning_data = []
        
        for page in pages:
            try:
                # Extract text content from page properties
                properties = page.get("properties", {})
                content_parts = []
                
                for prop_name, prop_data in properties.items():
                    if prop_data.get("type") == "title" and prop_data.get("title"):
                        content_parts.append(f"Title: {prop_data['title'][0]['text']['content']}")
                    elif prop_data.get("type") == "rich_text" and prop_data.get("rich_text"):
                        content_parts.append(f"{prop_name}: {prop_data['rich_text'][0]['text']['content']}")
                
                if content_parts:
                    learning_data.append({
                        "source": database_name,
                        "page_id": page["id"],
                        "content": " | ".join(content_parts),
                        "created_time": page.get("created_time"),
                        "last_edited_time": page.get("last_edited_time")
                    })
                    
            except Exception as e:
                logger.warning(f"Failed to extract data from page {page.get('id', 'unknown')}: {e}")
        
        return learning_data
    
    def sync_with_memory(self, memory_instance) -> Dict:
        """Sync Notion data with Mem0 for enhanced learning"""
        
        sync_results = {
            "databases_synced": 0,
            "pages_processed": 0,
            "memories_created": 0,
            "errors": []
        }
        
        for db_name, db_id in self.databases.items():
            if not db_id or db_name == "file_automation":
                continue
                
            try:
                logger.info(f"Syncing database: {db_name}")
                learning_data = self.extract_learning_data(db_name)
                
                for data in learning_data:
                    try:
                        # Store in Mem0 with metadata
                        memory_text = f"Notion {db_name}: {data['content']}"
                        metadata = {
                            "source": "notion",
                            "database": db_name,
                            "page_id": data["page_id"],
                            "created_time": data["created_time"]
                        }
                        
                        memory_instance.add(memory_text, metadata=metadata)
                        sync_results["memories_created"] += 1
                        
                    except Exception as e:
                        sync_results["errors"].append(f"Memory creation failed for {data['page_id']}: {e}")
                
                sync_results["pages_processed"] += len(learning_data)
                sync_results["databases_synced"] += 1
                
            except Exception as e:
                sync_results["errors"].append(f"Database sync failed for {db_name}: {e}")
        
        return sync_results
    
    def create_processing_report(self, processing_summary: Dict) -> bool:
        """Create a processing report page in Notion"""
        
        if not self.databases.get("file_automation"):
            return False
        
        try:
            report_content = f"""
# File Processing Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Summary
- **Total Files Processed**: {processing_summary.get('total_files', 0)}
- **Successfully Organized**: {processing_summary.get('successful', 0)}
- **Errors**: {processing_summary.get('errors', 0)}
- **Average Confidence**: {processing_summary.get('avg_confidence', 0):.2f}

## Categories
{self._format_categories(processing_summary.get('categories', {}))}

## High Priority Items
{self._format_priority_items(processing_summary.get('high_priority', []))}

## Compliance Alerts
{self._format_compliance_alerts(processing_summary.get('compliance_alerts', []))}
"""
            
            page_data = {
                "parent": {"database_id": self.databases["file_automation"]},
                "properties": {
                    "File Name": {
                        "title": [{"text": {"content": f"Processing Report {datetime.now().strftime('%Y%m%d_%H%M')}"}}]
                    },
                    "Category": {"select": {"name": "General"}},
                    "Status": {"select": {"name": "Processed"}},
                    "Processing Date": {"date": {"start": datetime.now().isoformat()}},
                    "AI Analysis": {
                        "rich_text": [{"text": {"content": report_content[:2000]}}]  # Notion has character limits
                    }
                }
            }
            
            response = self.client.pages.create(**page_data)
            logger.info(f"Created processing report: {response['id']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create processing report: {e}")
            return False
    
    def _format_categories(self, categories: Dict) -> str:
        """Format category information for report"""
        if not categories:
            return "No categories processed"
        
        lines = []
        for category, count in categories.items():
            lines.append(f"- **{category}**: {count} files")
        return "\n".join(lines)
    
    def _format_priority_items(self, priority_items: List) -> str:
        """Format high priority items for report"""
        if not priority_items:
            return "No high priority items identified"
        
        lines = []
        for item in priority_items[:10]:  # Limit to top 10
            lines.append(f"- {item.get('name', 'Unknown')} - {item.get('reason', 'High priority')}")
        return "\n".join(lines)
    
    def _format_compliance_alerts(self, alerts: List) -> str:
        """Format compliance alerts for report"""
        if not alerts:
            return "No compliance alerts"
        
        lines = []
        for alert in alerts:
            lines.append(f"- **{alert.get('type', 'Alert')}**: {alert.get('message', 'Requires attention')}")
        return "\n".join(lines)

class NotionSyncScheduler:
    """Automated sync scheduler for Notion integration"""
    
    def __init__(self, notion_integration: NotionIntegration, memory_instance):
        self.notion = notion_integration
        self.memory = memory_instance
        self.sync_interval = 900  # 15 minutes
        
    def run_continuous_sync(self):
        """Run continuous sync every 15 minutes"""
        
        logger.info("Starting continuous Notion sync...")
        
        while True:
            try:
                logger.info("Executing 15-minute sync pipeline...")
                sync_results = self.notion.sync_with_memory(self.memory)
                
                logger.info(f"Sync complete: {sync_results['memories_created']} memories created")
                
                if sync_results['errors']:
                    logger.warning(f"Sync errors: {len(sync_results['errors'])}")
                    for error in sync_results['errors'][:5]:  # Log first 5 errors
                        logger.warning(f"Sync error: {error}")
                
                logger.info("Sync complete. Sleeping...")
                time.sleep(self.sync_interval)
                
            except KeyboardInterrupt:
                logger.info("Sync interrupted by user")
                break
            except Exception as e:
                logger.error(f"Sync pipeline error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def run_single_sync(self) -> Dict:
        """Run a single sync operation"""
        
        try:
            logger.info("Running single sync operation...")
            sync_results = self.notion.sync_with_memory(self.memory)
            logger.info(f"Single sync complete: {sync_results}")
            return sync_results
            
        except Exception as e:
            logger.error(f"Single sync failed: {e}")
            return {"error": str(e), "databases_synced": 0, "memories_created": 0}