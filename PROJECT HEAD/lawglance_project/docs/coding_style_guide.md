# LawGlance Coding Style Guide

This document outlines the coding standards and best practices to be followed in the LawGlance project.

## General Principles

- Code should be simple, readable, and maintainable
- Follow PEP 8 conventions for Python code
- Document all functions, classes, and modules
- Write tests for all functionality
- Handle errors gracefully
- Keep functions short and focused

## Naming Conventions

### Variables and Functions
- Use snake_case for variables and functions
  - ✅ `document_content`, `parse_document()`
  - ❌ `documentContent`, `parseDocument()`

### Classes
- Use PascalCase (or UpperCamelCase) for class names
  - ✅ `DocumentParser`, `LegalAnalyzer`
  - ❌ `documentParser`, `legal_analyzer`

### Constants
- Use UPPER_CASE_WITH_UNDERSCORES for constants
  - ✅ `MAX_DOCUMENT_SIZE`, `DEFAULT_TIMEOUT`
  - ❌ `MaxDocumentSize`, `default_timeout`

### Private Methods/Variables
- Prefix with a single underscore for protected (internal use)
  - ✅ `_parse_text()`, `_content_buffer`
- Prefix with double underscore for truly private
  - ✅ `__calculate_checksum()`, `__temp_data`

## Code Structure

### Imports
- Group imports in the following order:
  1. Standard library imports
  2. Third-party library imports
  3. Local application imports
- Separate each group with a blank line
- Sort imports alphabetically within each group

```python
# Standard library imports
import os
import sys
from typing import Dict, List, Optional

# Third-party imports
import numpy as np
import pandas as pd
from docx import Document

# Local application imports
from src.utils.formatting import format_text
from src.utils.validation import validate_input
```

### Type Hints
- Use type hints for all function parameters and return values
- Use `Optional[Type]` for parameters that can be None
- Use `Union[Type1, Type2]` for parameters that can be multiple types

```python
def process_document(
    file_path: str,
    max_sections: Optional[int] = None,
    settings: Dict[str, Any] = None
) -> List[Dict[str, str]]:
    """Process a document and extract sections."""
    # Implementation here
```

## Documentation

### Docstrings
- All modules, classes, and functions should have docstrings
- Follow Google-style docstrings
- Include:
  - Brief description
  - Args section with parameter descriptions
  - Returns section with return value description
  - Raises section when exceptions are explicitly raised

```python
def analyze_legal_text(text: str, jurisdiction: str = "US") -> Dict[str, Any]:
    """
    Analyze legal text to extract key information.
    
    Args:
        text: The legal text to analyze
        jurisdiction: The legal jurisdiction (default: "US")
        
    Returns:
        Dictionary containing extracted legal entities and concepts
        
    Raises:
        ValueError: If text is empty or jurisdiction is invalid
    """
    # Implementation here
```

## Error Handling

- Use specific exceptions rather than catching all exceptions
- Provide informative error messages
- Re-raise exceptions when appropriate with additional context

```python
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
except FileNotFoundError:
    raise FileNotFoundError(f"Document not found at {file_path}")
except UnicodeDecodeError:
    raise ValueError(f"Unable to decode {file_path}. Try specifying the correct encoding.")
```

## Testing

- Write unit tests for all functions and classes
- Name test files with `test_` prefix
- Name test functions with descriptive names that start with `test_`
- Use appropriate assertions for the condition being tested
- Set up common test fixtures using pytest fixtures or setUp/tearDown methods

```python
def test_document_parser_extracts_correct_sections():
    """Test that the document parser extracts the expected sections."""
    # Test implementation
```

## Additional Best Practices

1. Avoid magic numbers - use named constants
2. Keep functions short (aim for under 30 lines)
3. Use dataclasses for data containers
4. Prefer composition over inheritance
5. Use explicit return statements (avoid implicit None returns)
6. Use f-strings for string formatting
7. Add TODO comments for future improvements with GitHub issue numbers
8. Use context managers (with statements) for resource management
