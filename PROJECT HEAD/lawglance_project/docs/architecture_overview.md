# LawGlance Architecture Overview

This document provides a high-level overview of the LawGlance codebase architecture to help developers understand how components relate to each other.

## Core Components Diagram

```
+-------------------+      +-------------------+      +-----------------+
|                   |      |                   |      |                 |
|   User Interface  |----->|  LawGlance Core   |----->|  Language Model |
|   (app.py/CLI)    |      | (lawglance_main)  |      |  (OpenAI/HF)    |
|                   |      |                   |      |                 |
+-------------------+      +--------+----------+      +-----------------+
                                    |
                                    v
                           +-------------------+
                           |                   |
                           |   Vector Storage  |
                           | (Chroma/FAISS DB) |
                           |                   |
                           +-------------------+
```

## Module Relationship Map

### 1. User Interaction Layer
- `app.py` - Streamlit web interface
- `src/cli.py` - Command-line interface
- `src/main.py` - FastAPI endpoints

### 2. Core Processing Layer  
- `src/lawglance_main.py` - Core reasoning and orchestration
- `src/utils/document_loader.py` - Document ingestion pipeline
- `src/utils/document_compare.py` - Document comparison functionality
- `src/utils/document_editor.py` - Document editing functionality

### 3. Data Management Layer
- Vector databases (Chroma)
- Document storage
- Configuration management

### 4. External Integration Layer
- `src/integrations/simple_lawglance_hf.py` - Hugging Face models integration

## Data Flow

1. **Document Processing Pipeline**:
   ```
   Raw Documents → document_loader.py → Vector Embeddings → Chroma DB
   ```

2. **Query Processing Pipeline**:
   ```
   User Query → lawglance_main.py → Vector DB Retrieval → LLM Processing → Response
   ```

3. **Document Editing Pipeline**:
   ```
   User Instructions → document_editor.py → Text/Format Modifications → Updated Document
   ```

## Class Hierarchy

```
BaseDocumentEditor
├── TextEditor
└── FormattingEditor

DocumentEditor
├── Uses TextEditor
└── Uses FormattingEditor

LawglanceCLI
├── Uses Lawglance
├── Uses DocumentLoader
├── Uses DocumentEditor
└── Uses DocumentCompare
```

## Extension Points

The LawGlance architecture is designed to be extensible in several ways:

1. **Model Providers** - New language model providers can be added by creating classes that conform to the expected interface in `src/integrations/`

2. **Document Types** - Support for additional document types can be added to `document_loader.py`

3. **Vector Stores** - Alternative vector storage systems can be implemented by swapping out the Chroma DB implementations

4. **UI Layers** - New user interfaces can be created that use the core LawGlance functionality
