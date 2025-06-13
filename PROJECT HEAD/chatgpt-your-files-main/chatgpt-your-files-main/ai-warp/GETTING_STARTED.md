# Getting Started: Local AI Processing

This guide will help you quickly set up and use the AI-Warp CLI with all processing done locally on your PC.

## 1. Prerequisites

Make sure you have:
- Docker and Docker Compose installed
- Ollama installed (v0.6.8+)
- Node.js (v16+) and npm

## 2. One-Command Setup

The fastest way to get everything running:

`ash
# Install dependencies and start services
npm install && npm run local:start
`

This will:
1. Install all Node.js dependencies
2. Start PostgreSQL in Docker
3. Start Ollama in Docker (if you prefer using your locally installed Ollama, edit the .env file)
4. Start the API server

## 3. Verify Installation

Check if everything is working:

`ash
# Run the diagnostic command
npm start -- diagnose
`

You should see information about your system, Ollama, Docker containers, and PostgreSQL connection.

## 4. Download Required Models

If not already available, download the required Ollama models:

`ash
# Download text generation model
ollama pull llama2

# Download embedding model  
ollama pull nomic-embed-text
`

## 5. Try It Out

### Summarize a web page:

`ash
npm start -- agent:fetch -u https://news.ycombinator.com
`

### Index your documents:

`ash
npm start -- agent:scan -d ./your-documents-folder
`

### Search for similar content:

`ash
npm start -- search -q "Your search query"
`

## 6. Build and Install CLI Globally (Optional)

For easier usage, build the CLI and install it globally:

`ash
# Build the project
npm run build

# Link globally (may require administrator privileges)
npm link
`

Now you can use warp from anywhere:

`ash
warp --help
warp diagnose
warp agent:fetch -u https://example.com
`

## 7. Stopping Services

When you're done, stop the services:

`ash
# Stop all Docker containers
npm run local:stop
`

## 8. Privacy and Security

All processing happens on your local machine:
- Ollama runs locally for LLM inference
- PostgreSQL stores data locally
- No data is sent to external APIs (except when fetching web content)
- No usage tracking or telemetry

## 9. What's Next?

- Explore the README.md for more advanced usage
- Check SELF_HOSTING_GUIDE.md for detailed architecture information
- Customize models by editing the .env file
