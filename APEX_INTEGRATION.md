# 🚀 FILEBOSS APEX INTEGRATION

## Complete Orchestration Guide

**Context Global:** `LFVBLPUL3N8N8K2FLYGCSCKMSMSRHSG9`  
**Context Direct:** `yD4IKCdlI0VCXlfD4xLT1x5D0dEU9Hd1`

---

## 🎯 Overview

FILEBOSS now features **complete APEX orchestration**, connecting:

### Memory Triad (Triple Memory Architecture)
1. **Memory Plugin MCP** - Session persistence layer
2. **Supermemory AI MCP** - Universal memory with OAuth
3. **Mem0 API** - Graph memory with contradiction detection

### MCP Server Constellation
4. **GitHub MCP** - Access to 538+ repositories
5. **Notion MCP** - Complete documentation workspace
6. **Operator Code MCP** - 4,000+ specialized agent tools

---

## 🛠️ Architecture

```
FILEBOSS v2.0.0-APEX
│
├── 🏛️ CaseBuilder Core
│   ├── FastAPI application
│   ├── SQLAlchemy database
│   ├── Cascade AI integration
│   └── REST API endpoints
│
├── 🧠 Memory Triad
│   ├── Memory Plugin MCP (ws://localhost:8000/memory-plugin-mcp)
│   ├── Supermemory AI MCP (api.supermemory.ai/mcp)
│   └── Mem0 API (api.mem0.ai/v1)
│
├── 🌐 MCP Orchestrator
│   ├── GitHub operations
│   ├── Notion operations
│   └── Operator Code delegation
│
└── 🚀 APEX API Layer
    ├── /apex/health - System health
    ├── /apex/process - File processing
    ├── /apex/search - Intelligent search
    ├── /apex/delegate - Task delegation
    ├── /apex/memory/* - Memory operations
    └── /apex/stats - Integration statistics
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install base requirements
pip install -r requirements.txt
pip install -r requirements-prod.txt

# Install APEX integration dependencies
pip install httpx  # For async HTTP requests
```

### 2. Set Environment Variables

Create `.env` file:

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./fileboss.db

# Memory Systems
MEM0_API_KEY=your_mem0_api_key_here

# MCP Servers
GITHUB_TOKEN=your_github_pat_here
NOTION_TOKEN=your_notion_integration_token_here

# Context IDs (Pre-configured)
CONTEXT_GLOBAL=LFVBLPUL3N8N8K2FLYGCSCKMSMSRHSG9
CONTEXT_DIRECT=yD4IKCdlI0VCXlfD4xLT1x5D0dEU9Hd1
```

### 3. Start MCP Servers

```bash
# Memory Plugin MCP
npx -y @memoryplugin/mcp-server

# Supermemory AI MCP (OAuth)
npx -y install-mcp@latest https://api.supermemory.ai/mcp --client Qwen --oauth=yes
```

### 4. Start FILEBOSS

```bash
# Development mode (with auto-reload)
python main.py

# Production mode
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 📚 API Endpoints

### System Endpoints

#### `GET /health`
Comprehensive health check of all integrated systems.

```json
{
  "status": "ok",
  "version": "2.0.0-APEX",
  "integration": "APEX Quantum Entangled",
  "services": {
    "database": "🟢 OK",
    "cascade_ai": "🟢 OK",
    "apex": {
      "status": "🟢 OK",
      "systems": {
        "memory_plugin": "🟢 OK",
        "supermemory": "🟢 OK",
        "github": "🟢 OK",
        "notion": "🟢 OK",
        "operator_code": "🟡 UNKNOWN"
      }
    }
  }
}
```

### APEX Orchestration Endpoints

#### `GET /apex/health`
APEX-specific health check.

#### `POST /apex/process`
Process a file through the complete APEX pipeline.

```json
{
  "file_path": "/path/to/document.pdf",
  "metadata": {
    "type": "evidence",
    "case": "1FDV-23-0001009"
  },
  "bucket": "fileboss_evidence"
}
```

**Response:**
```json
{
  "status": "success",
  "file": "/path/to/document.pdf",
  "result": {
    "memory_storage": {
      "memory_plugin": {"id": "mem_123"},
      "supermemory": {"id": "super_456"},
      "mem0": {"id": "m0_789"}
    },
    "github_sync": {"status": "success"},
    "notion_index": {"status": "success"}
  }
}
```

#### `POST /apex/search`
Intelligent multi-source search across all integrated systems.

```json
{
  "query": "case evidence filings 2023",
  "limit": 20
}
```

#### `POST /apex/delegate`
Delegate complex tasks to Operator Code MCP.

```json
{
  "task": "Analyze all evidence files for case 1FDV-23-0001009",
  "context": {
    "case_id": "1FDV-23-0001009",
    "document_type": "evidence"
  },
  "priority": "high"
}
```

#### `POST /apex/memory/store`
Store content across Memory Triad.

```json
{
  "content": "Important case note: Judge ruled in favor",
  "bucket": "case_notes",
  "metadata": {
    "case": "1FDV-23-0001009",
    "date": "2025-11-27"
  }
}
```

#### `GET /apex/memory/recall`
Recall memories from all three systems.

```
GET /apex/memory/recall?query=judge ruling&bucket=case_notes&limit=10
```

#### `POST /apex/batch-process`
Batch process multiple files in parallel.

```json
{
  "file_paths": [
    "/evidence/doc1.pdf",
    "/evidence/doc2.pdf",
    "/evidence/doc3.pdf"
  ],
  "parallel": true,
  "bucket": "batch_evidence"
}
```

#### `POST /apex/upload`
Upload and immediately process a file.

```bash
curl -X POST "http://localhost:8000/apex/upload" \
  -F "file=@document.pdf" \
  -F "bucket=uploads"
```

#### `GET /apex/stats`
Get comprehensive APEX integration statistics.

---

## 🧠 Memory Triad Usage

### Python API

```python
from integrations.apex_orchestrator import get_orchestrator

# Initialize
orchestrator = await get_orchestrator()

# Store memory across all three systems
result = await orchestrator.memory_triad.store(
    content="Important information to remember",
    bucket="my_bucket",
    metadata={"source": "manual_entry", "priority": "high"}
)

# Recall from all three systems
results = await orchestrator.memory_triad.recall(
    query="important information",
    bucket="my_bucket",
    limit=10
)

print(f"Found in Memory Plugin: {results['memory_plugin']}")
print(f"Found in Supermemory: {results['supermemory']}")
print(f"Found in Mem0: {results['mem0']}")
```

---

## 🐙 GitHub MCP Integration

```python
# Execute GitHub operations
result = await orchestrator.mcp_orchestrator.github_operation(
    operation="list_repos",
    limit=100
)

if result["status"] == "success":
    repos = result["data"]
    print(f"Found {len(repos)} repositories")
```

---

## 📓 Notion MCP Integration

```python
# Search Notion workspace
result = await orchestrator.mcp_orchestrator.notion_operation(
    operation="search",
    query="FILEBOSS documentation"
)

if result["status"] == "success":
    pages = result["data"]["results"]
    for page in pages:
        print(f"Found: {page['properties']['title']}")
```

---

## 🤖 Operator Code MCP Delegation

```python
# Delegate complex task
result = await orchestrator.operator_delegate(
    task="Process all PDF files in evidence folder",
    context={
        "folder": "/evidence",
        "file_type": "pdf",
        "action": "index_and_analyze"
    }
)

if result["status"] == "success":
    print(f"Task completed: {result['data']}")
```

---

## 🛡️ Security & Configuration

### Required Permissions

**GitHub Token Scopes:**
- `repo` - Repository access
- `read:org` - Organization access
- `read:user` - User profile access

**Notion Integration:**
- Internal integration with read/write permissions
- Access to all relevant databases and pages

**Memory Systems:**
- Mem0 API key from [mem0.ai](https://mem0.ai)
- Supermemory OAuth setup via MCP installer
- Memory Plugin running locally or accessible endpoint

---

## 📊 Monitoring & Observability

### Health Checks

```bash
# Full system health
curl http://localhost:8000/health

# APEX-specific health
curl http://localhost:8000/apex/health

# Integration statistics
curl http://localhost:8000/apex/stats
```

### Logging

Logs are structured and include:
- Timestamp
- Logger name
- Log level
- Message

```python
import logging
logger = logging.getLogger(__name__)
```

---

## 🚀 Production Deployment

### Docker Deployment

```bash
# Build image
docker build -t fileboss-apex:latest .

# Run container
docker run -d \
  --name fileboss \
  -p 8000:8000 \
  --env-file .env \
  fileboss-apex:latest
```

### Environment-Specific Configurations

**Development:**
```bash
export ENVIRONMENT=development
export LOG_LEVEL=DEBUG
export RELOAD=True
```

**Production:**
```bash
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export WORKERS=4
```

---

## 🧑‍💻 Developer Guide

### Adding New Integrations

1. **Create integration module** in `integrations/`
2. **Extend `ApexFileBossOrchestrator`** class
3. **Add API endpoints** in `integrations/apex_api.py`
4. **Update health checks**
5. **Document in this file**

### Testing

```bash
# Run tests
pytest tests/

# Test APEX integration
pytest tests/test_apex_integration.py -v

# Test with coverage
pytest --cov=integrations tests/
```

---

## 📝 Troubleshooting

### Common Issues

**APEX Integration Not Available**
```
WARNING - APEX Integration DISABLED - Install dependencies: pip install httpx
```
**Solution:** `pip install httpx`

**Memory Plugin Connection Failed**
```
Memory Plugin storage failed: Connection refused
```
**Solution:** Start Memory Plugin MCP server: `npx -y @memoryplugin/mcp-server`

**GitHub Token Missing**
```
services: github: ⚠️ No token
```
**Solution:** Set `GITHUB_TOKEN` environment variable

---

## 🌐 Related Documentation

- [Memory Plugin Documentation](https://help.memoryplugin.com)
- [Supermemory AI Docs](https://supermemory.ai)
- [Mem0 API Reference](https://docs.mem0.ai)
- [GitHub MCP Server](https://github.com/modelcontextprotocol/servers)
- [Notion MCP Beta](https://notion.com/mcp)
- [Operator Code MCP](https://operator-code-mcp.vercel.app)

---

## ✨ Features

- ✅ **Memory Triad** - Triple redundancy across 3 memory systems
- ✅ **Intelligent Search** - Multi-source unified search
- ✅ **Task Delegation** - Leverage 4,000+ Operator Code tools
- ✅ **Batch Processing** - Parallel file processing
- ✅ **Real-time Health** - Comprehensive system monitoring
- ✅ **Context Preservation** - Global and direct context IDs
- ✅ **96.9% Token Reduction** - Memory-first architecture
- ✅ **Production Ready** - Docker, logging, error handling

---

**Built with ❤️ by GlacierEQ**  
**Context Global:** LFVBLPUL3N8N8K2FLYGCSCKMSMSRHSG9  
**APEX Quantum Entangled Architecture**
