# Lawglance System Improvements Migration Guide

This guide explains how to integrate the performance, caching, and configuration improvements into your Lawglance system.

## 1. File Overview

The following new files have been added to improve the system:

- **config.py** - Configuration management
- **document_cache.py** - Document content and analysis caching
- **document_processor.py** - Enhanced document processing with chunking
- **performance_utils.py** - Performance monitoring utilities
- **lawglance_integration.py** - Integration with existing Lawglance system
- **enhanced_runner.py** - Main runner script for the enhanced system
- **lawglance_config.json** - Configuration settings

## 2. Installation Steps

1. Copy all new files to your Lawglance project directory
2. Install additional dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Modify your `lawglance_config.json` file with your specific settings

## 3. Integration Steps

### Option 1: Use Enhanced Runner (Recommended)

The simplest approach is to use the provided enhanced runner:

```python
from enhanced_runner import setup_lawglance, run_interactive_mode

# Run the interactive session
run_interactive_mode()

# Or initialize and use programmatically
lawglance = setup_lawglance()
response = lawglance.conversational("What is a legal contract?")
```

### Option 2: Manual Integration

If you need more control, you can integrate the components manually:

```python
from config import Config
from lawglance_integration import LawglanceIntegration
from lawglance_main import Lawglance

# Initialize your Lawglance instance as usual
lawglance = Lawglance(llm, embeddings, vector_store)

# Enhance with improved components
integration = LawglanceIntegration("lawglance_config.json")
lawglance = integration.setup_lawglance(lawglance)

# Use as normal
response = lawglance.conversational("Your query")
```

## 4. Key Improvements

### Performance Optimization

- **Overlapping Chunks**: Document chunks now overlap to avoid losing context at boundaries
- **Performance Monitoring**: The `timing` decorator tracks function performance
- **Caching**: Document content and analyses are cached for improved performance

### Dependency Management

- **Pinned Dependencies**: The `requirements.txt` file specifies exact versions
- **Fallback Strategies**: Components gracefully degrade when optional dependencies are missing

### Configuration Management

- **Central Config**: All settings now come from a central config file
- **Dynamic Configuration**: Update settings without code changes
- **Environment Integration**: Settings can be overridden by environment variables

### Testing Infrastructure

- **Unit Tests**: Tests for document processing and caching components
- **Integration Tests**: Tests for the full system

## 5. Performance Monitoring

You can monitor system performance with:

```python
from performance_utils import performance_monitor

# Print performance report
performance_monitor.print_report()
```

## 6. Migrating from Old Implementation

If you're currently using Lawglance directly, you can gradually migrate:

1. Start using the configuration system:
   ```python
   from config import Config
   config = Config()
   # Access settings with config.get("section", "key")
   ```

2. Add document caching:
   ```python
   from document_cache import DocumentCache
   cache = DocumentCache(config)
   ```

3. Enhance document processing:
   ```python
   from document_processor import DocumentProcessor
   doc_processor = DocumentProcessor(config, word_processor, doc_analyzer, concept_extractor, cache)
   ```

## 7. Troubleshooting

- Check the log file specified in your config for detailed error information
- Run tests to verify system components: `python -m unittest discover tests`
- Ensure API keys are correctly set in your configuration file

For detailed documentation of each component, please refer to the docstrings in the individual files.
