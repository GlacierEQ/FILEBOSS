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
   