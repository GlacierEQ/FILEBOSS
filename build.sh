#!/bin/bash

# FILEBOSS Build Script
echo "🚀 Building FILEBOSS v2.0.0-APEX..."

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-prod.txt

# Create database directory
echo "📁 Creating database directory..."
mkdir -p data

# Run database migrations if needed
echo "🗄️  Database ready"

echo "✅ Build complete!"
