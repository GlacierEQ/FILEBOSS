# LawGlance Architecture Overview

This document provides a high-level overview of the LawGlance project architecture, explaining how different components interact and their responsibilities.

## Core Components

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Streamlit UI   │────▶│   LawGlance     │────▶│   Language      │
│    (app.py)     │     │     Core        │     │     Model       │
│                 │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │                 │
                        │  Vector Store   │
                        │                 │
                        └─────────────────┘
```

### Component Responsibilities

1. **Streamlit UI (app.py)**
   - Provides user interface for interacting with the system
   - Handles user input/output
   - Manages chat history and session state

2. **LawGlance Core (src/lawglance_main.py)**
   - Central orchestration component
   - Processes queries
   - Retrieves relevant context from vector store
   - Formats prompts for language model
   - Manages conversation history

3. **Language Model**
   - Provides natural language understanding and generation
   - Can be either OpenAI models or Hugging Face models

4. **Vector Store**
   - Stores document embeddings
   - Handles similarity-based retrieval
   - Maintains indexed legal knowledge

## Utility Modules

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│                            Utilities                                │
│                                                                     │
├─────────────────┬─────────────────┬─────────────────┬──────────────┤
│                 │                 │                 │              │
│ Document Loader │ Document Editor │ Document Compare│ HuggingFace  │
│                 │                 │                 │    Setup     │
└─────────────────┴─────────────────┴─────────────────┴──────────────┘
```

### Utility Responsibilities

1. **Document Loader (src/document_loader.py)**
   - Loads legal documents from various formats
   - Splits documents into chunks
   - Adds documents to vector store

2. **Document Editor (src/utils/document_editor.py)**
   - Edits documents using natural language instructions
   - Handles text operations, formatting, and structure changes
   - Preserves document formatting

3. **Document Compare (src/utils/document_compare.py)**
   - Compares two documents for differences
   - Analyzes structural and content changes
   - Provides human-readable summaries

4. **HuggingFace Setup (src/utils/huggingface_setup.py)**
   - Configures access to HuggingFace models
   - Verifies API tokens
   - Sets up environment

## Integration Modules

```
┌─────────────────────────────────────────────────┐
│                                                 │
│                   Integrations                  │
│                                                 │
├─────────────────────────┬─────────────────────┤
│                         │                     │
│ HuggingFace Integration │ Other Integrations  │
│                         │                     │
└─────────────────────────┴─────────────────────┘
```

### Integration Responsibilities

1. **HuggingFace Integration (src/integrations/simple_lawglance_hf.py)**
   - Provides open-source model alternatives
   - Connects to HuggingFace endpoints
   - Configures model parameters

## Data Flow

1. User submits legal query through Streamlit UI
2. Query is passed to LawGlance core
3. LawGlance retrieves relevant documents from vector store
4. Retrieved context and query are formatted into a prompt
5. Prompt is sent to language model
6. Language model generates a response
7. Response is returned to user via UI

## Extension Points

- **New Model Integrations**: Add new model providers by creating new modules in `src/integrations/`
- **Document Processors**: Extend document handling by enhancing `src/document_loader.py`
- **UI Enhancements**: Modify `app.py` to add new UI features
- **Vector Store Providers**: Change the vector database by modifying the initialization in `app.py` and `src/main.py`
