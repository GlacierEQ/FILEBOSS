# Makefile for LawGlance

.PHONY: help setup clean build build-exe build-installer build-portable build-webview build-all

# Default target
help:
	@echo "LawGlance Build System"
	@echo "======================="
	@echo "Available targets:"
	@echo "  setup         - Create virtual environment and install dependencies"
	@echo "  clean         - Remove build artifacts"
	@echo "  build-exe     - Build standalone executable"
	@echo "  build-installer - Build Windows installer (requires Inno Setup)"
	@echo "  build-portable - Create portable ZIP package"
	@echo "  build-webview - Build PyWebView desktop application"
	@echo "  build-all     - Build all package types"

# Setup virtual environment and dependencies
setup:
	@echo "Setting up development environment..."
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	. venv/bin/activate && pip install pyinstaller pillow

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	rm -rf build dist __pycache__ output
	find . -name "*.pyc" -delete

# Build standalone executable
build-exe:
	@echo "Building executable..."
	. venv/bin/activate && python scripts/build.py --exe

# Build Windows installer
build-installer:
	@echo "Building installer..."
	. venv/bin/activate && python scripts/build.py --exe --installer

# Build portable package
build-portable:
	@echo "Building portable package..."
	. venv/bin/activate && python scripts/build.py --exe --portable

# Build PyWebView application
build-webview:
	@echo "Building PyWebView application..."
	. venv/bin/activate && python scripts/build.py --webview

# Build all packages
build-all:
	@echo "Building all package types..."
	. venv/bin/activate && python scripts/build.py --all
