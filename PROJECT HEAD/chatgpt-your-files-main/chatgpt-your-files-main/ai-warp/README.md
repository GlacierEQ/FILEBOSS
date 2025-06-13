# AI-Warp CLI

An AI-powered Warp CLI that uses Ollama for local LLM inference and PostgreSQL with pgvector for storage, with all processing done on your local machine.

## Features

- 🤖 Local LLM inference using Ollama (no cloud API calls)
- 🔍 Web content fetching and summarization
- 📁 Directory scanning and file indexing
- 🗄️ Vector database for semantic search using PostgreSQL with pgvector
- 🔒 Complete privacy - all processing happens on your PC

## System Requirements

- Node.js (v16+)
- Docker and Docker Compose
- Ollama (v0.6.8+)
- 16GB RAM recommended for running models locally

## Quick Start

1. Clone the repository:
   `ash
   git clone https://github.com/yourusername/ai-warp-cli.git
   cd ai-warp-cli
   `

2. Install dependencies:
   `ash
   npm install
   `

3. Start the local services with Docker:
   `ash
   npm run docker:up
   `

4. Start using the CLI:
   `ash
   # Summarize a web page
   npm run start -- agent:fetch -u https://example.com
   
   # Scan a directory and index files
   npm run start -- agent:scan -d ./your-directory
   
   # Search for similar content
   npm run start -- search -q "your search query"
   `

## Complete Local Setup

### Required Models

Make sure Ollama is installed and the following models are available:

`ash
# Download text generation model
ollama pull llama2

# Download embedding model
ollama pull nomic-embed-text
`

### Starting Services

Start all required services:

`ash
# Start PostgreSQL and Ollama in Docker
npm run docker:up

# Start the API server
npm run start:api
`

### Building and Installing the CLI

Build and link the CLI for global use:

`ash
npm run build
npm link  # May require administrator privileges
`

Now you can use the warp command directly:

`ash
# Show help
warp --help

# Check system diagnostics
warp diagnose

# Fetch and summarize content from a URL
warp agent:fetch -u https://example.com

# Scan and index a directory
warp agent:scan -d ~/Documents

# Search for similar content
warp search -q "your search query"
`

## Docker Management

The CLI provides commands to manage Docker containers:

`ash
# Start Docker containers
warp docker start

# Check Docker container status
warp docker status

# Stop Docker containers
warp docker stop
`

## Security & Privacy

This implementation:
- Processes all data locally on your machine
- Makes no external API calls (except to fetch web content when requested)
- Stores data only in your local PostgreSQL database
- Has no telemetry or analytics

## Architecture

- **Ollama**: Local LLM runner for text generation and embeddings
- **PostgreSQL**: Database with pgvector extension for vector storage and search
- **Express API**: Local API server for handling requests
- **CLI**: Command-line interface for interacting with the system

## Troubleshooting

- **Docker Issues**: Ensure Docker is running and ports 5432 (PostgreSQL) and 11434 (Ollama) are available
- **API Server**: Check that the API server is running with curl http://localhost:3000/api/health
- **Ollama**: Verify Ollama is running with ollama list

## License

MIT
