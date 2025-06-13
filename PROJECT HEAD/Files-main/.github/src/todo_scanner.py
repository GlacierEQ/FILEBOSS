#!/usr/bin/env python3
"""
CodexFlō CLI - Command Line Interface for AI-Driven Strategic File Nexus
Enhanced with robust error handling, resource management, and validation
"""

import typer
import asyncio
import signal
import atexit
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.tree import Tree
from rich.prompt import Prompt, Confirm
import yaml
import json
from typing import Optional, List, Dict, Any
import subprocess
import sys
import os


import time
import requests
import psutil
from datetime import datetime

from contextlib import asynccontextmanager
import logging
from dataclasses import dataclass


from enum import Enum
import tempfile
import shutil

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global process tracking for cleanup
_active_processes: List[subprocess.Popen] = []
_cleanup_registered = False

class ConfigError(Exception):
    """Configuration validation error"""
    pass

class ServiceError(Exception):
    """Service startup/management error"""
    pass

class ValidationError(Exception):
    """Input validation error"""
    pass

@dataclass
class ServiceHealth:
    """Service health status"""
    backend: bool = False
    frontend: bool = False
    ai_engine: bool = False
    database: bool = False

class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    LOCAL = "local"

@dataclass
class TodoItem:
    """Represents a TODO comment found in code"""
    file_path: str
    line_number: int
    content: str
    priority: str  # HIGH, MEDIUM, LOW
    category: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    context: Optional[str] = None

class TodoScanner:
    """Scans code files for TODO comments and extracts structured information"""

    # Enhanced TODO patterns with metadata support
    TODO_PATTERNS = [
        # Standard TODO with optional metadata
        r'#\s*TODO\s*(?:\[(?P<priority>HIGH|MEDIUM|LOW)\])?\s*(?:\((?P<assignee>\w+)\))?\s*:?\s*(?P<content>.*?)(?:\s*\[due:\s*(?P<due_date>[\d-]+)\])?',
        # Alternative comment styles
        r'//\s*TODO\s*(?:\[(?P<priority>HIGH|MEDIUM|LOW)\])?\s*(?:\((?P<assignee>\w+)\))?\s*:?\s*(?P<content>.*?)(?:\s*\[due:\s*(?P<due_date>[\d-]+)\])?',
        r'/\*\s*TODO\s*(?:\[(?P<priority>HIGH|MEDIUM|LOW)\])?\s*(?:\((?P<assignee>\w+)\))?\s*:?\s*(?P<content>.*?)(?:\s*\[due:\s*(?P<due_date>[\d-]+)\])?\s*\*/',
        # FIXME, HACK, BUG patterns
        r'#\s*(?P<category>FIXME|HACK|BUG|NOTE)\s*(?:\[(?P<priority>HIGH|MEDIUM|LOW)\])?\s*:?\s*(?P<content>.*)',
        r'//\s*(?P<category>FIXME|HACK|BUG|NOTE)\s*(?:\[(?P<priority>HIGH|MEDIUM|LOW)\])?\s*:?\s*(?P<content>.*)',
    ]

    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.file_extensions = self.config.get('file_extensions', [
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs',
            '.rb', '.php', '.swift', '.kt', '.scala', '.r', '.m'
        ])
        self.ignore_patterns = self.config.get('ignore_patterns', [
            'node_modules', 'vendor', '.git', '__pycache__', 'dist', 'build'
        ])

    def scan_directory(self, root_path: str) -> List[TodoItem]:
        """Recursively scan directory for TODO comments"""
        todos = []
        root_path = Path(root_path)

        for file_path in self._get_files(root_path):
            file_todos = self.scan_file(str(file_path))
            todos.extend(file_todos)

        return self._sort_todos(todos)

    def scan_file(self, file_path: str) -> List[TodoItem]:
        """Scan a single file for TODO comments"""
        todos = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                for pattern in self.TODO_PATTERNS:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        todo = self._create_todo_item(
                            file_path, line_num, match,
                            self._get_context(lines, line_num)
                        )
                        if todo:
                            todos.append(todo)

        except Exception as e:
            print(f"Error scanning {file_path}: {e}")

        return todos

    def _get_files(self, root_path: Path) -> List[Path]:
        """Get all eligible files for scanning"""
        files = []

        for path in root_path.rglob('*'):
            if path.is_file() and self._should_scan_file(path):
                files.append(path)

        return files

    def _should_scan_file(self, path: Path) -> bool:
        """Check if file should be scanned"""
        # Check ignore patterns
        for ignore in self.ignore_patterns:
            if ignore in str(path):
                return False

        # Check file extension
        return path.suffix in self.file_extensions

    def _create_todo_item(self, file_path: str, line_num: int,
                         match: re.Match, context: str) -> Optional[TodoItem]:
        """Create TodoItem from regex match"""
        groups = match.groupdict()

        content = groups.get('content', '').strip()
        if not content:
            return None

        return TodoItem(
            file_path=file_path,
            line_number=line_num,
            content=content,
            priority=groups.get('priority', 'MEDIUM'),
            category=groups.get('category', 'TODO'),
            assignee=groups.get('assignee'),
            due_date=groups.get('due_date'),
            context=context
        )

    def _get_context(self, lines: List[str], line_num: int,
                    context_lines: int = 2) -> str:
        """Get surrounding code context"""
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)

        context_lines = lines[start:end]
        return ''.join(context_lines)

    def _sort_todos(self, todos: List[TodoItem]) -> List[TodoItem]:
        """Sort TODOs by priority and due date"""
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}

        def sort_key(todo):
            priority = priority_order.get(todo.priority, 999)
            due_date = todo.due_date or '9999-99-99'
            return (priority, due_date, todo.file_path)

        return sorted(todos, key=sort_key)

    def export_todos(self, todos: List[TodoItem], format: str = 'json') -> str:
        """Export TODOs in various formats"""
        if format == 'json':
            return json.dumps([self._todo_to_dict(t) for t in todos], indent=2)
        elif format == 'markdown':
            return self._export_markdown(todos)
        elif format == 'csv':
            return self._export_csv(todos)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _todo_to_dict(self, todo: TodoItem) -> Dict:
        """Convert TodoItem to dictionary"""
        return {
            'file_path': todo.file_path,
            'line_number': todo.line_number,
            'content': todo.content,
            'priority': todo.priority,
            'category': todo.category,
            'assignee': todo.assignee,
            'due_date': todo.due_date,
            'context': todo.context
        }

    def _export_markdown(self, todos: List[TodoItem]) -> str:
        """Export TODOs as markdown"""
        md = "# TODO Report\n\n"
        md += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        # Group by priority
        by_priority = {}
        for todo in todos:
            priority = todo.priority
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(todo)

        for priority in ['HIGH', 'MEDIUM', 'LOW']:
            if priority in by_priority:
                md += f"## {priority} Priority\n\n"
                for todo in by_priority[priority]:
                    md += f"- **{todo.content}**\n"
                    md += f"  - File: `{todo.file_path}:{todo.line_number}`\n"
                    if todo.assignee:
                        md += f"  - Assignee: {todo.assignee}\n"
                    if todo.due_date:
                        md += f"  - Due: {todo.due_date}\n"
                    md += "\n"

        return md

    def _export_csv(self, todos: List[TodoItem]) -> str:
        """Export TODOs as CSV"""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'File', 'Line', 'Content', 'Priority',
            'Category', 'Assignee', 'Due Date'
        ])

        # Data
        for todo in todos:
            writer.writerow([
                todo.file_path,
                todo.line_number,
                todo.content,
                todo.priority,
                todo.category or '',
                todo.assignee or '',
                todo.due_date or ''
            ])

        return output.getvalue()

def scan_directory(directory: str) -> List[str]:
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

def query_ai(prompt: str) -> str:
    ollama_endpoint = 'http://localhost:11434/api/generate'
    # Check if endpoint is accessible
    health_check = requests.get('http://localhost:11434')
    if health_check.status_code != 200 or 'ollama' not in health_check.text.lower():
        return 'Ollama server not running or misconfigured. Start Ollama and ensure endpoint is correct.'
    response = requests.post(ollama_endpoint, json={"model": "llama3", "prompt": prompt})
    if response.status_code == 200:
        return response.text
    elif response.status_code == 404:
        return 'AI endpoint not found. Check Ollama configuration.'
    else:
        return f'AI query failed with status code {response.status_code}'

def main():
    files = scan_directory('.')
    ai_suggestion = query_ai('Suggest sorting and renaming strategies for files: ' + str(files))
    print(ai_suggestion)

if __name__ == '__main__':
    main()
