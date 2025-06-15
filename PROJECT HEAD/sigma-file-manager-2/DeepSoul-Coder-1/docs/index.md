# DeepSeek-Coder Documentation

Welcome to the DeepSeek-Coder documentation. This guide will help you understand, install, and use the DeepSeek-Coder system for AI-powered code generation and completion.

## Quick Links

- [Installation](installation.md)
- [Getting Started](getting_started.md)
- [API Reference](api/index.md)
- [Tutorials](tutorials/index.md)
- [Advanced Usage](advanced/index.md)

## Overview

DeepSeek-Coder is composed of a series of code language models, each trained from scratch on 2T tokens, with a composition of 87% code and 13% natural language in both English and Chinese. We provide various sizes of the code model, ranging from 1B to 33B versions. Each model is pre-trained on project-level code corpus by employing a window size of 16K and an extra fill-in-the-blank task, to support project-level code completion and infilling.

## Features

- **Code Completion**: Generate and complete code in multiple programming languages
- **Code Insertion**: Insert code between existing blocks of code
- **Chat Interface**: Interact with the model in a conversational manner
- **Repository-Level Understanding**: Process and understand entire codebases
- **API Access**: Access all functionality through a RESTful API

## Requirements

- Python 3.8 or higher
- CUDA-compatible GPU (recommended)
- Docker (for containerized deployment)

## License

This code repository is licensed under the MIT License. The use of DeepSeek Coder models is subject to the Model License. DeepSeek Coder supports commercial use.
