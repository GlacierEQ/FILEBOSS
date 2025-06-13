# Enhanced OpenDevin Installation 🚀

## Overview

This is a **heightened installation** of OpenDevin that utilizes "the best of all worlds" by integrating:

- 🤖 **Ollama** for local LLM inference (privacy + speed)
- 🗄️ **Supabase** for enhanced data storage and real-time capabilities
- ⚡ **Redis** for caching and session management
- 🐳 **Docker** containerization for easy deployment
- 🎯 **Hybrid LLM routing** (local + cloud fallback)

## Features

### 🌟 Enhanced Capabilities
- **Local AI Models**: Run CodeLlama, Llama2, Mistral, and DeepSeek locally
- **Persistent Storage**: Store conversations and projects in Supabase
- **Real-time Collaboration**: Share sessions with team members
- **Hybrid Intelligence**: Fallback to cloud LLMs when needed
- **Advanced Code Analysis**: Enhanced code understanding and generation
- **Automated Testing**: Built-in test generation and execution

### 🔧 Technical Stack
- **Frontend**: React-based UI with real-time updates
- **Backend**: FastAPI with WebSocket support
- **AI**: Ollama + LiteLLM for model routing
- **Database**: Supabase (PostgreSQL + real-time)
- **Cache**: Redis for session management
- **Container**: Docker Compose orchestration

## Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- Python 3.11+
- 8GB+ RAM (for AI models)
- 20GB+ storage (for models)

### 2. Setup

```powershell
# Clone or navigate to your OpenDevin directory
cd "C:\Users\casey\Downloads\OpenDevin.OpenDevin-main"

# Run enhanced setup
.\start-enhanced.ps1 -Mode setup
```

### 3. Configure Environment

Edit the `.env` file with your Supabase credentials:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

### 4. Start Services

```powershell
# Start all services
.\start-enhanced.ps1 -Mode start

# Check status
.\start-enhanced.ps1 -Mode status

# View logs
.\start-enhanced.ps1 -Mode logs
```

## Configuration

### warp.toml

The `warp.toml` file contains all configuration for your enhanced installation:

```toml
[integrations.ollama]
enabled = true
base_url = "http://localhost:11434"
models = [
    "codellama:7b-instruct",
    "llama2:7b-chat",
    "mistral:7b-instruct",
    "deepseek-coder:6.7b-instruct"
]

[integrations.supabase]
enabled = true
project_url = "${SUPABASE_URL}"
auth = true
realtime = true
storage = true

[features]
hybrid_llm = true
persistent_storage = true
realtime_collaboration = true
code_analysis = true
automated_testing = true
```

## Usage

### 🎯 Access Points

- **OpenDevin UI**: http://localhost:3000
- **Ollama API**: http://localhost:11434
- **Redis**: localhost:6379

### 🤖 Available Models

1. **CodeLlama 7B**: Specialized for code generation
2. **Llama2 7B Chat**: General conversation
3. **Mistral 7B**: Instruction following
4. **DeepSeek Coder**: Advanced coding tasks

### 💡 Enhanced Features

#### Hybrid LLM Routing
- Automatically routes requests to best available model
- Falls back to cloud LLMs if local models are busy
- Optimizes for cost and performance

#### Persistent Storage
- All conversations saved to Supabase
- Project history and context preservation
- Cross-session continuity

#### Real-time Collaboration
- Share coding sessions with team members
- Live cursor and code updates
- Collaborative debugging

## Management Commands

```powershell
# Setup and configure
.\start-enhanced.ps1 -Mode setup

# Start all services
.\start-enhanced.ps1 -Mode start

# Stop all services
.\start-enhanced.ps1 -Mode stop

# Check service status
.\start-enhanced.ps1 -Mode status

# View service logs
.\start-enhanced.ps1 -Mode logs
```

## Troubleshooting

### Common Issues

#### 1. Ollama Models Not Loading
```powershell
# Check Ollama status
docker-compose -f docker-compose.enhanced.yml logs ollama

# Manually pull models
docker-compose -f docker-compose.enhanced.yml exec ollama ollama pull codellama:7b-instruct
```

#### 2. Supabase Connection Issues
- Verify your `.env` file has correct Supabase credentials
- Check Supabase project settings for API keys
- Ensure your IP is whitelisted in Supabase

#### 3. Memory Issues
```powershell
# Check Docker resource usage
docker stats

# Adjust model size in warp.toml if needed
# Use smaller models like codellama:3b-instruct
```

### 4. Port Conflicts
```powershell
# Check if ports are in use
netstat -an | findstr :3000
netstat -an | findstr :11434

# Modify ports in docker-compose.enhanced.yml if needed
```

## Performance Optimization

### Hardware Recommendations

- **CPU**: 8+ cores for optimal performance
- **RAM**: 16GB+ (8GB minimum)
- **GPU**: NVIDIA GPU for faster inference (optional)
- **Storage**: SSD recommended for model loading

### Model Selection

- **Light Usage**: Use 3B parameter models
- **Balanced**: Use 7B parameter models (default)
- **Heavy Usage**: Use 13B+ parameter models

## Security

### Sandboxing
- All code execution is sandboxed in Docker containers
- File system access is restricted to workspace directory
- Network access is controlled and monitored

### Data Privacy
- Local AI models ensure code privacy
- Supabase data is encrypted in transit and at rest
- No data sent to external AI providers by default

## Contributing

This enhanced installation builds upon the original OpenDevin project. To contribute:

1. Follow the original [OpenDevin contributing guidelines](./CONTRIBUTING.md)
2. Test your changes with the enhanced configuration
3. Update the `warp.toml` configuration as needed

## License

Same as the original OpenDevin project - MIT License.

## Support

For issues specific to this enhanced installation:
1. Check the troubleshooting section above
2. Review the logs: `./start-enhanced.ps1 -Mode logs`
3. Create an issue with the "enhanced" label

For general OpenDevin issues, refer to the main project documentation.

---

🎉 **Enjoy your heightened OpenDevin experience!** 🚀

