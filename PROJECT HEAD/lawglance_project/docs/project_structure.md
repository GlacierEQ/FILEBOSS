# LawGlance Project Structure

This document outlines the structure of the LawGlance project to help new contributors understand how the code is organized.

## Overview

LawGlance is organized as a modular Python package with clear separation of concerns:

```
lawglance_project/
├── app.py                         # Streamlit UI entry point
├── src/                           # Core source code
│   ├── __init__.py
│   ├── lawglance_main.py          # Main LawGlance class
│   ├── main.py                    # FastAPI application 
│   ├── document_loader.py         # Utility for loading documents
│   ├── utils/                     # Utility modules
│   │   ├── __init__.py
│   │   ├── document_editor.py     # Document editing functionality
│   │   ├── huggingface_setup.py   # Hugging Face integration utilities
│   │   └── README.md              # Documentation for utilities
│   └── integrations/              # External integrations
│       ├── __init__.py
│       └── simple_lawglance_hf.py # Hugging Face model integration
├── data/                          # Legal documents
│   └── sample_legal_text.txt      # Sample legal document
├── logo/                          # Branding assets
│   └── create_placeholder_logo.py # Script to generate logo
├── docs/                          # Documentation
│   ├── usage.md                   # User guide
│   ├── document_editor.md         # Document editor documentation
│   └── project_structure.md       # This file
├── tests/                         # Test files
│   ├── __init__.py
│   ├── test_lawglance.py          # Tests for core functionality
│   └── test_document_editor.py    # Tests for document editor
├── examples/                      # Example usage scripts
│   └── huggingface_example.py     # Example of using Hugging Face models
├── scripts/                       # Utility scripts
│   ├── setup_huggingface.sh       # Script to set up Hugging Face
│   ├── reset_database.sh          # Script to reset the vector DB
│   └── run_docker.sh              # Script to run Docker containers
├── .github/                       # GitHub specific files
│   └── workflows/                 # CI/CD workflows
│       └── ci.yml                 # Continuous Integration config
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
├── setup.py                       # Project setup script
├── lawglance_runner.py            # CLI runner script
├── Dockerfile                     # Container definition
├── docker-compose.yml             # Multi-container setup
├── docker-entrypoint.sh           # Docker entry point script
├── .gitignore                     # Git ignore file
└── LICENSE                        # License file
```

## Key Components

### Core Components

- **LawGlance Class** (`src/lawglance_main.py`): The main class that handles the conversation with the LLM and document retrieval.
- **FastAPI App** (`src/main.py`): Provides a REST API for interacting with LawGlance.
- **Streamlit UI** (`app.py`): User-friendly web interface for LawGlance.

### Utilities

- **Document Loader** (`src/document_loader.py`): Processes and loads documents into the vector store.
- **Document Editor** (`src/utils/document_editor.py`): Edits legal documents using natural language instructions.
- **Hugging Face Setup** (`src/utils/huggingface_setup.py`): Helps set up Hugging Face API access.

### Integrations

- **Hugging Face Integration** (`src/integrations/simple_lawglance_hf.py`): Allows using Hugging Face models with LawGlance.

## Coding Conventions

- Use Python type hints throughout the codebase
- Follow PEP 8 style guidelines
- Write docstrings for all modules, classes and functions
- Keep classes focused on a single responsibility
- Use meaningful variable and function names
- Include appropriate error handling
- Add unit tests for new functionality

## Architecture Principles

1. **Modularity**: Components should be self-contained with clear interfaces
2. **Extensibility**: Make it easy to add new features without modifying existing code
3. **Error Handling**: Robust error handling with informative messages
4. **Documentation**: All code should be well-documented
5. **Testing**: All components should have automated tests

## Data Flow

1. User inputs a legal question via the UI or API
2. The query is processed by the LawGlance main class
3. Relevant legal information is retrieved from the vector database
4. The LLM generates a response incorporating the retrieved information
5. The response is returned to the user

## Extension Points

To extend LawGlance:

- Add new model integrations in `src/integrations/`
- Add new utilities in `src/utils/`
- Enhance document processing in `src/document_loader.py`
- Add new UI features in `app.py`
