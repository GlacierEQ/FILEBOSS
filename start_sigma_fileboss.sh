#!/bin/bash
echo "========================================"
echo "  SIGMA FILEBOSS - Unified File Manager"
echo "========================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and try again"
    exit 1
fi

# Change to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
else
    echo "No virtual environment found. Using system Python."
fi

# Check if requirements are installed
python3 -c "import PyQt6" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing required packages..."
    pip3 install -r requirements_sigma.txt
    if [ $? -ne 0 ]; then
        echo "Error: Failed to install requirements"
        exit 1
    fi
fi

echo
echo "Starting SIGMA FILEBOSS..."
echo

# Launch the application
python3 launch_sigma_fileboss.py "$@"

if [ $? -ne 0 ]; then
    echo
    echo "Application exited with error"
    read -p "Press Enter to continue..."
fi

echo
echo "SIGMA FILEBOSS closed."
