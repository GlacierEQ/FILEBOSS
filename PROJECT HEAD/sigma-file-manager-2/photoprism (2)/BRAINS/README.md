# LlamaFS

<img src="electron-react-app/assets/llama_fs.png" width="30%" />

## Inspiration

[Watch the explainer video](https://x.com/AlexReibman/status/1789895425828204553)

Open your `~/Downloads` directory. Or your Desktop. It's probably a mess...

> There are only two hard things in Computer Science: cache invalidation and **naming things**.

## What it does

LlamaFS is a self-organizing file manager. It automatically renames and organizes your files based on their content and well-known conventions (e.g., time). It supports many kinds of files, including images (through Moondream) and audio (through Whisper).

LlamaFS runs in two "modes" - as a batch job (batch mode), and an interactive daemon (watch mode).

In batch mode, you can send a directory to LlamaFS, and it will return a suggested file structure and organize your files.

In watch mode, LlamaFS starts a daemon that watches your directory. It intercepts all filesystem operations and uses your most recent edits to proactively learn how you rename file. For example, if you create a folder for your 2023 tax documents, and start moving 1-3 files in it, LlamaFS will automatically create and move the files for you!

Uh... Sending all my personal files to an API provider?! No thank you!

It also has a toggle for "incognito mode," allowing you route every request through Ollama instead of Groq. Since they use the same Llama 3 model, the perform identically.

## How we built it

We built LlamaFS on a Python backend, leveraging the Llama3 model through Groq for file content summarization and tree structuring. For local processing, we integrated Ollama running the same model to ensure privacy in incognito mode. The frontend is crafted with Electron, providing a sleek, user-friendly interface that allows users to interact with the suggested file structures before finalizing changes.

- **It's extremely fast!** (by LLM standards)! Most file operations are processed in <500ms in watch mode (benchmarked by [AgentOps](https://agentops.ai/?utm_source=llama-fs)). This is because of our smart caching that selectively rewrites sections of the index based on the minimum necessary filesystem diff. And of course, Groq's super fast inference API. 😉

- **It's immediately useful** - It's very low friction to use and addresses a problem almost everyone has. We started using it ourselves on this project (very Meta).

## What's next for LlamaFS

- Find and remove old/unused files
- We have some really cool ideas for - filesystem diffs are hard...

## Installation

### Prerequisites

Before installing, ensure you have the following requirements:
- Python 3.10 or higher
- pip (Python package installer)

### Installing

To install the project, follow these steps:
1. Clone the repository:
   ```bash
   git clone https://github.com/iyaja/llama-fs.git
   ```

2. Navigate to the project directory:
    ```bash
    cd llama-fs
    ```

3. Install requirements
   ```bash
   pip install -r requirements.txt
   ```

4. Update your `.env`
Copy `.env.example` into a new file called `.env`. Then, provide the following API keys:
* Groq: You can obtain one from [here](https://console.groq.com/keys).
* AgentOps: You can obtain one from [here](https://app.agentops.ai/settings/projects).

Groq is used for fast cloud inference but can be replaced with Ollama in the code directly (TODO.)

AgentOps is used for logging and monitoring and will report the latency, cost per session, and give you a full session replay of each LlamaFS call.

5. (Optional) Install moondream if you want to use the incognito mode
    ```bash
    ollama pull moondream
    ```

## Usage

To serve the application locally using FastAPI, run the following command
   ```bash
   fastapi dev server.py
   ```

This will run the server by default on port 8000. The API can be queried using a `curl` command, and passing in the file path as the argument. For example, on the Downloads folder:
   ```bash
   curl -X POST http://127.0.0.1:8000/batch \
    -H "Content-Type: application/json" \
    -d '{"path": "/Users/<username>/Downloads/", "instruction": "string", "incognito": false}'
   ```

# Sorting Hat Documentation

## System Organization

The Sorting Hat system is designed to automatically organize files while maintaining system stability by:

1. **Ignoring System Folders**: Special Windows folders that could cause permission errors or contain system files are automatically excluded from monitoring.

2. **Centralized Program Files**: All Sorting Hat components are kept together in the BRAINS directory for easier maintenance and updates.

## Key Components

- **file_organizer.js**: The core file monitoring and sorting engine
- **service.js**: API server for the dashboard and status reporting
- **dashboard_controller.js**: Manages the UI interactions and data flow
- **api_service.js**: Handles API requests with caching and offline capabilities

## Best Practices

### System File Handling

- System folders like "My Music", "My Videos", etc. are ignored to prevent permission errors
- Temporary files (starting with ~$ or ending with .tmp) are skipped
- Hidden files (starting with .) are not processed

### Organization Structure

```
C:/SORTING HAT/
├── BRAINS/           # Program files and configuration
│   ├── cache/        # Cached API responses
│   ├── config.js     # System configuration
│   ├── public/       # Dashboard web interface
│   └── logs/         # System logs
└── rules/            # Custom sorting rules (optional)

C:/Users/casey/OrganizeFolder/   # Organized file destination
├── Legal/
├── Financial/
├── Real Estate/
└── ...
```

## Future Improvements

1. **Deep Directory Scanning**: Add capability to scan nested folders (currently limited to depth=1)

2. **Content Analysis**: Implement better text extraction from documents using specialized libraries:
   - PDF text extraction with pdf-parse
   - Office documents with textract
   - Image text recognition with Tesseract

3. **AI Enhancement**: Train a machine learning model on previously sorted files to improve categorization

4. **Custom Rule Editor**: Create a UI for editing sorting rules and patterns

5. **Statistics Dashboard**: Add visual reports of sorting efficiency and disk space usage

## Maintenance

- Run `sorting_status.js` weekly to verify system health
- Use `permission_fix.bat` if permission errors occur in logs
- Keep all program files in the BRAINS directory for easier updates
