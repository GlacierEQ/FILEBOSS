#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display help
show_help() {
    echo -e "${YELLOW}FileBoss Development Script${NC}"
    echo "Usage: ./dev.sh [command]"
    echo ""
    echo "Commands:"
    echo "  setup            Set up the development environment"
    echo "  start            Start the development server"
    echo "  test             Run tests"
    echo "  lint             Run linters"
    echo "  format           Format code with black and isort"
    echo "  db-migrate       Create a new database migration"
    echo "  db-upgrade       Apply database migrations"
    echo "  db-downgrade     Rollback database migrations"
    echo "  help             Show this help message"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Setup development environment
setup() {
    echo -e "${GREEN}Setting up development environment...${NC}"
    
    # Check if Python 3.9+ is installed
    if ! command_exists python3; then
        echo -e "${RED}Python 3.9 or higher is required but not installed.${NC}"
        exit 1
    fi
    
    # Check if pip is installed
    if ! command_exists pip3; then
        echo -e "${RED}pip3 is required but not installed.${NC}"
        exit 1
    fi
    
    # Create and activate virtual environment
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate  # On Windows: .\venv\Scripts\activate
    
    # Install dependencies
    echo -e "${GREEN}Installing dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Set up pre-commit hooks
    echo -e "${GREEN}Setting up pre-commit hooks...${NC}"
    pre-commit install
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}Please update the .env file with your configuration.${NC}"
    fi
    
    echo -e "${GREEN}Setup complete!${NC}"
    echo -e "To activate the virtual environment, run: source venv/bin/activate"
}

# Start development server
start() {
    echo -e "${GREEN}Starting development server...${NC}"
    uvicorn app.main:app --reload
}

# Run tests
test() {
    echo -e "${GREEN}Running tests...${NC}"
    pytest tests/ -v --cov=app --cov-report=term-missing
}

# Run linters
lint() {
    echo -e "${GREEN}Running flake8...${NC}"
    flake8 app tests
    
    echo -e "\n${GREEN}Running mypy...${NC}"
    mypy app
}

# Format code
format() {
    echo -e "${GREEN}Running isort...${NC}"
    isort .
    
    echo -e "\n${GREEN}Running black...${NC}"
    black .
}

# Create a new migration
db_migrate() {
    if [ -z "$1" ]; then
        echo -e "${RED}Please provide a migration message.${NC}"
        echo "Usage: ./dev.sh db-migrate <message>"
        exit 1
    fi
    
    echo -e "${GREEN}Creating new migration...${NC}"
    alembic revision --autogenerate -m "$1"
}

# Apply migrations
db_upgrade() {
    echo -e "${GREEN}Applying database migrations...${NC}"
    alembic upgrade head
}

# Rollback migrations
db_downgrade() {
    echo -e "${YELLOW}Warning: This will rollback the database schema.${NC}"
    read -p "Are you sure you want to continue? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${GREEN}Rolling back database...${NC}"
        alembic downgrade -1
    else
        echo -e "${YELLOW}Operation cancelled.${NC}"
    fi
}

# Main script execution
case "$1" in
    setup)
        setup
        ;;
    start)
        start
        ;;
    test)
        test
        ;;
    lint)
        lint
        ;;
    format)
        format
        ;;
    db-migrate)
        shift
        db_migrate "$@"
        ;;
    db-upgrade)
        db_upgrade
        ;;
    db-downgrade)
        db_downgrade
        ;;
    help|*)
        show_help
        ;;
esac
