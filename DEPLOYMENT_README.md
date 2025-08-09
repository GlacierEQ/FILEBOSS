# SIGMA FILEBOSS - Deployment Guide

## 🚀 Unified File Management & AI Processing Suite

SIGMA FILEBOSS is a comprehensive tabbed GUI application that integrates all FILEBOSS components into a unified interface. It combines case management, file organization, audio transcription, document processing, and AI analysis in one powerful application.

## 📋 System Requirements

### Minimum Requirements

- **OS**: Windows 10+, macOS 10.15+, or Ubuntu 18.04+
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 2GB free space for application and dependencies
- **Display**: 1280x720 minimum resolution (1600x900+ recommended)

### Recommended Specifications

- **RAM**: 16GB+ for AI processing
- **GPU**: CUDA-compatible GPU for faster AI inference
- **Storage**: SSD for better performance

## 🛠️ Installation

### Quick Start (Windows)

1. Clone or download the repository
2. Double-click `Start_SIGMA_FILEBOSS.bat`
3. The script will automatically install dependencies and launch the application

### Quick Start (Linux/macOS)

1. Clone or download the repository
2. Run `./start_sigma_fileboss.sh`
3. The script will automatically install dependencies and launch the application

### Manual Installation

1. **Install Python 3.8+** if not already installed
2. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd FILEBOSS
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements_sigma.txt
   ```

4. **Launch the application**:
   ```bash
   python launch_sigma_fileboss.py
   ```

## 🎯 Application Features

### Tab Overview

The application features 8 specialized tabs, each focusing on specific functionality:

1. **📁 Case Builder** - Main file management and case organization
2. **📝 Document Generator** - Legal document creation and templates
3. **🎤 WhisperX Audio** - Audio transcription and processing
4. **🗂️ File Organizer** - Intelligent file organization with AI
5. **📸 PhotoPrism** - Photo management and organization
6. **⚖️ Legal Brain** - Advanced legal document processing
7. **🧠 AI Analysis** - Intelligent document and content analysis
8. **📊 System Monitor** - Performance and health monitoring

### Key Capabilities

#### Case Builder Tab

- **Case Management**: Create, organize, and manage legal cases
- **File Import**: Drag-and-drop file import with automatic categorization
- **Watch Folders**: Automatic monitoring of directories for new files
- **Database Integration**: SQLAlchemy-based case and file tracking
- **Cross-tab Communication**: Shares data with other tabs

#### WhisperX Audio Tab

- **Audio Transcription**: High-quality speech-to-text conversion
- **Multiple Formats**: Support for MP3, WAV, M4A, FLAC, OGG, AAC
- **Audio Playback**: Built-in media player with volume control
- **Language Detection**: Auto-detect or manually specify language
- **Export Options**: Save transcriptions in various formats
- **History Tracking**: Keep track of all transcription sessions

#### File Organizer Tab

- **Smart Organization**: AI-powered file categorization
- **Multiple Modes**: Organize by type, date, or content
- **Legal Document Detection**: Automatic identification of legal files
- **Batch Processing**: Handle large directories efficiently
- **Preview Mode**: See organization structure before execution
- **Drag-and-Drop**: Easy directory selection

#### Integration Features

- **Cross-tab Data Sharing**: Seamless data flow between components
- **Unified Theming**: Modern dark theme across all tabs
- **Session Management**: Save and restore work sessions
- **Progress Tracking**: Real-time progress indicators
- **Error Handling**: Graceful error recovery and reporting

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root to customize settings:

```env
# Database Configuration
DATABASE_URL=sqlite:///data/sigma_fileboss.db

# WhisperX Configuration
WHISPER_API_URL=http://localhost:9000/asr

# PhotoPrism Configuration
PHOTOPRISM_API_URL=http://localhost:2342/api/v1
PHOTOPRISM_ADMIN_USER=admin
PHOTOPRISM_ADMIN_PASSWORD=your_password

# AI Model Configuration
USE_GPU=true
MODEL_CACHE_DIR=./models

# Logging Configuration
LOG_LEVEL=INFO
```

### Command Line Options

```bash
python launch_sigma_fileboss.py --help

Options:
  --log-level {DEBUG,INFO,WARNING,ERROR}  Set logging level
  --demo-mode                             Run in demo mode
  --tab TAB_NAME                         Start with specific tab active
```

## 🔧 Component Dependencies

### Core Components (Always Available)

- **Case Builder**: Basic case management functionality
- **File Organizer**: File organization without AI features
- **System Monitor**: Basic system monitoring

### Optional Components (Require Additional Setup)

- **WhisperX**: Requires WhisperX service running
- **Legal Brain**: Requires Legal Brain service components
- **PhotoPrism**: Requires PhotoPrism installation
- **AI Analysis**: Requires AI models and GPU (optional)

### Service Dependencies

The application gracefully handles missing services:

- **Missing services**: Tabs show "demo mode" or limited functionality
- **Partial availability**: Core features work, advanced features disabled
- **Full availability**: All features enabled

## 📂 Project Structure

```
FILEBOSS/
├── sigma_fileboss_main.py          # Main application window
├── launch_sigma_fileboss.py        # Application launcher
├── requirements_sigma.txt          # Python dependencies
├── Start_SIGMA_FILEBOSS.bat        # Windows launcher
├── start_sigma_fileboss.sh         # Linux/macOS launcher
├── tabs/                           # Tab components
│   ├── __init__.py
│   ├── casebuilder_tab.py         # Case management tab
│   ├── whisperx_tab.py            # Audio transcription tab
│   ├── file_organizer_tab.py      # File organization tab
│   ├── document_generator_tab.py   # Document generation tab
│   ├── photoprism_tab.py          # Photo management tab
│   ├── legal_brain_tab.py         # Legal processing tab
│   ├── ai_analysis_tab.py         # AI analysis tab
│   └── system_monitor_tab.py      # System monitoring tab
├── casebuilder/                    # Existing CaseBuilder integration
├── PROJECT HEAD/                   # Existing project components
│   ├── Local-File-Organizer-main/
│   └── sigma-file-manager-2/
├── data/                          # Application data
├── logs/                          # Application logs
├── temp/                          # Temporary files
└── exports/                       # Exported files
```

## 🚀 Deployment Scenarios

### Development Environment

- Use SQLite database for simplicity
- Run all services locally
- Enable debug logging
- Use demo mode for missing components

### Production Environment

- Use PostgreSQL for better performance
- Deploy services in containers
- Configure proper logging
- Set up monitoring and backups

### Docker Deployment (Future)

```yaml
# docker-compose.yml (planned)
version: "3.8"
services:
  sigma-fileboss:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/fileboss
    depends_on:
      - db
      - whisper
      - photoprism
```

## 🔍 Troubleshooting

### Common Issues

#### "PyQt6 not found"

```bash
pip install PyQt6>=6.5.0
```

#### "No module named 'casebuilder'"

Ensure you're running from the correct directory and all paths are set up properly.

#### WhisperX service unavailable

- Check if WhisperX service is running
- Verify WHISPER_API_URL configuration
- Tab will show demo mode if service unavailable

#### Performance issues

- Close unused tabs to free memory
- Reduce AI model complexity
- Check available RAM and CPU usage

### Log Analysis

Check logs in the `logs/` directory:

- `sigma_fileboss.log`: Main application log
- Component-specific logs for detailed debugging

## 📈 Performance Optimization

### Memory Management

- **Tab Loading**: Tabs initialize only when first accessed
- **AI Models**: Load models on-demand to save memory
- **File Processing**: Stream large files instead of loading entirely

### Storage Optimization

- **Database**: Regular cleanup of old session data
- **Temp Files**: Automatic cleanup of temporary files
- **Cached Data**: LRU cache for frequently accessed data

## 🔐 Security Considerations

### Data Protection

- **Local Storage**: All data stored locally by default
- **Encryption**: Sensitive data encrypted at rest
- **Access Control**: File system permissions respected

### Network Security

- **API Endpoints**: Secure communication with external services
- **Input Validation**: All user inputs sanitized
- **Error Handling**: No sensitive data in error messages

## 🎯 Usage Examples

### Quick File Organization

1. Open File Organizer tab
2. Select source directory (drag-and-drop or browse)
3. Choose organization mode (by type/date/content)
4. Click "Start Organization"

### Audio Transcription Workflow

1. Open WhisperX tab
2. Load audio file (drag-and-drop or browse)
3. Configure transcription settings
4. Click "Start Transcription"
5. Save or export results

### Case Management

1. Open Case Builder tab
2. Create new case or select existing
3. Import files using drag-and-drop
4. Use cross-tab features to process files
5. Export case data when complete

## 🛟 Support & Documentation

### Getting Help

- **Issues**: Check the troubleshooting section
- **Logs**: Review application logs for errors
- **Demo Mode**: Use demo mode to test functionality

### Contributing

- Follow the existing code structure
- Add new tabs by extending the base tab interface
- Ensure graceful handling of missing dependencies

## 📋 Roadmap

### Planned Features

- **Enhanced AI Integration**: More AI models and capabilities
- **Cloud Integration**: Support for cloud storage providers
- **Plugin System**: Extensible architecture for custom plugins
- **Mobile Interface**: Web interface for mobile access
- **Collaboration Features**: Multi-user support and sharing

### Technical Improvements

- **Performance**: Async processing and better caching
- **Testing**: Comprehensive test suite
- **Documentation**: API documentation and user guides
- **Deployment**: Container-based deployment options

---

## 🎉 Quick Start Summary

**Windows Users:**

```
1. Download/clone repository
2. Double-click Start_SIGMA_FILEBOSS.bat
3. Wait for automatic setup
4. Start using the tabbed interface!
```

**Linux/macOS Users:**

```
1. Download/clone repository
2. Run: ./start_sigma_fileboss.sh
3. Wait for automatic setup
4. Start using the tabbed interface!
```

**From Command Line:**

```bash
git clone <repo>
cd FILEBOSS
pip install -r requirements_sigma.txt
python launch_sigma_fileboss.py
```

The application will launch with all available tabs enabled. Missing services will show demo mode, allowing you to explore the interface even without all components installed.

---

_SIGMA FILEBOSS - Where file management meets artificial intelligence._
