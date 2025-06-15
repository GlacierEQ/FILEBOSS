#!/usr/bin/env python
"""
Natural Language File Organizer - Command Line Interface

A command-line tool that lets users organize files using plain English commands.
This is a user-friendly interface to the Natural Language Organizer system.
"""
import os
import sys
import json
import asyncio
import argparse
import platform
import shutil
from typing import Dict, Any, Optional, List

# Make sure we can import local modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the natural language organizer
try:
    from natural_language_organizer import NaturalLanguageOrganizer
except ImportError:
    print("Error: Natural language organizer module not found.")
    print("Make sure you're running this script from the correct directory.")
    sys.exit(1)

# ASCII Art banner
BANNER = """
███████╗ ██████╗ ██████╗ ████████╗██╗███╗   ██╗ ██████╗     ██╗  ██╗ █████╗ ████████╗
██╔════╝██╔═══██╗██╔══██╗╚══██╔══╝██║████╗  ██║██╔════╝     ██║  ██║██╔══██╗╚══██╔══╝
███████╗██║   ██║██████╔╝   ██║   ██║██╔██╗ ██║██║  ███╗    ███████║███████║   ██║   
╚════██║██║   ██║██╔══██╗   ██║   ██║██║╚██╗██║██║   ██║    ██╔══██║██╔══██║   ██║   
███████║╚██████╔╝██║  ██║   ██║   ██║██║╚██╗██║██║   ██║    ██║  ██║██║  ██║   ██║   
"""

# Example commands for inspiration
EXAMPLES = [
    "Move all PDFs to the Documents folder and name them by date",
    "Create folders for photos by year and month, then organize all images",
    "Organize code files by language into the Programming folder",
    "Move large video files older than 30 days to the Archive folder",
    "Find all downloads from last week and sort them by type",
    "Collect all text files and put them in a Text folder",
    "Sort all screenshots into a Screenshots folder and name them by date"
]

# Color terminal output if supported
if os.name == 'posix' or platform.system() == 'Windows' and sys.stdout.isatty():
    COLORS = {
        'reset': '\033[0m',
        'bold': '\033[1m',
        'blue': '\033[94m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'cyan': '\033[96m'
    }
else:
    COLORS = {k: '' for k in ['reset', 'bold', 'blue', 'green', 'yellow', 'red', 'cyan']}

def print_color(text, color='reset', bold=False):
    """Print colored text if terminal supports it"""
    prefix = COLORS['bold'] if bold else ''
    print(f"{prefix}{COLORS[color]}{text}{COLORS['reset']}")

def print_banner():
    """Print the application banner"""
    print(f"{COLORS['cyan']}{BANNER}{COLORS['reset']}")
    print(f"{COLORS['bold']}Natural Language File Organizer{COLORS['reset']}")
    print("Organize your files using plain English commands")
    print()

def print_examples():
    """Print example commands"""
    print(f"{COLORS['bold']}Example commands:{COLORS['reset']}")
    for i, example in enumerate(EXAMPLES, 1):
        print(f"{COLORS['cyan']}{i}.{COLORS['reset']} {example}")
    print()

def interactive_mode():
    """Run the organizer in interactive mode"""
    print_banner()
    print_examples()
    
    organizer = NaturalLanguageOrganizer()
    
    while True:
        print(f"\n{COLORS['bold']}Enter your organization instruction (or type 'exit' to quit):{COLORS['reset']}")
        instruction = input(f"{COLORS['green']}> {COLORS['reset']}")
        
        if instruction.lower() in ('exit', 'quit'):
            break
            
        if not instruction.strip():
            continue
            
        print(f"\n{COLORS['yellow']}Processing...{COLORS['reset']}")
        
        # Ask for a path (optional)
        print(f"{COLORS['bold']}Enter the path to organize (leave empty for default):{COLORS['reset']}")
        path = input(f"{COLORS['green']}> {COLORS['reset']}")
        path = path if path.strip() else None
        
        # Get confirmation
        print(f"\n{COLORS['bold']}Ready to organize:{COLORS['reset']}")
        print(f"  Instruction: {instruction}")
        print(f"  Path: {path if path else 'Default'}")
        confirm = input(f"\nProceed? [Y/n] {COLORS['green']}")
        
        if confirm.lower() in ('n', 'no'):
            continue
        
        # Process the instruction
        try:
            loop = asyncio.get_event_loop()
            result = loop.run_until_complete(organizer.organize(instruction, path))
            
            # Display results
            if result['success']:
                print(f"\n{COLORS['green']}✓ {result['message']}{COLORS['reset']}")
                if result['files_moved'] > 0:
                    print(f"\n{COLORS['bold']}Files organized:{COLORS['reset']}")
                    for i, action in enumerate(result['actions'][:10], 1):
                        src = os.path.basename(action['source'])
                        dst = os.path.basename(action['destination'])
                        print(f"  {i}. {src} → {dst}")
                    
                    if len(result['actions']) > 10:
                        print(f"  ... and {len(result['actions']) - 10} more")
            else:
                print(f"\n{COLORS['red']}✗ {result['message']}{COLORS['reset']}")
                
        except Exception as e:
            print(f"\n{COLORS['red']}Error: {e}{COLORS['reset']}")

def command_mode(args):
    """Run the organizer with command-line arguments"""
    organizer = NaturalLanguageOrganizer()
    
    try:
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(organizer.organize(args.instruction, args.path))
        
        # Display results based on output format
        if args.output == 'json':
            print(json.dumps(result, indent=2))
        else:
            # Display results in human-readable format
            if result['success']:
                print(f"✓ {result['message']}")
                print(f"Files moved: {result['files_moved']}")
                print(f"Time taken: {result['execution_time']:.2f}s")
                
                if args.verbose and result['files_moved'] > 0:
                    print("\nFiles organized:")
                    for i, action in enumerate(result['actions'], 1):
                        src = os.path.basename(action['source'])
                        dst = os.path.basename(action['destination'])
                        print(f"  {i}. {src} → {dst}")
            else:
                print(f"✗ {result['message']}")
                
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        # Check for groq (optional)
        try:
            import groq
            groq_available = True
        except ImportError:
            groq_available = False
            
        if not groq_available:
            print(f"{COLORS['yellow']}Warning: groq package not found. AI-based parsing will not be available.{COLORS['reset']}")
            print(f"{COLORS['yellow']}You can install it with: pip install groq{COLORS['reset']}")
            print()
            
        return True
    except ImportError as e:
        print(f"Error: Required dependency not found: {e}")
        return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Organize files using natural language commands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n" + "\n".join(f"  • {ex}" for ex in EXAMPLES[:3])
    )
    
    parser.add_argument("instruction", nargs="?", help="Natural language instruction for file organization")
    parser.add_argument("--path", "-p", help="Base path to start organization from")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    parser.add_argument("--output", "-o", choices=["text", "json"], default="text", help="Output format (text or JSON)")
    parser.add_argument("--examples", "-e", action="store_true", help="Show example commands and exit")
    
    args = parser.parse_args()
    
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)
        
    # Handle --examples flag
    if args.examples:
        print_banner()
        print_examples()
        sys.exit(0)
    
    # Run in interactive mode if specified or if no instruction provided
    if args.interactive or not args.instruction:
        interactive_mode()
    else:
        # Command mode
        command_mode(args)

if __name__ == "__main__":
    main()