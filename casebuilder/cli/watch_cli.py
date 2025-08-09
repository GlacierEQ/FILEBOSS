"""
Watch Folder CLI

Command-line interface for managing watch folders.
"""

import os
import sys
import logging
import argparse
from typing import List, Optional, Dict, Any
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..services.watch_service import WatchService
from ..services.database import DatabaseService, init_db
from ..services.file_organizer import FileOrganizer
from ..models import FileCategory
from ..config import settings

# Initialize Typer app
app = typer.Typer(help="Manage watch folders for automatic file processing")
console = Console()

# Global service instances
db_service: Optional[DatabaseService] = None
organizer: Optional[FileOrganizer] = None
watch_service: Optional[WatchService] = None

def get_services() -> tuple[DatabaseService, FileOrganizer, WatchService]:
    """Initialize and return service instances."""
    global db_service, organizer, watch_service
    
    if db_service is None:
        # Initialize database
        init_db()
        db_service = DatabaseService(next(DatabaseService.get_db()))
    
    if organizer is None:
        organizer = FileOrganizer()
    
    if watch_service is None:
        watch_service = WatchService(db_service=db_service, organizer=organizer)
        watch_service.start()
    
    return db_service, organizer, watch_service

@app.command()
def add(
    directory: str = typer.Argument(..., help="Directory to watch"),
    case_id: str = typer.Option(..., "--case", "-c", help="Case ID to associate with files"),
    subcase_id: Optional[str] = typer.Option(None, "--subcase", "-s", help="Subcase ID (optional)"),
    category: Optional[FileCategory] = typer.Option(
        None, "--category", "-C", 
        help="File category (e.g., Evidence, Documents, Media)"
    ),
    recursive: bool = typer.Option(
        True, "--no-recursive", "-nr", 
        help="Do not watch subdirectories recursively",
        is_flag=True,
        flag_value=False
    ),
    process_existing: bool = typer.Option(
        True, "--no-process-existing", "-np",
        help="Do not process existing files in the directory",
        is_flag=True,
        flag_value=False
    )
):
    """Add a directory to watch for new files."""
    try:
        # Get services
        _, _, watch_service = get_services()
        
        # Convert to absolute path
        directory = os.path.abspath(directory)
        
        # Check if directory exists
        if not os.path.isdir(directory):
            console.print(f"[red]Error: Directory not found: {directory}")
            raise typer.Exit(1)
        
        # Add watch
        success = watch_service.add_watch(
            directory=directory,
            case_id=case_id,
            subcase_id=subcase_id,
            category=category,
            recursive=recursive
        )
        
        if success:
            console.print(f"[green]✓ Now watching directory: {directory}")
            
            # Process existing files if requested
            if process_existing:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=True,
                ) as progress:
                    task = progress.add_task("Processing existing files...", total=1)
                    
                    # Count files to process
                    file_count = 0
                    if recursive:
                        for root, _, files in os.walk(directory):
                            file_count += len([f for f in files if not f.startswith('.')])
                    else:
                        file_count = len([
                            f for f in os.listdir(directory) 
                            if os.path.isfile(os.path.join(directory, f)) and not f.startswith('.')
                        ])
                    
                    if file_count > 0:
                        progress.update(task, total=file_count, description=f"Processing {file_count} files...")
                        
                        # Process files
                        processed = 0
                        if recursive:
                            for root, _, files in os.walk(directory):
                                for file in files:
                                    if file.startswith('.'):
                                        continue
                                    file_path = os.path.join(root, file)
                                    watch_service.watches[directory]['handler']._process_file(file_path)
                                    processed += 1
                                    progress.update(task, advance=1, description=f"Processed {processed}/{file_count} files")
                        else:
                            for file in os.listdir(directory):
                                file_path = os.path.join(directory, file)
                                if os.path.isfile(file_path) and not file.startswith('.'):
                                    watch_service.watches[directory]['handler']._process_file(file_path)
                                    processed += 1
                                    progress.update(task, advance=1, description=f"Processed {processed}/{file_count} files")
                        
                        console.print(f"[green]✓ Processed {processed} existing files")
                    else:
                        progress.update(task, description="No files to process")
                        
        else:
            console.print(f"[yellow]⚠ Directory already being watched or error occurred: {directory}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}")
        raise typer.Exit(1)

@app.command()
def remove(
    directory: str = typer.Argument(..., help="Directory to stop watching")
):
    """Stop watching a directory."""
    try:
        # Get services
        _, _, watch_service = get_services()
        
        # Convert to absolute path
        directory = os.path.abspath(directory)
        
        # Remove watch
        if watch_service.remove_watch(directory):
            console.print(f"[green]✓ Stopped watching directory: {directory}")
        else:
            console.print(f"[yellow]⚠ Directory was not being watched: {directory}")
            
    except Exception as e:
        console.print(f"[red]Error: {e}")
        raise typer.Exit(1)

@app.command("list")
def list_watches():
    """List all watched directories."""
    try:
        # Get services
        _, _, watch_service = get_services()
        
        # Get watches
        watches = watch_service.list_watches()
        
        if not watches:
            console.print("[yellow]No directories are being watched")
            return
        
        # Create table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Directory", style="dim", width=50)
        table.add_column("Case ID")
        table.add_column("Subcase ID")
        table.add_column("Category")
        table.add_column("Recursive")
        
        # Add rows
        for watch in watches:
            table.add_row(
                watch['directory'],
                watch['case_id'],
                watch['subcase_id'] or "-",
                watch['category'] or "-",
                "✓" if watch['recursive'] else "✗"
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}")
        raise typer.Exit(1)

@app.command()
def start():
    """Start the watch service."""
    try:
        # Get services
        _, _, watch_service = get_services()
        watch_service.start()
        console.print("[green]✓ Watch service started")
        
    except Exception as e:
        console.print(f"[red]Error: {e}")
        raise typer.Exit(1)

@app.command()
def stop():
    """Stop the watch service."""
    try:
        global watch_service
        if watch_service is not None:
            watch_service.stop()
            watch_service = None
            console.print("[green]✓ Watch service stopped")
        else:
            console.print("[yellow]⚠ Watch service is not running")
            
    except Exception as e:
        console.print(f"[red]Error: {e}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
