# OpenDevin Enhanced Environment Setup Guide

This guide will help you set up all required credentials and configuration files for the OpenDevin Enhanced project with Supabase and Ollama integrations.

## 📋 Prerequisites

- Windows 10/11 with PowerShell 5.1+ or PowerShell Core 7+
- Git for version control
- Python 3.8+ (for OpenDevin core)
- Node.js 16+ (for frontend)
- Docker (recommended for sandbox environments)

## 🚀 Quick Setup

Run the automated setup script:

```powershell
.\setup-environment.ps1
```

This script will:
- ✅ Create `.env` file from template
- ✅ Check Ollama installation and status
- ✅ Help configure Supabase credentials
- ✅ Set up OpenAI API key (optional)
- ✅ Verify configuration

## 🔧 Manual Setup

If you prefer to set up manually or need to troubleshoot:

### 1. Environment Variables

1. Copy the example environment file:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Edit `.env` file with your actual values:
   ```bash
   # Core OpenDevin Configuration
   LLM_API_KEY=your-openai-api-key-here
   LLM_BASE_URL=http://localhost:11434
   LLM_MODEL=ollama/codellama:7b-instruct
   
   # Supabase Configuration
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_ANON_KEY=your-supabase-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
   ```

### 2. Ollama Setup

1. **Install Ollama:**
   - Download from [https://ollama.ai](https://ollama.ai)
   - Install and ensure it's in your PATH

2. **Start Ollama service:**
   ```powershell
   ollama serve
   ```

3. **Install recommended models:**
   ```powershell
   ollama pull codellama:7b-instruct
   ollama pull llama2:7b-chat
   ollama pull mistral:7b-instruct
   ollama pull deepseek-coder:6.7b-instruct
   ```

4. **Verify installation:**
   ```powershell
   ollama list
   curl http://localhost:11434/api/tags
   ```

### 3. Supabase Setup

1. **Create Supabase Project:**
   - Go to [https://app.supabase.com](https://app.supabase.com)
   - Create a new account or sign in
   - Create a new project
   - Wait for the project to be ready

2. **Get Credentials:**
   - Go to Settings → API
   - Copy the Project URL
   - Copy the `anon` public key
   - Copy the `service_role` secret key

3. **Set up Database Schema:**
   - Go to SQL Editor in your Supabase dashboard
   - Copy the contents of `supabase-schema.sql`
   - Paste and run it in the SQL editor

4. **Configure Authentication (Optional):**
   - Go to Authentication → Settings
   - Configure your preferred auth providers
   - Set up email templates if needed

### 4. Configuration Files

The project uses several configuration files:

#### `warp.toml`
Already configured with:
- ✅ Supabase integration settings
- ✅ Ollama model preferences
- ✅ Security configurations
- ✅ Feature flags
- ✅ Development settings

#### `.env`
Contains sensitive credentials:
- 🔐 API keys and secrets
- 🔐 Database connection strings
- 🔐 Service URLs

## 🔒 Security Best Practices

### Environment Variables
- ✅ `.env` file is in `.gitignore` (never commit secrets)
- ✅ Use different credentials for development/production
- ✅ Rotate keys regularly
- ✅ Use least-privilege access for service accounts

### Supabase Security
- ✅ Row Level Security (RLS) is enabled
- ✅ Proper access policies are configured
- ✅ Service role key should only be used server-side
- ✅ Anon key is safe for client-side use

### Ollama Security
- ✅ Default setup runs on localhost only
- ✅ Consider network restrictions for production
- ✅ Monitor resource usage

## 📁 File Structure

```
opendevin-enhanced/
├── warp.toml              # Main project configuration
├── .env.example          # Environment variables template
├── .env                  # Your actual environment variables (git-ignored)
├── supabase-schema.sql   # Database schema for Supabase
├── setup-environment.ps1 # Automated setup script
├── ENVIRONMENT_SETUP.md  # This guide
└── workspace/            # Your project workspace
```

## 🛠 Troubleshooting

### Ollama Issues

**"ollama: command not found"**
- Ensure Ollama is installed and in your PATH
- Restart your terminal after installation
- Try the full path: `C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama.exe`

**"Connection refused to localhost:11434"**
- Start Ollama service: `ollama serve`
- Check if port 11434 is available
- Verify firewall settings

**Models download slowly**
- Check your internet connection
- Models are large (4-7GB each)
- Consider downloading one model at a time

### Supabase Issues

**"Invalid JWT"**
- Check your API keys are correct
- Ensure you're using the right key for the right environment
- Verify project URL format: `https://xxxxx.supabase.co`

**"Permission denied"**
- Check Row Level Security policies
- Verify user authentication status
- Ensure proper table permissions

**Schema errors**
- Run the schema setup SQL in the correct order
- Check for existing table conflicts
- Verify extensions are enabled

### General Issues

**"Module not found"**
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version compatibility
- Verify virtual environment is activated

**Configuration not loading**
- Check `.env` file format (no spaces around `=`)
- Verify file encoding (UTF-8)
- Ensure environment variables are exported properly

## 🚀 Next Steps

Once environment setup is complete:

1. **Start the application:**
   ```powershell
   .\start-enhanced.ps1
   ```

2. **Access the interface:**
   - Web UI: http://localhost:3000
   - API: http://localhost:8000

3. **Test integrations:**
   - Try a simple coding task
   - Verify Supabase data persistence
   - Check Ollama model responses

## 📞 Support

If you encounter issues:

1. Check this troubleshooting guide
2. Review logs in the console output
3. Verify all prerequisites are installed
4. Check the main README.md for additional information

## 🔄 Updating Configuration

To update your configuration:

1. **Environment variables:** Edit `.env` file
2. **Project settings:** Edit `warp.toml`
3. **Database schema:** Run update scripts in Supabase SQL editor
4. **Restart services:** Re-run setup scripts if needed

Remember to backup your configuration before making changes!

