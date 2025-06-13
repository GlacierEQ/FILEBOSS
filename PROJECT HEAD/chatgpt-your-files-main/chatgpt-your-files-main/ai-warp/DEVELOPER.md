# Developer Guide

This document provides more detailed information for developers working on the AI-Warp CLI project.

## Architecture Overview

The AI-Warp CLI consists of several components:

1. **CLI Interface** - Built with Commander.js for handling command-line arguments and interactions.
2. **Ollama Integration** - Client for local LLM inference using Ollama API.
3. **Supabase Backend** - Vector database for storing and querying embeddings.
4. **Edge Functions** - Serverless functions for processing and generating embeddings.

## Local Development Setup

### Prerequisites

- Node.js (v18+)
- npm (v9+)
- Docker Desktop
- Ollama (v0.6.8+)
- Git

### Detailed Setup Steps

1. **Clone the repository**

   `ash
   git clone https://github.com/yourusername/ai-warp-cli.git
   cd ai-warp-cli
   `

2. **Install dependencies**

   `ash
   npm install
   `

3. **Start Supabase local development stack**

   First, you need to install the Supabase CLI:

   `ash
   # For npm
   npm install -g supabase
   # OR for Windows with direct installer
   # Visit https://github.com/supabase/cli/releases
   `

   Initialize and start Supabase:

   `ash
   supabase init
   supabase start
   `

   This will:
   - Start PostgreSQL database
   - Start GoTrue auth server
   - Start PostgREST API
   - Start Storage API
   - Start Supabase Studio (web UI)

4. **Configure environment variables**

   Copy the example environment file:

   `ash
   cp .env.example .env
   `

   Update the values in .env with your local Supabase credentials (displayed after running supabase start).

5. **Enable pgvector extension**

   Open the Supabase Studio at http://localhost:54323, navigate to the SQL Editor, and run:

   `sql
   CREATE EXTENSION IF NOT EXISTS vector;
   `

6. **Apply database migrations**

   `ash
   supabase migration up
   `

7. **Build the project**

   `ash
   npm run build
   `

8. **Link the CLI for local development**

   `ash
   npm link
   `

   Now you can run the warp command from anywhere in your terminal.

## Development Workflow

### TypeScript Compilation

The project uses TypeScript for type safety. To compile the TS files:

`ash
npm run build
`

For development with watch mode:

`ash
npm run dev
`

### Testing

The project uses Jest for testing. To run tests:

`ash
npm test
`

For watch mode:

`ash
npm test -- --watch
`

### Linting

To lint the code:

`ash
npm run lint
`

To automatically fix linting issues:

`ash
npm run lint -- --fix
`

## Working with Ollama

### Starting Ollama

Ensure Ollama is running before using the CLI:

`ash
ollama serve
`

### Downloading Models

Download required models for the CLI:

`ash
ollama pull llama2
ollama pull nomic-embed-text
`

## Working with Supabase

### Database Migrations

Create a new migration:

`ash
supabase migration new your_migration_name
`

This creates a new timestamped SQL file in the supabase/migrations directory.

### Edge Functions

Deploy an Edge Function locally:

`ash
supabase functions serve generateEmbedding
`

## Deployment

### Packaging the CLI

To create a distributable package:

`ash
npm pack
`

This creates a tarball that can be installed globally:

`ash
npm install -g ./ai-warp-cli-0.1.0.tgz
`

### CI/CD Pipeline

The project uses GitHub Actions for CI/CD. The workflow is defined in .github/workflows/ci.yml.

## Contributing

1. Fork the repository
2. Create a feature branch: git checkout -b feature/my-feature
3. Commit your changes: git commit -am 'Add some feature'
4. Push to the branch: git push origin feature/my-feature
5. Submit a pull request

## Troubleshooting

### Supabase Issues

If you encounter issues with Supabase:

1. Check Docker is running
2. Restart the Supabase stack: supabase stop && supabase start
3. Check logs: supabase logs

### Ollama Issues

If you encounter issues with Ollama:

1. Ensure Ollama is running: ollama serve
2. Check model availability: ollama list
3. Restart Ollama service
