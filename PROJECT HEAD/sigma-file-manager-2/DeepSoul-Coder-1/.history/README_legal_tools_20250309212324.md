# Legal Data Processing Tools

This directory contains a comprehensive set of tools for legal data acquisition, processing, and analysis. These tools enable you to scrape court websites, process legal documents, extract citations, and perform sophisticated analysis of legal text.

## Components

### 1. Legal Scraping Module
- `legal_scraping.py` - Handles scraping of legal websites with advanced capabilities for handling login forms and CAPTCHA
- Supports multiple scraping methods: Playwright, Selenium, and direct API access

### 2. Legal Data Pipeline
- `legal_data_pipeline.py` - End-to-end pipeline for processing legal data
- Extracts structured information from legal documents, including case information and citations
- Supports storage in Elasticsearch for advanced search capabilities
- Enables export to CSV for further analysis

### 3. Legal Assistant
- `deepsoul_legal_integration.py` - Integrates legal data capabilities with the DeepSoul AI system
- Provides research capabilities, document generation, and legal text analysis

### 4. Command-Line Interface
- `legal_data_cli.py` - Command-line interface for accessing legal data tools
- Supports all major functionality through a user-friendly CLI

## Quick Start

### Setting Up

1. Install required dependencies:
   ```
   pip install -r requirements.txt
   pip install playwright selenium undetected-chromedriver beautifulsoup4 pandas elasticsearch
   playwright install
   ```

2. Set up your environment (optional):
   - Elasticsearch for document storage and search
   - API keys for legal data services (CourtListener, Justia, etc.)

### Memory Management

The legal tools include built-in memory protection to prevent Out-of-Memory (OOM) errors:

- Automatic memory monitoring with configurable thresholds
- Smart resource allocation during large document processing
- Graceful degradation when system resources are constrained
- Detailed memory usage logs for troubleshooting

To configure memory protection settings, modify the `legal_memory_config.json` file.

### Example Usage

#### Scraping Court Documents

```bash
# Scrape a single URL
python legal_data_cli.py scrape https://www.courtlistener.com/opinion/4801970/oracle-america-inc-v-google-llc/

# Scrape multiple URLs from a file
python legal_data_cli.py scrape urls.txt --method playwright --csv
```

#### Searching for Legal Cases

```bash
# Search for cases related to a topic
python legal_data_cli.py search "fair use copyright" --limit 5 --save
```

#### Analyzing Legal Documents

```bash
# Analyze a legal document to extract key information
python legal_data_cli.py analyze legal_brief.txt --save
```

#### Extracting Citations

```bash
# Extract citations from a document and look up details
python legal_data_cli.py extract legal_brief.txt --lookup --save
```

#### Running the Full Pipeline

```bash
# Process multiple URLs with the complete pipeline
python legal_data_cli.py pipeline urls.txt --method playwright --csv --analyze
```

## Integration with DeepSoul

The legal tools integrate seamlessly with the DeepSoul AI system, enabling advanced legal research and document generation:

```python
from implementation.deepsoul_legal_integration import LegalAssistant

# Create a legal assistant with your AI model
legal_assistant = LegalAssistant(model=your_model, tokenizer=your_tokenizer)

# Research a legal topic
results = legal_assistant.research_legal_topic("fair use copyright", depth=2)

# Generate a legal document
brief = legal_assistant.generate_legal_document("brief", {
    "title": "Fair Use Analysis",
    "issue": "Whether the use of copyrighted material for educational purposes constitutes fair use",
    "court": "U.S. District Court for the Southern District of New York"
})
```

## OOM Protection

The system includes comprehensive OOM (Out of Memory) protection to prevent crashes during resource-intensive operations:

- Dynamic scaling of batch sizes based on available memory
- Automatic offloading of data to disk when memory pressure is high
- Graceful fallback options when resources are constrained
- Detailed memory monitoring and warning system

## Contributing

Contributions to these legal tools are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Make your changes with appropriate tests
4. Submit a pull request

## License

These legal tools are released under the MIT License.
