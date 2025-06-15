#!/bin/bash
set -e

# ANSI color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}  DeepSeek-Coder Setup Script        ${NC}"
echo -e "${BLUE}=====================================${NC}"

# Function to check for command availability
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}Error: $1 is not installed or not in PATH${NC}"
        echo "Please install $1 and try again."
        return 1
    else
        echo -e "${GREEN}✓ $1 is installed${NC}"
        return 0
    fi
}

# Parse arguments
SKIP_DEPS=false
EVAL_ONLY=false
FINETUNE_ONLY=false
DEMO_ONLY=false
CREATE_VENV=true
VENV_NAME="deepsoul-env"
TEST_MODEL=false
SETUP_CACHE=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-deps)
            SKIP_DEPS=true
            shift
            ;;
        --eval-only)
            EVAL_ONLY=true
            shift
            ;;
        --finetune-only)
            FINETUNE_ONLY=true
            shift
            ;;
        --demo-only)
            DEMO_ONLY=true
            shift
            ;;
        --no-venv)
            CREATE_VENV=false
            shift
            ;;
        --venv-name)
            VENV_NAME="$2"
            shift 2
            ;;
        --test-model)
            TEST_MODEL=true
            shift
            ;;
        --no-cache)
            SETUP_CACHE=false
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Check for Python
echo "Checking for Python..."
check_command python3 || { echo -e "${RED}Python 3 is required to use DeepSeek-Coder.${NC}"; exit 1; }

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${RED}Python 3.8 or higher is required. Found: $PYTHON_VERSION${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Python version $PYTHON_VERSION is compatible${NC}"
fi

# Check for pip
echo "Checking for pip..."
check_command pip3 || { echo -e "${RED}pip3 is required to use DeepSeek-Coder.${NC}"; exit 1; }

# Check for git
echo "Checking for git..."
check_command git || echo -e "${YELLOW}Warning: git not found. Some features may not work correctly.${NC}"

# Create virtual environment if requested
if [ "$CREATE_VENV" = true ]; then
    echo "Creating virtual environment '$VENV_NAME'..."
    python3 -m venv $VENV_NAME
    
    # Activate virtual environment
    echo "Activating virtual environment..."
    source $VENV_NAME/bin/activate
    
    echo -e "${GREEN}✓ Virtual environment created and activated${NC}"
    echo -e "${YELLOW}To activate the virtual environment in the future, run:${NC}"
    echo -e "${BLUE}source $VENV_NAME/bin/activate${NC}"
fi

# Install dependencies if not skipped
if [ "$SKIP_DEPS" = false ]; then
    echo "Upgrading pip, setuptools, and wheel..."
    pip3 install --upgrade pip setuptools wheel
    
    if [ "$EVAL_ONLY" = true ]; then
        echo "Installing evaluation dependencies..."
        pip3 install -r Evaluation/HumanEval/requirements.txt
        pip3 install -r Evaluation/MBPP/requirements.txt
        pip3 install -r Evaluation/PAL-Math/requirements.txt
        pip3 install -r Evaluation/DS-1000/requirements.txt
    elif [ "$FINETUNE_ONLY" = true ]; then
        echo "Installing fine-tuning dependencies..."
        pip3 install -r finetune/requirements.txt
    elif [ "$DEMO_ONLY" = true ]; then
        echo "Installing demo dependencies..."
        pip3 install -r demo/requirements.txt
    else
        echo "Installing base dependencies..."
        pip3 install -r requirements.txt
    fi
    
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# Check for CUDA
echo "Checking for CUDA support in PyTorch..."
CUDA_AVAILABLE=$(python3 -c "import torch; print(torch.cuda.is_available())")

if [ "$CUDA_AVAILABLE" = "True" ]; then
    NUM_GPUS=$(python3 -c "import torch; print(torch.cuda.device_count())")
    if [ "$NUM_GPUS" -gt 0 ]; then
        echo -e "${GREEN}✓ CUDA is available with $NUM_GPUS GPU(s)${NC}"
        python3 -c "import torch; [print(f'  {i}: {torch.cuda.get_device_name(i)}') for i in range(torch.cuda.device_count())]"
    else
        echo -e "${YELLOW}Warning: CUDA is available but no GPUs detected${NC}"
    fi
else
    echo -e "${YELLOW}Warning: CUDA is not available. Models will run on CPU which will be very slow.${NC}"
fi

# Set up model cache
if [ "$SETUP_CACHE" = true ]; then
    echo "Setting up model cache..."
    mkdir -p models
    export TRANSFORMERS_CACHE="$(pwd)/models"
    echo -e "${GREEN}✓ Model cache directory created at $(pwd)/models${NC}"
    echo -e "${YELLOW}To use this cache location in the future, set:${NC}"
    echo -e "${BLUE}export TRANSFORMERS_CACHE=\"$(pwd)/models\"${NC}"
fi

# Download and test a small model if requested
if [ "$TEST_MODEL" = true ]; then
    echo "Downloading and testing a small model..."
    python3 -c "from transformers import AutoTokenizer; tokenizer = AutoTokenizer.from_pretrained('deepseek-ai/deepseek-coder-1.3b-base', trust_remote_code=True); print('Tokenizer loaded successfully')"
    echo -e "${GREEN}✓ Test model downloaded successfully${NC}"
fi

# Create data directories
echo "Creating necessary directories..."
mkdir -p data logs

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}  DeepSeek-Coder setup complete!     ${NC}"
echo -e "${GREEN}=====================================${NC}"
echo -e "To get started, try the examples in the README.md file."
echo -e "For issues or questions, please visit: https://github.com/deepseek-ai/deepseek-coder"
echo -e ""
if [ "$CREATE_VENV" = true ]; then
    echo -e "${YELLOW}Remember to activate the virtual environment with:${NC}"
    echo -e "${BLUE}source $VENV_NAME/bin/activate${NC}"
fi
