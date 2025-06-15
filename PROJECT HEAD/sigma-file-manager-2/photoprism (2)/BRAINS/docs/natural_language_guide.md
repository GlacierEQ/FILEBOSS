# Natural Language File Organizer Guide

The Natural Language File Organizer is a powerful feature of the Sorting Hat system that lets you organize files using plain English instructions. Instead of complex rules or technical syntax, you can simply describe what you want to do, and the system will interpret your instructions and organize your files accordingly.

## Getting Started

You can access the Natural Language File Organizer in several ways:

1. **Command Line Interface**: Run `python nlorganize.py` to use the interactive command-line tool
2. **Graphical User Interface**: Run `nl_gui.py` or double-click `organize_with_language.bat` for a visual interface
3. **Web Dashboard**: Access the Natural Language component in the web dashboard
4. **API**: Use the `/api/nl/organize` endpoint programmatically

## Basic Usage

Using the Natural Language Organizer is simple:

1. Enter your instruction in plain English
2. Specify a target directory (optional, uses default safe directory if not specified)
3. Click "Organize Files" or press Enter

The system will:
1. Interpret your instruction
2. Find files that match your criteria
3. Move or rename them according to your instructions
4. Report what it did

## Example Instructions

Here are some examples of what you can tell the system to do:

- "Move all PDFs to the Documents folder and name them by date"
- "Create folders for photos by year and month, then organize all images"
- "Organize code files by language into the Programming folder"
- "Move large video files older than 30 days to the Archive folder"
- "Find all downloads from last week and sort them by type"
- "Collect all text files and put them in a Text folder"
- "Sort all screenshots into a Screenshots folder and name them by date"

## Advanced Features

### Time-Based Organization

You can specify time periods in your instructions:

- "Move files from yesterday to the Recent folder"
- "Archive files older than 30 days"
- "Organize last week's downloads by type"

### Content-Based Organization

The system can organize files based on their content:

- "Group text files by content similarity"
- "Find Python files containing 'database' and move them to the Database project folder"

### Naming Patterns

You can specify naming patterns:

- "Rename image files to include their creation date"
- "Add sequential numbers to document files"
- "Convert filenames to lowercase"

## Troubleshooting

If the organization doesn't work as expected:

1. **Be more specific**: "Move PDFs" is more clear than "Move documents"
2. **Check permissions**: Ensure the system has permission to access and modify files
3. **Verify paths**: Make sure the source and destination directories exist
4. **Check logs**: Look at the sorting_service.log file for detailed error information

## How It Works

Behind the scenes, the Natural Language Organizer:

1. Processes your instruction using natural language understanding
2. Extracts file types, locations, and organization rules
3. Converts these into specific file operations
4. Executes them safely using the core Sorting Hat system

The more you use the system, the better it gets at understanding your preferences and organizational style.
