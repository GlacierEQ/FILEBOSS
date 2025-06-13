# CodexFlō: AI-Driven Strategic File Nexus

CodexFlō is a comprehensive AI-powered file management system designed to intelligently organize, analyze, and extract insights from legal documents. It combines advanced document processing with legal intelligence to automate case building and document management.

## Key Features

- **Intelligent Document Processing**: Automatically classifies, extracts metadata, and organizes files
- **Legal Intelligence**: Detects privilege, extracts citations, identifies deadlines, and builds case timelines
- **Advanced Organization**: Creates structured filing systems based on document content and relationships
- **Case Building Engine**: Automatically assembles evidence, identifies contradictions, and builds case timelines
- **Security & Compliance**: Implements ethical walls, privilege detection, and comprehensive audit logging

## System Architecture

CodexFlō consists of several integrated components:

- **CLI Interface**: Command-line tools for system management and file processing
- **Legal Pipeline**: Core document analysis and legal intelligence features
- **Security Engine**: Handles access control, encryption, and compliance
- **Storage Manager**: Organizes files with intelligent naming and structure
- **Integration Layer**: Connects all components for seamless operation
- **API Backend**: Provides REST API access to all system features

## Getting Started

### Prerequisites

- Python 3.8+
- Node.js 14+ (for frontend)
- Storage space for document database

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/codexflo.git
   cd codexflo
   ```

2. Install Python dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Initialize the configuration:
   ```
   python -m cli.codexflo_cli init --interactive
   ```

4. Launch the system:
   ```
   python -m cli.codexflo_cli launch --watch-dir /path/to/documents
   ```

## Usage

### Processing Files

```
python -m cli.codexflo_cli process --file /path/to/document.pdf
```

### Building Case Analysis

```
python -m cli.codexflo_cli case build --case-id CASE123
```

### Generating Reports

```
python -m cli.codexflo_cli report --type case_summary --case-id CASE123
```

## API Access

The system provides a REST API for integration with other applications:

- `GET /health` - System health check
- `POST /files/process` - Process a file
- `POST /cases/build` - Build a case analysis
- `POST /reports/generate` - Generate reports

## Configuration

The system is configured through a YAML file, typically located at `config/ai_file_explorer.yml`. Key configuration sections include:

- `app`: General application settings
- `ai`: AI provider and model settings
- `storage`: Storage locations and database settings
- `legal`: Legal intelligence features and settings
- `security`: Security and compliance settings
- `modules`: Enable/disable specific system modules

## Legal Intelligence Features

- **Document Classification**: Automatically identifies document types (pleadings, motions, etc.)
- **Entity Extraction**: Identifies people, organizations, and other entities
- **Timeline Generation**: Creates chronological case timelines from document dates
- **Citation Extraction**: Identifies legal citations and references
- **Privilege Detection**: Flags potentially privileged content
- **Contradiction Detection**: Identifies inconsistencies between documents
- **Deadline Tracking**: Extracts and monitors legal deadlines

## Security Features

- **Ethical Walls**: Prevents unauthorized access across case boundaries
- **Privilege Protection**: Detects and protects privileged content
- **Access Control**: Role-based permissions for document access
- **Audit Logging**: Comprehensive logging of all system activities
- **Encryption**: Optional document encryption for sensitive materials

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.