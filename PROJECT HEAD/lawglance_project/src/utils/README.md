# LawGlance Utilities

This directory contains various utility modules used throughout the LawGlance project.

## Available Utilities

### Document Editor

The `document_editor.py` module provides functionality for editing legal documents using natural language instructions. It features:

- Text replacement, insertion and deletion
- Text formatting (bold, italic, underline, colors)
- Section management
- Support for .docx, .doc, .txt and .md files

Example usage:

```python
from utils.document_editor import DocumentEditor

editor = DocumentEditor()
result = editor.edit_document(
    "contract.docx",
    "Replace 'Party A' with 'Acme Corporation'"
)
```

See the [Document Editor documentation](../../docs/document_editor.md) for more details.

### Hugging Face Setup

The `huggingface_setup.py` module helps set up and verify Hugging Face API tokens for using open-source models:

```python
from utils.huggingface_setup import setup_huggingface

# This will prompt for a token if needed
success = setup_huggingface()
```

## Adding New Utilities

When adding new utilities:

1. Create a new Python file in this directory
2. Add proper documentation with docstrings
3. Include type hints
4. Add appropriate unit tests in `/tests`
5. Update this README with information about your utility
