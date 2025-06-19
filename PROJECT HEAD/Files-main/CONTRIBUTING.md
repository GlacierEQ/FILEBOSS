# Contributing to Files

Thank you for your interest in contributing to Files! We welcome all contributions, whether they're bug reports, feature requests, documentation improvements, or code contributions.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)
  - [Pull Requests](#pull-requests)
- [Development Setup](#development-setup)
- [Coding Guidelines](#coding-guidelines)
- [Plugin Development](#plugin-development)
- [Localization](#localization)
- [License](#license)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the [existing issues](https://github.com/files-community/Files/issues) to see if the problem has already been reported.

When creating a bug report, please include:
- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Screenshots if applicable
- Your system information (Windows version, app version, etc.)

### Suggesting Enhancements

We welcome suggestions for new features and improvements. Please check the [existing feature requests](https://github.com/files-community/Files/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement) before creating a new one.

When suggesting an enhancement, please include:
- A clear, descriptive title
- A detailed description of the feature
- Why this feature would be useful
- Any potential drawbacks or considerations

### Your First Code Contribution

1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Make your changes
4. Add tests for your changes
5. Run the test suite and ensure all tests pass
6. Submit a pull request

### Pull Requests

- Keep pull requests focused on a single feature or bugfix
- Include tests for new features and bugfixes
- Update documentation as needed
- Follow the coding guidelines below
- Reference any related issues in your pull request

## Development Setup

### Prerequisites

- Windows 10 version 1809 (build 17763) or later
- Visual Studio 2022 or later with the following workloads:
  - .NET desktop development
  - Universal Windows Platform development
  - Desktop development with C++
- Windows 10/11 SDK (10.0.19041.0 or later)

### Building the Project

1. Clone the repository
2. Open `Files.sln` in Visual Studio
3. Restore NuGet packages
4. Build the solution
5. Run the application

## Coding Guidelines

- Follow the [C# Coding Conventions](https://docs.microsoft.com/en-us/dotnet/csharp/fundamentals/coding-style/coding-conventions)
- Use meaningful variable and method names
- Add XML documentation for public APIs
- Keep methods small and focused
- Write unit tests for new features

## Plugin Development

Files supports plugins to extend its functionality. See the [Plugin Development Guide](PLUGINS_README.md) for more information.

## Localization

We welcome contributions to translate Files into more languages. See the [Localization Guide](LOCALIZATION_GUIDE.md) for more information.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
