# PhotoPrism Sorting Department Guide

## Overview

The PhotoPrism Sorting Department is a multi-agent file sorting system integrated with PhotoPrism. It uses two specialized AIs:

1. **Fast AI**: Quick scanning and categorization
2. **Accurate AI**: Deep analysis and final naming

Files are sorted hierarchically based on content and renamed with the format:
`YYMMDD-[Description Up to 30 Chars]`

## Features

- **Multi-Agent Architecture**: Two specialized AIs work together to provide both speed and accuracy
- **Hierarchical Sorting**: Files are organized into categories and subcategories based on content
- **Smart Renaming**: Files are renamed with a date and descriptive name for easy identification
- **Memory System**: Both AIs maintain a memory of past decisions to improve consistency
- **PhotoPrism Integration**: Automatically updates PhotoPrism's index after organizing files
- **API Access**: RESTful API for programmatic access to the sorting functionality

## Setup

1. Run the setup script: `setup_photoprism_sorter.bat`
2. This will:
   - Create the necessary directories
   - Register the component with the Sorting Hat service
   - Create initial category folders

## Configuration

The system can be configured by editing the `integration/photoprism/config.json` file:

```json
{
    "sorting_department_path": "C:/Users/casey/PhotoPrism/storage/sorting-dept",
    "photoprism_url": "http://localhost:2342",
    "photoprism_username": "admin",
    "photoprism_password": "admin",
    "fast_ai": {
        "memory_limit": 100,
        "confidence_threshold": 0.7,
        "max_processing_time": 1.0
    },
    "accurate_ai": {
        "memory_limit": 200,
        "confidence_threshold": 0.9,
        "max_processing_time": 5.0
    },
    "file_types": {
        "image": [
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".tiff",
            ".webp",
            ".heic"
        ],
        "video": [
            ".mp4",
            ".mov",
            ".avi",
            ".mkv",
            ".flv",
            ".wmv"
        ],
        "document": [
            ".pdf",
            ".doc",
            ".docx",
            ".txt",
            ".rtf",
            ".odt",
            ".md"
        ]
    },
    "logging": {
        "level": "INFO",
        "file": "photoprism_sorter.log",
        "max_size": 10485760,
        "backup_count": 5
    }
}
```

## Usage

### Starting the Service

Run the service using the provided batch file:

```
run_photoprism_sorter.bat
```

### Adding Files for Sorting

Simply place files in the sorting department directory:

```
C:/Users/casey/PhotoPrism/storage/sorting-dept
```

The system will automatically:
1. Detect new files
2. Analyze them with Fast AI
3. Refine the analysis with Accurate AI
4. Sort them into the appropriate category
5. Rename them with the YYMMDD-[Description] format
6. Update PhotoPrism's index

### Using the API

The system provides a RESTful API for programmatic access:

- `GET /api/photoprism/status` - Get the status of the sorting department
- `POST /api/photoprism/process` - Process a specific file
- `POST /api/photoprism/upload` - Upload and process a file
- `GET /api/photoprism/categories` - Get the list of categories
- `GET /api/photoprism/files/{category}` - Get files in a specific category

## How It Works

### Multi-Agent Collaboration

1. **Fast AI**:
   - Quickly analyzes file metadata and filename
   - Proposes initial categories and description
   - Maintains a lightweight memory of recent decisions

2. **Accurate AI**:
   - Performs deeper analysis of file content
   - Refines categories and description
   - Maintains a persistent memory of past decisions
   - Makes the final decision on categorization and naming

### Hierarchical Structure

Files are organized into a hierarchical structure:

```
sorting-dept/
├── People/
│   ├── 2023-01/
│   │   ├── 230101-FamilyReunion.jpg
│   │   └── 230115-JohnBirthdayParty.jpg
│   └── 2023-02/
│       └── 230205-TeamMeeting.jpg
├── Events/
│   └── 2023-01/
│       └── 230120-ConferencePresentationNYC.jpg
└── Documents/
    └── 2023-02/
        └── 230210-ProjectProposal.pdf
```

### File Renaming

Files are renamed using the format: `YYMMDD-[Description]`

- `YYMMDD`: Date from file metadata (creation date)
- `Description`: Up to 30 characters describing the file content

Examples:
- `230101-FamilyReunion.jpg`
- `230210-ProjectProposal.pdf`
- `230315-VacationBeachSunset.jpg`

## Troubleshooting

### Common Issues

1. **Files not being processed**:
   - Check if the sorting department service is running
   - Verify the sorting department directory exists
   - Check permissions on the directory

2. **PhotoPrism integration not working**:
   - Verify PhotoPrism is running
   - Check the URL, username, and password in the config
   - Ensure the PhotoPrism API is accessible

3. **Incorrect categorization**:
   - The AI models improve over time as they build memory
   - You can manually move files to train the system

### Logs

Check the log file for detailed information:

```
photoprism_sorter.log
```

## Advanced Usage

### Command Line Interface

Process individual files using the command line:

```
python integration/photoprism/photoprism_sorter.py --file C:/path/to/file.jpg
```

### Custom Categories

You can modify the categories by editing the `HIERARCHICAL_CATEGORIES` dictionary in `photoprism_sorter.py`.
