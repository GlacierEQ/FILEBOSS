#!/usr/bin/env python3
"""
AI-Powered File Automation Tool with Memory & Notion Integration
Smart sorting and renaming of PDFs, Word docs, audio, and video files with persistent learning
"""

import argparse
import sys
import os
from pathlib import Path
import logging
from datetime import datetime
from typing import Optional

from config import Config
from file_processor import FileProcessor
from file_organizer import FileOrganizer
from backup_manager import BackupManager
from logger import setup_logger, ProgressLogger

def main():
    parser = argparse.ArgumentParser(
        description="AI-Powered File Automation Tool with Memory & Notion Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py /path/to/files --output /organized/files
  python main.py /path/to/files --dry-run --verbose
  python main.py /path/to/files --pattern smart --backup --memory
  python main.py /path/to/files --notion-sync --memory
  python main.py --notion-continuous-sync
        """
    )
    
    parser.add_argument("input_directory", nargs='?',
                       help="Directory containing files to process")
    parser.add_argument("--output", "-o", 
                       help="Output directory for organized files")
    parser.add_argument("--pattern", "-p", 
                       choices=["smart", "content", "timestamp", "category"],
                       default="smart",
                       help="Naming pattern for files")
    parser.add_argument("--types", "-t", 
                       nargs="+",
                       default=["pdf", "doc", "text", "audio", "video"],
                       help="File types to process")
    parser.add_argument("--max-files", "-m", 
                       type=int, default=100,
                       help="Maximum number of files to process")
    parser.add_argument("--dry-run", "-d", 
                       action="store_true",
                       help="Show what would be done without making changes")
    parser.add_argument("--backup", "-b", 
                       action="store_true",
                       help="Create backup before processing")
    parser.add_argument("--copy", "-c", 
                       action="store_true",
                       help="Copy files instead of moving them")
    parser.add_argument("--verbose", "-v", 
                       action="store_true",
                       help="Enable verbose logging")
    parser.add_argument("--log-file", "-l", 
                       help="Log file path")
    
    # Enhanced features
    parser.add_argument("--memory", 
                       action="store_true",
                       help="Use memory-enhanced AI analysis with Mem0")
    parser.add_argument("--notion-sync", 
                       action="store_true",
                       help="Sync results with Notion databases")
    parser.add_argument("--notion-continuous-sync", 
                       action="store_true",
                       help="Run continuous Notion sync every 15 minutes")
    parser.add_argument("--legal-mode", 
                       action="store_true",
                       help="Enable enhanced legal document analysis")
    parser.add_argument("--business-mode", 
                       action="store_true",
                       help="Enable enhanced business intelligence analysis")
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = setup_logger(log_level, args.log_file)
    
    try:
        # Handle continuous Notion sync mode
        if args.notion_continuous_sync:
            return run_continuous_notion_sync(logger)
        
        # Validate input directory for file processing
        if not args.input_directory:
            logger.error("Input directory is required for file processing")
            parser.print_help()
            sys.exit(1)
            
        input_path = Path(args.input_directory)
        if not input_path.exists():
            logger.error(f"Input directory does not exist: {input_path}")
            sys.exit(1)
        
        if not input_path.is_dir():
            logger.error(f"Input path is not a directory: {input_path}")
            sys.exit(1)
        
        # Set output directory
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = input_path / "organized_files"
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Create configuration with enhanced features
        config = Config(
            file_types=args.types,
            max_files=args.max_files,
            naming_pattern=args.pattern,
            dry_run=args.dry_run,
            backup_enabled=args.backup,
            copy_files=args.copy
        )
        
        logger.info(f"Starting enhanced file automation with config: {config}")
        logger.info(f"Input: {input_path}")
        logger.info(f"Output: {output_path}")
        
        # Enhanced features status
        if args.memory:
            logger.info("Memory-enhanced AI analysis: ENABLED")
        if args.notion_sync:
            logger.info("Notion integration: ENABLED")
        if args.legal_mode:
            logger.info("Legal document analysis: ENHANCED")
        if args.business_mode:
            logger.info("Business intelligence: ENHANCED")
        
        # Initialize enhanced AI analyzer if requested
        ai_analyzer = None
        if args.memory:
            try:
                from memory_enhanced_analyzer import MemoryEnhancedAnalyzer
                ai_analyzer = MemoryEnhancedAnalyzer()
                logger.info("Memory-enhanced AI analyzer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize memory analyzer: {e}")
                logger.info("Falling back to standard AI analysis")
        
        # Initialize Notion integration if requested
        notion_integration = None
        if args.notion_sync:
            try:
                from notion_sync import NotionIntegration
                notion_token = os.getenv("NOTION_INTEGRATION_SECRET") or "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"
                notion_integration = NotionIntegration(notion_token)
                logger.info("Notion integration initialized")
                
                # Setup file automation database
                db_setup = notion_integration.setup_file_automation_database()
                if db_setup:
                    logger.info("Notion database configured for file automation")
                    
            except Exception as e:
                logger.warning(f"Failed to initialize Notion integration: {e}")
                logger.info("Continuing without Notion sync")
                notion_integration = None
        
        # Create backup if requested
        backup_id = None
        if config.backup_enabled and not config.dry_run:
            backup_manager = BackupManager()
            backup_id = backup_manager.create_backup(input_path)
            if backup_id:
                logger.info(f"Created backup: {backup_id}")
            else:
                logger.warning("Failed to create backup")
        
        # Process files with enhanced analyzer
        processor = FileProcessor(config)
        
        # Use the cost-effective multi-provider analyzer (already initialized in FileProcessor)
        
        logger.info("Scanning directory for files...")
        files = processor.scan_directory(input_path)
        if not files:
            logger.warning("No supported files found")
            return
        
        logger.info(f"Found {len(files)} supported files")
        
        # Initialize progress tracking
        progress = ProgressLogger(len(files), logger)
        
        logger.info("Processing files with enhanced AI analysis...")
        processed_files = processor.process_files(files)
        
        # Organize files
        organizer = FileOrganizer(config)
        logger.info("Organizing files with intelligent categorization...")
        
        results = organizer.organize_files(processed_files, output_path)
        
        # Enhanced results processing
        if notion_integration:
            logger.info("Syncing results with Notion...")
            sync_count = 0
            for file_result in results.get('processed_files', []):
                if notion_integration.log_file_processing(
                    file_result.get('file_info', {}), 
                    file_result.get('analysis', {})
                ):
                    sync_count += 1
            logger.info(f"Synced {sync_count} files to Notion")
            
            # Create processing report
            processing_summary = {
                'total_files': results['total_files'],
                'successful': results['successful'],
                'errors': results['errors'],
                'categories': results.get('categories', {}),
                'avg_confidence': calculate_average_confidence(processed_files),
                'high_priority': extract_high_priority_items(processed_files),
                'compliance_alerts': extract_compliance_alerts(processed_files)
            }
            
            if notion_integration.create_processing_report(processing_summary):
                logger.info("Created processing report in Notion")
        
        # Create enhanced report
        organizer.create_organization_report(results, output_path)
        
        # Enhanced summary with memory and legal insights
        logger.info("=" * 60)
        logger.info("ENHANCED AI PROCESSING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Files processed: {len(processed_files)}")
        logger.info(f"Successfully organized: {results.get('successful', 0)}")
        logger.info(f"Errors: {results.get('errors', 0)}")
        logger.info(f"Skipped: {results.get('skipped', 0)}")
        
        if results.get('categories'):
            logger.info("\nIntelligent Categories:")
            for category, count in results['categories'].items():
                logger.info(f"  {category}: {count} files")
        
        # Enhanced insights
        if ai_analyzer:
            avg_confidence = calculate_average_confidence(processed_files)
            logger.info(f"\nAI Analysis Confidence: {avg_confidence:.1%}")
            
            high_priority = extract_high_priority_items(processed_files)
            if high_priority:
                logger.info(f"High Priority Items: {len(high_priority)}")
            
            compliance_alerts = extract_compliance_alerts(processed_files)
            if compliance_alerts:
                logger.info(f"Compliance Alerts: {len(compliance_alerts)}")
        
        if backup_id:
            logger.info(f"\nBackup created: {backup_id}")
        
        if notion_integration:
            logger.info(f"Results synced to Notion databases")
        
        logger.info(f"\nResults saved to: {output_path}")
        logger.info("\nFile automation complete with enhanced AI intelligence!")
        
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

def run_continuous_notion_sync(logger: logging.Logger):
    """Run continuous Notion sync mode"""
    
    try:
        logger.info("Starting continuous Notion sync mode...")
        
        # Check for required secrets
        notion_token = os.getenv("NOTION_INTEGRATION_SECRET")
        if not notion_token:
            logger.error("NOTION_INTEGRATION_SECRET environment variable required for sync mode")
            logger.info("Please set your Notion integration token and try again")
            return
        
        # Initialize Notion integration and memory
        from notion_sync import NotionIntegration, NotionSyncScheduler
        notion_integration = NotionIntegration(notion_token)
        
        # Initialize Mem0 memory
        try:
            from mem0 import Memory
            memory = Memory()
            logger.info("Memory system initialized for continuous learning")
        except Exception as e:
            logger.error(f"Failed to initialize memory system: {e}")
            return
        
        # Create sync scheduler
        scheduler = NotionSyncScheduler(notion_integration, memory)
        
        # Run continuous sync
        logger.info("Starting 15-minute sync intervals...")
        logger.info("Press Ctrl+C to stop")
        scheduler.run_continuous_sync()
        
    except Exception as e:
        logger.error(f"Continuous sync failed: {e}")

def calculate_average_confidence(processed_files: list) -> float:
    """Calculate average confidence score from processed files"""
    
    if not processed_files:
        return 0.0
    
    total_confidence = 0.0
    count = 0
    
    for file_data in processed_files:
        analysis = file_data.get('analysis', {})
        if 'confidence' in analysis:
            total_confidence += analysis['confidence']
            count += 1
    
    return total_confidence / count if count > 0 else 0.0

def extract_high_priority_items(processed_files: list) -> list:
    """Extract high priority items from processed files"""
    
    high_priority = []
    
    for file_data in processed_files:
        analysis = file_data.get('analysis', {})
        if analysis.get('business_priority') == 'critical' or analysis.get('urgency_level') == 'high':
            high_priority.append({
                'name': file_data.get('file_info', {}).get('name', 'Unknown'),
                'reason': f"Priority: {analysis.get('business_priority', 'high')}"
            })
    
    return high_priority

def extract_compliance_alerts(processed_files: list) -> list:
    """Extract compliance alerts from processed files"""
    
    alerts = []
    
    for file_data in processed_files:
        analysis = file_data.get('analysis', {})
        compliance_reqs = analysis.get('compliance_requirements', [])
        
        if compliance_reqs:
            alerts.append({
                'type': 'Compliance Required',
                'message': f"File requires {', '.join(compliance_reqs)} compliance review"
            })
        
        if analysis.get('sensitivity_level') in ['restricted', 'classified']:
            alerts.append({
                'type': 'High Sensitivity',
                'message': f"File marked as {analysis.get('sensitivity_level')} - review access controls"
            })
    
    return alerts

if __name__ == "__main__":
    main()