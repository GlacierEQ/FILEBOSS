# Files - A Modern File Explorer

[![Build Status](https://dev.azure.com/files-community/Files/_apis/build/status/Build%20Pipeline?branchName=main)](https://dev.azure.com/files-community/Files/_build/latest?definitionId=1&branchName=main)

A modern file explorer that pushes the boundaries of the Windows platform.

## Features

- **Modern UI**: Built with WinUI 3 for a fluent, responsive experience
- **Tabs**: Multiple tabs for easy file management
- **Dual Pane**: View and manage two locations side by side
- **Extensible**: Plugin system for adding new features
- **Localization**: Support for multiple languages
- **Dark/Light Theme**: Choose your preferred color scheme

## New in This Version

### Plugin System

Files now includes a powerful plugin system that allows developers to extend its functionality. Plugins can add new features, modify existing behavior, or integrate with external services.

- **Easy Integration**: Simple API for plugin development
- **Sandboxed**: Plugins run in their own context for security
- **Lifecycle Management**: Proper initialization and cleanup

For more information, see the [Plugin Development Guide](PLUGINS_README.md).

### Localization

Files now supports multiple languages through a comprehensive localization system:

- **Resource-based**: Uses standard .resw files for translations
- **Runtime Switching**: Change languages without restarting
- **Developer-Friendly**: Easy to add new languages and strings

For more information, see the [Localization Guide](LOCALIZATION_GUIDE.md).

## Getting Started

### Prerequisites

- Windows 10 version 1809 (build 17763) or later
- .NET 6.0 or later
- Windows App SDK 1.0 or later

### Installation

1. Download the latest release from the [Releases](https://github.com/files-community/Files/releases) page
2. Run the installer
3. Launch Files from the Start menu

### Building from Source

1. Clone the repository:
   ```
   git clone https://github.com/files-community/Files.git
   ```
2. Open the solution in Visual Studio 2022 or later
3. Build and run the solution

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more information.

### Code of Conduct

This project has adopted the [Contributor Covenant](CODE_OF_CONDUCT.md) as its Code of Conduct.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to all our contributors
- Built with ❤️ by the Files Community
