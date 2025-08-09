"""
Command Line Interface for FILEBOSS File Organizer

Provides a user-friendly CLI for the file organization and analysis tools.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any

from .file_organizer import FileOrganizer
from .file_analyzer import FileAnalyzer
from .file_utils import format_size

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_args(args: List[str] = None) -> argparse.Namespace:
    """Parse command line arguments.
    
    Args:
        args: List of command line arguments (default: sys.argv[1:])
        
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='FILEBOSS - Advanced File Organizer and Analyzer',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Global arguments
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
        '--include-hidden',
        action='store_true',
        help='Include hidden files and directories'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', required=True)
    
    # Organize command
    org_parser = subparsers.add_parser(
        'organize',
        help='Organize files into directories'
    )
    org_parser.add_argument(
        'source',
        type=Path,
        help='Source directory to organize'
    )
    org_parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help='Output directory (default: <source>/organized)'
    )
    org_parser.add_argument(
        '--by',
        choices=['type', 'date', 'extension'],
        default='type',
        help='Organization criteria'
    )
    org_parser.add_argument(
        '--date-format',
        default='%Y-%m-%d',
        help='Date format string (for --by=date)'
    )
    org_parser.add_argument(
        '--copy',
        action='store_true',
        help='Copy files instead of moving them'
    )
    org_parser.add_argument(
        '--pattern',
        default='*',
        help='File pattern to match (e.g., "*.jpg")'
    )
    org_parser.add_argument(
        '--no-recursive',
        action='store_false',
        dest='recursive',
        help='Do not process subdirectories recursively'
    )
    
    # Find duplicates command
    dup_parser = subparsers.add_parser(
        'find-duplicates',
        help='Find duplicate files'
    )
    dup_parser.add_argument(
        'directory',
        type=Path,
        help='Directory to search for duplicates'
    )
    dup_parser.add_argument(
        '--delete',
        action='store_true',
        help='Delete duplicate files (keeping one copy)'
    )
    dup_parser.add_argument(
        '--no-recursive',
        action='store_false',
        dest='recursive',
        help='Do not search subdirectories recursively'
    )
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        'analyze',
        help='Analyze directory contents'
    )
    analyze_parser.add_argument(
        'directory',
        type=Path,
        help='Directory to analyze'
    )
    analyze_parser.add_argument(
        '--no-recursive',
        action='store_false',
        dest='recursive',
        help='Do not analyze subdirectories recursively'
    )
    
    # Scan command
    scan_parser = subparsers.add_parser(
        'scan',
        help='Scan directory and list files'
    )
    scan_parser.add_argument(
        'directory',
        type=Path,
        help='Directory to scan'
    )
    scan_parser.add_argument(
        '--pattern',
        default='*',
        help='File pattern to match (e.g., "*.jpg")'
    )
    scan_parser.add_argument(
        '--no-recursive',
        action='store_false',
        dest='recursive',
        help='Do not scan subdirectories recursively'
    )
    
    return parser.parse_args(args)

def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=2, default=str))

def main(args: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI.
    
    Args:
        args: Command line arguments (default: sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse command line arguments
    try:
        args = parse_args(args)
    except Exception as e:
        logger.error(f"Error parsing arguments: {e}")
        return 1
    
    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.getLogger().setLevel(log_level)
    
    # Initialize the organizer
    organizer = FileOrganizer(
        dry_run=args.dry_run,
        overwrite=args.overwrite,
        include_hidden=args.include_hidden,
        log_level=log_level
    )
    
    try:
        if args.command == 'organize':
            return handle_organize(organizer, args)
        elif args.command == 'find-duplicates':
            return handle_find_duplicates(organizer, args)
        elif args.command == 'analyze':
            return handle_analyze(organizer, args)
        elif args.command == 'scan':
            return handle_scan(organizer, args)
        else:
            logger.error(f"Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130  # SIGINT exit code
    except Exception as e:
        logger.exception(f"Error: {e}")
        return 1
    finally:
        # Print statistics
        stats = organizer.get_stats()
        if args.json:
            print_json(stats)
        else:
            print("\n=== Statistics ===")
            print(f"Files processed: {stats['files_processed']}")
            if 'files_moved' in stats and stats['files_moved'] > 0:
                print(f"Files moved: {stats['files_moved']}")
            if 'files_copied' in stats and stats['files_copied'] > 0:
                print(f"Files copied: {stats['files_copied']}")
            if 'duplicates_found' in stats and stats['duplicates_found'] > 0:
                print(f"Duplicate files found: {stats['duplicates_found']}")
            if 'errors' in stats and stats['errors'] > 0:
                print(f"Errors: {stats['errors']}")
            if 'duration_seconds' in stats:
                print(f"Duration: {stats['duration_seconds']:.2f} seconds")
            if 'files_per_second' in stats:
                print(f"Speed: {stats['files_per_second']:.1f} files/second")
            if 'throughput_mb_per_second' in stats:
                print(f"Throughput: {stats['throughput_mb_per_second']:.1f} MB/s")

def handle_organize(organizer: FileOrganizer, args: argparse.Namespace) -> int:
    """Handle the organize command."""
    source_dir = args.source.resolve()
    output_dir = args.output_dir.resolve() if args.output_dir else source_dir / 'organized'
    
    if not source_dir.exists() or not source_dir.is_dir():
        logger.error(f"Source directory does not exist: {source_dir}")
        return 1
    
    if args.dry_run:
        logger.info("=== DRY RUN - No changes will be made ===")
    
    logger.info(f"Organizing files in: {source_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Organization method: by {args.by}")
    
    try:
        if args.by == 'type':
            results = organizer.organize_by_type(
                source_dir=source_dir,
                dest_dir=output_dir,
                copy=args.copy,
                pattern=args.pattern,
                recursive=args.recursive
            )
        elif args.by == 'date':
            results = organizer.organize_by_date(
                source_dir=source_dir,
                dest_dir=output_dir,
                date_format=args.date_format,
                copy=args.copy,
                pattern=args.pattern,
                recursive=args.recursive
            )
        else:
            logger.error(f"Unsupported organization method: {args.by}")
            return 1
        
        if args.json:
            print_json({
                'status': 'success',
                'source': str(source_dir),
                'destination': str(output_dir),
                'method': args.by,
                'results': results,
                'stats': organizer.get_stats()
            })
        
        return 0
        
    except Exception as e:
        logger.exception(f"Error organizing files: {e}")
        return 1

def handle_find_duplicates(organizer: FileOrganizer, args: argparse.Namespace) -> int:
    """Handle the find-duplicates command."""
    directory = args.directory.resolve()
    
    if not directory.exists() or not directory.is_dir():
        logger.error(f"Directory does not exist: {directory}")
        return 1
    
    logger.info(f"Searching for duplicate files in: {directory}")
    
    try:
        duplicates = organizer.find_duplicates(
            directory=directory,
            recursive=args.recursive
        )
        
        if args.json:
            print_json({
                'status': 'success',
                'directory': str(directory),
                'duplicates_found': len(duplicates),
                'duplicates': duplicates,
                'stats': organizer.get_stats()
            })
        
        return 0
        
    except Exception as e:
        logger.exception(f"Error finding duplicates: {e}")
        return 1

def handle_analyze(organizer: FileOrganizer, args: argparse.Namespace) -> int:
    """Handle the analyze command."""
    directory = args.directory.resolve()
    
    if not directory.exists() or not directory.is_dir():
        logger.error(f"Directory does not exist: {directory}")
        return 1
    
    try:
        results = organizer.analyze_directory(
            directory=directory,
            recursive=args.recursive
        )
        
        if args.json:
            print_json({
                'status': 'success',
                'analysis': results,
                'stats': organizer.get_stats()
            })
        
        return 0
        
    except Exception as e:
        logger.exception(f"Error analyzing directory: {e}")
        return 1

def handle_scan(organizer: FileOrganizer, args: argparse.Namespace) -> int:
    """Handle the scan command."""
    directory = args.directory.resolve()
    
    if not directory.exists() or not directory.is_dir():
        logger.error(f"Directory does not exist: {directory}")
        return 1
    
    try:
        files = organizer.scan_directory(
            directory=directory,
            recursive=args.recursive
        )
        
        if args.json:
            print_json({
                'status': 'success',
                'directory': str(directory),
                'files': files,
                'file_count': len(files),
                'stats': organizer.get_stats()
            })
        else:
            print(f"\nFound {len(files)} files in {directory}:")
            for file_info in files:
                print(f"- {file_info['path']} ({format_size(file_info.get('size', 0))})")
        
        return 0
        
    except Exception as e:
        logger.exception(f"Error scanning directory: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
