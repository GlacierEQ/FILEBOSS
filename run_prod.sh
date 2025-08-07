#!/bin/bash

# Activate the virtual environment
source ./venv/Scripts/activate

# Set environment variables
export ENVIRONMENT=production
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run Gunicorn with the configuration file
echo "Starting CaseBuilder in production mode..."
gunicorn -c gunicorn_config.py main:app
