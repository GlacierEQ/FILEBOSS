#!/bin/bash
# Script to set up Hugging Face integration

set -e

# Make script directory the working directory
cd "$(dirname "$0")"
# Go up one level to project root
cd ..

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.9 or newer."
    exit 1
fi

# Create directories if they don't exist
mkdir -p src/utils
mkdir -p src/integrations

# Ensure required packages are installed
echo "Installing required packages for Hugging Face integration..."
pip install huggingface_hub transformers sentence-transformers python-dotenv

# Run the setup script
echo "Setting up Hugging Face integration..."
python -c "from src.utils.huggingface_setup import setup_huggingface; setup_huggingface()"

echo "✅ Hugging Face setup complete!"
echo "You can now use HuggingFaceLawGlance from src.integrations.simple_lawglance_hf"
