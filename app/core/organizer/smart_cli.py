"""
Smart File Organizer - Command Line Interface

Provides a user-friendly CLI for the smart file organizer.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

from .smart_organizer import SmartFileOrganizer, NamingRules, CategoryRule

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args(args: List[str] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Smart File Organizer - Organize and rename files by category',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Global arguments
    parser.add_argument(
        'directory',
        type=Path,
        help='Base directory to organize',
        default='.',
        nargs='?'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate operations without making changes'
    )
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing files'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    
    # Naming rules
    naming_group = parser.add_argument_group('Naming Rules')
    naming_group.add_argument(
        '--case',
        choices=['lower', 'upper', 'title', 'sentence'],
        default='title',
        help='Case style for filenames'
    )
    naming_group.add_argument(
        '--separator',
        choices=['space', 'underscore', 'hyphen'],
        default='space',
        help='Word separator in filenames'
    )
    naming_group.add_argument(
        '--max-length',
        type=int,
        default=64,
        help='Maximum length of filenames'
    )
    naming_group.add_argument(
        '--preserve-extension',
        action='store_true',
        help='Preserve file extensions'
    )
    
    # Category rules
    parser.add_argument(
        '--category',
        action='append',
        nargs='+',
        metavar=('NAME', 'TARGET_DIR', 'PATTERN', '...'),
        help='Define a category with patterns (e.g., "Documents docs *.doc *.docx")'
    )
    
    # File patterns
    parser.add_argument(
        '--pattern',
        default='*',
        help='File pattern to match (e.g., "*.pdf" or "**/*.jpg" for recursive)'
    )
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Process files in subdirectories'
    )
    
    return parser.parse_args(args)

def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, default=str))

def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    try:
        args = parse_args(args)
    except Exception as e:
        logger.error(f"Error parsing arguments: {e}")
        return 1
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.getLogger().setLevel(log_level)
    
    # Initialize the organizer
    try:
        organizer = SmartFileOrganizer(
            base_dir=args.directory,
            dry_run=args.dry_run,
            overwrite=args.overwrite,
            log_level=log_level
        )
        
        # Set default naming rules
        organizer.default_naming = NamingRules(
            case_style=args.case,
            word_separator=args.separator,
            max_length=args.max_length,
            preserve_extension=args.preserve_extension
        )
        
        # Add categories if specified
        if args.category:
            for category_args in args.category:
                if len(category_args) < 3:
                    logger.error(f"Invalid category definition: {category_args}")
                    return 1
                
                name = category_args[0]
                target_dir = category_args[1]
                patterns = category_args[2:]
                
                organizer.add_category(
                    name=name,
                    target_dir=target_dir,
                    patterns=patterns,
                    naming_rules=NamingRules(
                        case_style=args.case,
                        word_separator=args.separator,
                        max_length=args.max_length,
                        preserve_extension=args.preserve_extension
                    )
                )
        
        # Organize files
        stats = organizer.organize_directory(
            recursive=args.recursive,
            pattern=args.pattern
        )
        
        # Output results
        if args.json:
            print_json({
                'status': 'success',
                'directory': str(args.directory),
                'stats': stats
            })
        else:
            print("\n=== Organization Complete ===")
            print(f"Directory: {args.directory}")
            print(f"Files processed: {stats['files_processed']}")
            if stats['files_moved'] > 0:
                print(f"Files moved: {stats['files_moved']}")
            if stats['files_renamed'] > 0:
                print(f"Files renamed: {stats['files_renamed']}")
            if stats['files_skipped'] > 0:
                print(f"Files skipped: {stats['files_skipped']}")
            if stats['errors'] > 0:
                print(f"Errors: {stats['errors']}")
            print(f"Duration: {stats.get('duration_seconds', 0):.1f} seconds")
            
            if 'files_per_second' in stats:
                print(f"Speed: {stats['files_per_second']:.1f} files/second")
            
            if 'throughput_mb_per_second' in stats:
                print(f"Throughput: {stats['throughput_mb_per_second']:.1f} MB/s")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130  # SIGINT exit code
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
