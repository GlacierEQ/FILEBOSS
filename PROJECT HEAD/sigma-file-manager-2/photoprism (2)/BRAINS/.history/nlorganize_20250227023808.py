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
███████║╚██████╔╝██║  ██║   ██