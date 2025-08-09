# FileBoss Organizer & Analyzer

A powerful file organization and analysis tool that helps you manage your files efficiently.

## Features

- **File Scanning**: Recursively scan directories and index files with detailed metadata
- **File Analysis**: Get insights into file types, sizes, and usage patterns
- **Duplicate Detection**: Find and manage duplicate files using content hashing
- **Smart Organization**: Automatically organize files by type into appropriate directories
- **Custom Rules**: Extensible system for adding custom organization rules
- **Comprehensive Logging**: Detailed logging for tracking operations

## Installation

1. Ensure you have Python 3.10+ installed
2. Install the required dependencies:
   ```bash
   pip install -e .
   ```

## Basic Usage

### Command Line Interface

```bash
# Scan a directory and show analysis
python -m app.core.file_organizer /path/to/directory

# Find duplicate files
python -m app.core.file_organizer /path/to/directory --find-duplicates

# Organize files by type
python -m app.core.file_organizer /path/to/directory --organize --output-dir /path/to/output

# Combine options
python -m app.core.file_organizer /path/to/directory --find-duplicates --organize
```

### Python API

```python
from app.core.file_organizer import FileOrganizer

# Initialize the organizer with a directory
organizer = FileOrganizer("/path/to/directory")

# Scan the directory
organizer.scan_directory()

# Find duplicates
duplicates = organizer.find_duplicates()

# Organize files by type
organizer.organize_by_type("/path/to/output")

# Get analysis report
analysis = organizer.analyze_file_usage()
```

## Advanced Usage

### Custom File Types

You can extend the file type detection by modifying the `_get_file_type` method in the `FileOrganizer` class.

### Custom Organization Rules

To implement custom organization rules, create a subclass of `FileOrganizer` and override the `organize_by_type` method:

```python
class CustomOrganizer(FileOrganizer):
    def organize_by_type(self, output_dir):
        # Implement custom organization logic
        pass
```

### Logging

The module uses Python's built-in logging. Configure logging to see detailed information:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

## Example Output

### File Analysis

```
File Analysis:
Total files: 1,234
Total size: 15.67 GB

Files by type:
  document: 450 files
  image: 320 files
  video: 200 files
  audio: 150 files
  archive: 100 files
  other: 14 files

Last modified:
  < 30 days: 800 files
  30-90 days: 300 files
  90-365 days: 100 files
  > 1 year: 34 files

Found 50 duplicate files (in 15 sets)
```

## License

Proprietary - All rights reserved
