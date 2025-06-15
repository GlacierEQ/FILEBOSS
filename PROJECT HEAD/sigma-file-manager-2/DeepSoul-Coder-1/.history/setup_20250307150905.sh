#!/bin/bash

# DeepSeek-Coder Setup Script for Unix-like systems
# This script helps set up the environment for DeepSeek-Coder

# ANSI color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored messages
print_msg() {
  echo -e "${2}${1}${NC}"
}

print_header() {
  echo -e "\n${BLUE}===========================${NC}"
  echo -e "${BLUE}  $1${NC}"
  echo -e "${BLUE}===========================${NC}"
}

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check for Python
print_header "Checking Python"
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    print_msg "Python is not installed. Please install Python 3.8 or higher and try again." "$RED"
    exit 1
fi

# Check Python version
PY_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
print_msg "Python version: $PY_VERSION" "$GREEN"

# Version check
if (( $(echo "$PY_VERSION < 3.8" | bc -l) )); then
    print_msg "Python version is too old. DeepSeek-Coder requires Python 3.8 or higher." "$RED"
    exit 1
fi

# Check for virtual environment
if [ -d "$SCRIPT_DIR/venv" ]; then
    print_msg "Virtual environment found. Activating..." "$GREEN"
    source "$SCRIPT_DIR/venv/bin/activate"
    if [ $? -ne 0 ]; then
        print_msg "Failed to activate virtual environment." "$RED"
        print_msg "Continuing with system Python..." "$YELLOW"
    else
        print_msg "Virtual environment activated." "$GREEN"
    fi
else
    print_msg "No virtual environment found at $SCRIPT_DIR/venv" "$YELLOW"
    print_msg "You can create one using: python -m venv venv" "$YELLOW"
    print_msg "Continuing with system Python..." "$YELLOW"
fi

# Check for pip
print_header "Checking pip"
if ! $PYTHON_CMD -m pip --version &>/dev/null; then
    print_msg "pip is not installed. Installing pip..." "$YELLOW"
    $PYTHON_CMD -m ensurepip --upgrade
    if [ $? -ne 0 ]; then
        print_msg "Failed to install pip. Please install pip manually." "$RED"
        exit 1
    fi
fi

# Run the setup.py script with the provided arguments
print_header "Running Setup Script"
$PYTHON_CMD "$SCRIPT_DIR/setup.py" "$@"
SETUP_EXIT_CODE=$?

if [ $SETUP_EXIT_CODE -ne 0 ]; then
    print_msg "\nSetup encountered errors. Please check the output above for details." "$RED"
else
    print_msg "\nSetup completed successfully!" "$GREEN"
fi

print_header "Additional Information"
print_msg "If you encountered any issues, please check the following:" "$YELLOW"
print_msg "1. Make sure you have Python 3.8 or higher installed."
print_msg "2. If you're using a virtual environment, ensure it's activated."
print_msg "3. For GPU support, make sure you have NVIDIA drivers installed and compatible with CUDA 11.8."
print_msg "4. Check the README.md for more information on usage and requirements."
print_msg "\nFor more help, visit: https://github.com/deepseek-ai/deepseek-coder/issues"

exit $SETUP_EXIT_CODE
