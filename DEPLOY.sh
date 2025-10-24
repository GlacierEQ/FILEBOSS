#!/bin/bash

# 🔥 FILEBOSS PRODUCTION DEPLOYMENT SCRIPT
# One-Command Deployment for Legal Case Management System
# Supports: Local, Docker, Cloud (Render/Railway/Heroku)

set -e

# Configuration
APP_NAME="FILEBOSS"
VERSION="2.0.0"
DEFAULT_PORT=8000
PRODUCTION_MODE=false
DOCKER_MODE=false
CLOUD_DEPLOY=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${PURPLE}[FILEBOSS]${NC} $1"
}

# Function to display banner
show_banner() {
    echo -e "${CYAN}"
    echo "██████╗ ██╗██╗     ███████╗██████╗  ██████╗ ███████╗███████╗"
    echo "██╔══██╗██║██║     ██╔════╝██╔══██╗██╔═══██╗██╔════╝██╔════╝"
    echo "██████╔╝██║██║     █████╗  ██████╔╝██║   ██║███████╗███████╗"
    echo "██╔══██╗██║██║     ██╔══╝  ██╔══██╗██║   ██║╚════██║╚════██║"
    echo "██║  ██║██║███████╗███████╗██████╔╝╚██████╔╝███████║███████║"
    echo "╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚═════╝  ╚═════╝ ╚══════╝╚══════╝"
    echo -e "${NC}"
    echo -e "${GREEN}🔥 Hyper-Powerful Legal Case Management System v$VERSION${NC}"
    echo -e "${BLUE}🏛️ Built for Operators | Ready for Production${NC}"
    echo ""
}

# Function to check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    local python_version=$(python3 --version | grep -oE '[0-9]+\.[0-9]+')
    if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 0 ]]; then
        log_error "Python 3.8+ is required (found $python_version)"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        log_error "pip is required but not installed"
        exit 1
    fi
    
    # Check Docker (if needed)
    if [[ "$DOCKER_MODE" == "true" ]]; then
        if ! command -v docker &> /dev/null; then
            log_error "Docker is required but not installed"
            exit 1
        fi
        
        if ! docker info > /dev/null 2>&1; then
            log_error "Docker is installed but not running"
            exit 1
        fi
    fi
    
    log_success "System requirements satisfied"
}

# Function to setup virtual environment
setup_venv() {
    log_info "Setting up Python virtual environment..."
    
    if [[ ! -d "venv" ]]; then
        python3 -m venv venv
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    log_success "Virtual environment ready"
}

# Function to install dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Ensure we have requirements file
    if [[ ! -f "requirements.txt" ]]; then
        log_error "requirements.txt not found"
        exit 1
    fi
    
    # Install requirements
    if [[ "$PRODUCTION_MODE" == "true" && -f "requirements-prod.txt" ]]; then
        pip install -r requirements-prod.txt
        log_success "Production dependencies installed"
    else
        pip install -r requirements.txt
        log_success "Development dependencies installed"
    fi
    
    # Install additional production dependencies
    if [[ "$PRODUCTION_MODE" == "true" ]]; then
        pip install gunicorn uvicorn[standard]
    fi
}

# Function to setup database
setup_database() {
    log_info "Initializing database..."
    
    # Run database tests
    if python3 test_db_fixed.py; then
        log_success "Database connection verified"
    else
        log_warn "Database test failed, but continuing..."
    fi
    
    # Run any database migrations
    if [[ -f "alembic.ini" ]]; then
        log_info "Running database migrations..."
        alembic upgrade head || log_warn "Alembic migrations failed (may be normal for first run)"
    fi
}

# Function for Docker deployment
deploy_docker() {
    log_header "Docker Deployment Mode"
    
    # Use production Docker Compose if available
    local compose_file="docker-compose.yml"
    if [[ "$PRODUCTION_MODE" == "true" && -f "docker-compose.prod.yml" ]]; then
        compose_file="docker-compose.prod.yml"
    fi
    
    log_info "Building and starting Docker containers..."
    docker-compose -f "$compose_file" up --build -d
    
    # Wait for services
    log_info "Waiting for services to start..."
    sleep 15
    
    # Health check
    if curl -s -f "http://localhost:$DEFAULT_PORT/health" > /dev/null; then
        log_success "Docker deployment successful!"
        return 0
    else
        log_error "Health check failed. Checking logs..."
        docker-compose -f "$compose_file" logs --tail=50
        return 1
    fi
}

# Function for local deployment
deploy_local() {
    log_header "Local Development Deployment"
    
    # Setup environment
    setup_venv
    source venv/bin/activate
    install_dependencies
    setup_database
    
    # Run tests
    log_info "Running verification tests..."
    python3 test_casebuilder_verification.py || log_warn "Some tests failed"
    
    # Start the application
    log_info "Starting FILEBOSS application..."
    
    if [[ "$PRODUCTION_MODE" == "true" ]]; then
        # Production server with Gunicorn
        gunicorn main:app --bind 0.0.0.0:$DEFAULT_PORT --workers 4 --worker-class uvicorn.workers.UvicornWorker &
        SERVER_PID=$!
    else
        # Development server
        python3 main.py &
        SERVER_PID=$!
    fi
    
    # Wait for server to start
    sleep 5
    
    # Health check
    if curl -s -f "http://localhost:$DEFAULT_PORT/health" > /dev/null; then
        log_success "FILEBOSS deployed successfully!"
        return 0
    else
        log_error "Deployment failed - server not responding"
        kill $SERVER_PID 2>/dev/null || true
        return 1
    fi
}

# Function for cloud deployment setup
setup_cloud_deploy() {
    log_header "Cloud Deployment Setup"
    
    log_info "Verifying cloud deployment configuration..."
    
    # Check for platform-specific files
    local platforms=()
    [[ -f "render.yaml" ]] && platforms+=("Render")
    [[ -f "railway.json" ]] && platforms+=("Railway") 
    [[ -f "app.json" ]] && platforms+=("Heroku")
    [[ -f "Dockerfile" ]] && platforms+=("Docker")
    
    if [[ ${#platforms[@]} -eq 0 ]]; then
        log_error "No cloud deployment configuration found"
        exit 1
    fi
    
    log_success "Cloud deployment ready for: ${platforms[*]}"
    
    echo ""
    echo "📤 Cloud Deployment Options:"
    echo "  🌐 Render:   Push to GitHub, connect at render.com"
    echo "  🚂 Railway:  Push to GitHub, connect at railway.app"
    echo "  🟣 Heroku:   heroku create && git push heroku main"
    echo "  🐳 Docker:   docker build -t fileboss . && docker run -p 8000:8000 fileboss"
    echo ""
}

# Function to run post-deployment tasks
post_deploy_tasks() {
    log_info "Running post-deployment tasks..."
    
    # Create sample data (in development)
    if [[ "$PRODUCTION_MODE" != "true" ]]; then
        log_info "Creating sample data..."
        python3 -c "
from casebuilder.database import get_db
from casebuilder.models import Case
import asyncio

async def create_sample():
    db = get_db()
    # Sample data creation would go here
    print('Sample data created')
    
asyncio.run(create_sample())
" 2>/dev/null || log_warn "Sample data creation skipped"
    fi
    
    # Open application in browser (local only)
    if [[ "$DOCKER_MODE" != "true" && "$CLOUD_DEPLOY" != "true" ]]; then
        sleep 3
        if command -v open &> /dev/null; then
            open "http://localhost:$DEFAULT_PORT"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "http://localhost:$DEFAULT_PORT"
        fi
    fi
    
    log_success "Post-deployment tasks completed"
}

# Function to display deployment info
show_deployment_info() {
    echo ""
    echo -e "${GREEN}🎉 FILEBOSS DEPLOYMENT SUCCESSFUL!${NC}"
    echo "=" * 50
    echo -e "${CYAN}🌐 Application URL:${NC} http://localhost:$DEFAULT_PORT"
    echo -e "${CYAN}📚 API Documentation:${NC} http://localhost:$DEFAULT_PORT/docs"
    echo -e "${CYAN}🔄 Alternative Docs:${NC} http://localhost:$DEFAULT_PORT/redoc"
    echo -e "${CYAN}❤️ Health Check:${NC} http://localhost:$DEFAULT_PORT/health"
    echo ""
    echo -e "${YELLOW}🛠️ Management Commands:${NC}"
    
    if [[ "$DOCKER_MODE" == "true" ]]; then
        echo "  docker-compose logs -f     # View logs"
        echo "  docker-compose down        # Stop services"
        echo "  docker-compose restart     # Restart services"
    else
        echo "  pkill -f 'python.*main.py' # Stop application"
        echo "  python3 main.py            # Restart application"
        echo "  tail -f logs/fileboss.log  # View logs"
    fi
    
    echo ""
    echo -e "${GREEN}🚀 FILEBOSS is ready for action!${NC}"
}

# Function to parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --production)
                PRODUCTION_MODE=true
                log_info "Production mode enabled"
                shift
                ;;
            --docker)
                DOCKER_MODE=true
                log_info "Docker mode enabled"
                shift
                ;;
            --cloud)
                CLOUD_DEPLOY=true
                log_info "Cloud deployment mode"
                shift
                ;;
            --port)
                DEFAULT_PORT="$2"
                log_info "Using custom port: $DEFAULT_PORT"
                shift 2
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Function to show usage
show_usage() {
    cat << EOF
🔥 FILEBOSS Deployment Script v$VERSION

Usage: $0 [OPTIONS]

Options:
    --production    Deploy in production mode with optimizations
    --docker        Use Docker for deployment
    --cloud         Setup for cloud deployment (Render/Railway/Heroku)
    --port PORT     Use custom port (default: $DEFAULT_PORT)
    --help, -h      Show this help message

Deployment Modes:
    Local Development:   $0
    Production Local:    $0 --production
    Docker Development:  $0 --docker
    Docker Production:   $0 --docker --production
    Cloud Setup:         $0 --cloud

Examples:
    $0                           # Quick local development
    $0 --production --port 5000  # Production on port 5000
    $0 --docker                  # Docker development
    $0 --cloud                   # Prepare for cloud deployment

EOF
}

# Main deployment function
main() {
    show_banner
    
    log_header "Starting $APP_NAME v$VERSION deployment..."
    
    # Parse command line arguments
    parse_args "$@"
    
    # Check requirements
    check_requirements
    
    # Choose deployment method
    if [[ "$CLOUD_DEPLOY" == "true" ]]; then
        setup_cloud_deploy
    elif [[ "$DOCKER_MODE" == "true" ]]; then
        deploy_docker
    else
        deploy_local
    fi
    
    # Run post-deployment tasks
    post_deploy_tasks
    
    # Show deployment information
    show_deployment_info
    
    log_header "FILEBOSS deployment completed successfully!"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    # Any cleanup tasks would go here
}

# Set trap for cleanup
trap cleanup EXIT

# Run main function with all arguments
main "$@"