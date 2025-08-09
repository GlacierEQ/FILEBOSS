# FILEBOSS File Organizer

A powerful and extensible file organization and analysis library for Python.

## Features

- **File Organization**: Organize files by type, date, or custom rules
- **Duplicate Detection**: Find and manage duplicate files
- **File Analysis**: Get detailed statistics and metadata about files and directories
- **Command Line Interface**: Easy-to-use CLI for common operations
- **Extensible**: Easily add new file types and organization rules
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Installation

```bash
pip install -e .
```

## Usage

### Python API

```python
from pathlib import Path
from app.core.organizer import FileOrganizer

# Initialize the organizer
organizer = FileOrganizer(dry_run=False, overwrite=False)

# Organize files by type
organizer.organize_by_type(
    source_dir=Path('/path/to/source'),
    dest_dir=Path('/path/to/destination'),
    copy=False
)

# Find duplicate files
duplicates = organizer.find_duplicates(Path('/path/to/search'))

# Analyze directory contents
analysis = organizer.analyze_directory(Path('/path/to/analyze'))
```

### Command Line Interface

```bash
# Organize files by type
python -m app.core.organizer organize /path/to/source --output-dir /path/to/destination

# Find duplicate files
python -m app.core.organizer find-duplicates /path/to/search

# Analyze directory contents
python -m app.core.organizer analyze /path/to/analyze

# Get help
python -m app.core.organizer --help
```

## Available Commands

### Organize

Organize files into directories based on type, date, or other criteria.

```bash
# Organize by file type (default)
python -m app.core.organizer organize /source --output-dir /destination

# Organize by date
python -m app.core.organizer organize /source --by date --date-format "%Y-%m"

# Copy files instead of moving them
python -m app.core.organizer organize /source --output-dir /destination --copy

# Only process specific file types
python -m app.core.organizer organize /source --pattern "*.jpg,*.png"
```

### Find Duplicates

Find and optionally delete duplicate files.

```bash
# Find duplicate files
python -m app.core.organizer find-duplicates /path/to/search

# Delete duplicate files (keeping one copy)
python -m app.core.organizer find-duplicates /path/to/search --delete
```

### Analyze

Get detailed information about files and directories.

```bash
# Analyze directory contents
python -m app.core.organizer analyze /path/to/analyze

# Output results as JSON
python -m app.core.organizer analyze /path/to/analyze --json
```

### Scan

List files in a directory with metadata.

```bash
# List all files
python -m app.core.organizer scan /path/to/scan

# Filter by pattern
python -m app.core.organizer scan /path/to/scan --pattern "*.py"
```

## Configuration

You can configure the organizer using the following environment variables:

- `FILE_ORGANIZER_DRY_RUN`: Set to `1` to enable dry run mode
- `FILE_ORGANIZER_OVERWRITE`: Set to `1` to overwrite existing files
- `FILE_ORGANIZER_INCLUDE_HIDDEN`: Set to `1` to include hidden files
- `FILE_ORGANIZER_LOG_LEVEL`: Set the log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Extending

### Adding New File Types

To add support for new file types, update the `get_file_type` function in `file_utils.py`.

### Custom Organization Rules

Create a new method in the `FileOrganizer` class to implement custom organization logic.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
