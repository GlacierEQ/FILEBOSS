# Omnithread Forensic Protocol

A comprehensive, multi-agent forensic data collection and analysis framework designed for zero-loss, total-scope forensic investigations across cloud and local storage systems.

## Features

- **Multi-Source Data Collection**: Unified interface for local filesystems, cloud storage, email, and more
- **Artifact-Centric Processing**: Every piece of data is treated as a first-class forensic artifact
- **Extensible Agent System**: Plug-in architecture for specialized analysis modules
- **Comprehensive Metadata**: Rich metadata capture including file properties, content analysis, and relationships
- **Scalable Architecture**: Designed to handle everything from single files to petabyte-scale storage

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/omnithread-forensic.git
   cd omnithread-forensic
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Quick Start

```python
from omnithread_forensic.core.orchestrator import OmniThreadOrchestrator
from omnithread_forensic.sources.local_fs import LocalFSConfig
import asyncio

async def main():
    # Initialize the orchestrator
    orchestrator = OmniThreadOrchestrator()
    
    # Add a local filesystem source
    fs_config = {
        "source_type": "local_fs",
        "name": "My Documents",
        "description": "Personal documents",
        "base_path": "~/Documents",
        "include_hidden": False,
        "skip_system_files": True
    }
    
    await orchestrator.add_source(fs_config)
    
    # Process the sources
    await orchestrator.process_sources()
    
    # Print some statistics
    stats = orchestrator.stats.finalize()
    print(f"Processed {stats['processed_artifacts']} artifacts in {stats['processing_time_seconds']:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
```

## Project Structure

```
omnithread_forensic/
├── config/                  # Configuration settings
│   └── settings.py          # Application settings and environment variables
├── core/                    # Core framework code
│   ├── models.py            # Data models and Pydantic schemas
│   ├── orchestrator.py      # Main orchestration logic
│   └── processing.py        # Core processing pipeline
├── sources/                 # Data source implementations
│   ├── base.py              # Base source interface
│   ├── local_fs.py          # Local filesystem source
│   ├── google_drive.py      # Google Drive source (TODO)
│   └── ...                  # Other sources
├── agents/                  # Analysis agents
│   ├── base.py              # Base agent interface
│   ├── timeline.py          # Timeline analysis agent (TODO)
│   ├── contradiction.py     # Contradiction detection (TODO)
│   └── ...                  # Other agents
├── storage/                 # Storage backends
│   ├── base.py              # Base storage interface
│   ├── local.py             # Local file storage
│   └── ...                  # Other storage backends
├── utils/                   # Utility functions
│   ├── hashing.py           # Hashing utilities
│   ├── mime.py              # MIME type detection
│   └── ...                  # Other utilities
└── tests/                   # Unit and integration tests
```

## Configuration

Configuration is handled through environment variables and/or a `.env` file. See `.env.example` for available options.

## Data Model

The system uses a rich data model to represent forensic artifacts:

- **Artifact**: Base class for all forensic evidence
- **ArtifactSource**: Origin information for artifacts
- **ArtifactRelationship**: Relationships between artifacts
- **ProcessingLog**: Audit trail of all processing steps

## Adding New Data Sources

To add a new data source, create a new class in the `sources` directory that implements the `BaseSource` interface.

## Creating Analysis Agents

Analysis agents process artifacts to extract information, detect patterns, and create relationships. To create a new agent, extend the `BaseAgent` class and implement the required methods.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please read our [contributing guidelines](CONTRIBUTING.md) before submitting pull requests.

## Documentation

For full documentation, see the [docs](docs/) directory.

## Support

For support, please open an issue in the GitHub issue tracker.

## Status

This project is currently in active development. The API is subject to change.
