#!/bin/bash
# Build script for LawGlance on Mac/Linux
# Automates verification, dependency installation, and executable creation

# Color codes for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print a header with blue background
print_header() {
    echo -e "${BLUE}"
    echo "======================================================================"
    echo "                 $1"
    echo "======================================================================"
    echo -e "${NC}"
}

# Print success message with green checkmark
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print error message with red X
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Print warning message in yellow
print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

# Starting script
print_header "LAWGLANCE EXECUTABLE BUILDER"
echo "This script will verify your system and build the LawGlance executable."
echo

# Step 1: Verify Python is installed correctly
print_header "STEP 1: VERIFYING PYTHON INSTALLATION"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2)
python_major=$(echo $python_version | cut -d. -f1)
python_minor=$(echo $python_version | cut -d. -f2)

echo "Found Python version: $python_version"

# Ensure Python 3.8+
if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 8 ]); then
    print_error "Python 3.8 or higher is required. Found $python_version"
    exit 1
fi
print_success "Python version is adequate for LawGlance."

# Check for pip
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip."
    exit 1
fi
print_success "pip is installed and working correctly."

# Step 2: Install all required dependencies
print_header "STEP 2: INSTALLING DEPENDENCIES"

# Install core dependencies for building
echo "Installing core build dependencies..."
pip3 install --upgrade pyinstaller pillow setuptools wheel cmake ninja
if [ $? -ne 0 ]; then
    print_error "Failed to install core dependencies."
    exit 1
fi
print_success "Core dependencies installed."

# Install project requirements
echo "Installing project requirements..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        print_warning "Some requirements may have failed to install."
    else
        print_success "Project requirements installed."
    fi
else
    print_warning "requirements.txt not found. Skipping project requirements."
fi

# Step 3: Create a logo if one doesn't exist
print_header "STEP 3: CHECKING FOR LOGO"

mkdir -p logo

if [ ! -f "logo/logo.png" ]; then
    echo "Logo not found. Creating a new logo..."
    
    # Create a simple logo using Python
    python3 -c '
import os
try:
    from PIL import Image, ImageDraw
    
    # Create a blue background
    img = Image.new("RGB", (256, 256), color=(33, 150, 243))
    draw = ImageDraw.Draw(img)
    
    # Draw scales of justice in white
    # Horizontal bar
    draw.rectangle([64, 170, 192, 192], fill=(255, 255, 255))
    # Vertical stand
    draw.rectangle([118, 64, 138, 170], fill=(255, 255, 255))
    # Left scale
    draw.ellipse([64, 64, 114, 114], outline=(255, 255, 255), width=10)
    # Right scale
    draw.ellipse([162, 64, 212, 114], outline=(255, 255, 255), width=10)
    
    # Save as PNG
    img.save("logo/logo.png", format="PNG")
    print("Created logo image successfully.")
    
    # On macOS/Linux, we don't need ICO files but create one anyway for compatibility
    img.save("logo/logo.ico", format="ICO", sizes=[(32, 32), (64, 64), (128, 128), (256, 256)])
    
except ImportError:
    print("Error: PIL/Pillow not installed correctly. Cannot create logo.")
    print("Please install Pillow: pip3 install pillow")
    exit(1)
except Exception as e:
    print(f"Error creating logo: {str(e)}")
    exit(1)
'
    if [ $? -ne 0 ]; then
        print_error "Failed to create logo."
    else
        print_success "Logo created successfully."
    fi
else
    print_success "Logo already exists."
fi

# Step 4: Build the project using CMake and Ninja
print_header "STEP 4: BUILDING PROJECT"

echo "Starting CMake build process with Ninja..."
mkdir -p build
cd build

# Configure the project
cmake -G Ninja ..
if [ $? -ne 0 ]; then
    print_error "CMake configuration failed."
    exit 1
fi

# Build the project with parallel jobs
ninja -j12
if [ $? -ne 0 ]; then
    print_error "Ninja build failed."
    exit 1
fi

print_success "Project built successfully."

# Step 5: Provide clear instructions on next steps
print_header "STEP 5: NEXT STEPS"

EXECUTABLE="dist/LawGlance"
if [ -f "$EXECUTABLE" ]; then
    print_success "Your LawGlance executable is ready at: $EXECUTABLE"
    
    echo
    echo "To use LawGlance:"
    echo "1. Create a file named '.env' in the same folder as the executable"
    echo "2. Add your OpenAI API key to the .env file:"
    echo "   OPENAI_API_KEY=your_api_key_here"
    echo "3. Run LawGlance using: ./dist/LawGlance"
    echo
    echo "Important Notes:"
    echo "- Make sure the executable has execute permissions (chmod +x dist/LawGlance)"
    echo "- The first run may take a few moments to start up"
    echo "- You'll need an active internet connection"
else
    print_error "Could not find the LawGlance executable."
    echo "The build process may have failed or created the executable in a different location."
    echo "Please check the 'dist' directory or build output for details."
fi

print_header "BUILD PROCESS COMPLETE"
echo "Thank you for using LawGlance!"
echo
