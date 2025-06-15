@echo off
echo Setting up PhotoPrism Sorting Department...

REM Create necessary directories
echo Creating directories...
python -c "import os; os.makedirs('C:/Users/casey/PhotoPrism/storage/sorting-dept', exist_ok=True)"

REM Register with service
echo Registering with service...
python integration/photoprism/photoprism_integration.py

echo Setup complete!
echo To start the PhotoPrism Sorting Department, run: run_photoprism_sorter.bat
