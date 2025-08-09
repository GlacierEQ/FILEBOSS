# 🚀 FILEBOSS - Advanced File Management System

FILEBOSS is a powerful, scalable file management system built with FastAPI and modern Python. It provides a robust API for file operations, user management, and secure access control.

## ✨ Features

- **RESTful API**: Built with FastAPI for high performance and automatic OpenAPI documentation
- **Modern Python**: Type hints, async/await, and Pydantic models throughout
- **Modular Architecture**: Clean separation of concerns with domain-driven design
- **Authentication & Authorization**: JWT-based authentication with role-based access control
- **File Processing**: Support for various file types with metadata extraction
- **Database**: SQLAlchemy ORM with async support, PostgreSQL recommended
- **Testing**: Comprehensive test suite with pytest and coverage reporting
- **Containerized**: Ready for Docker and Kubernetes deployment
- **CI/CD**: GitHub Actions for automated testing and deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 14+ (or SQLite for development)
- Redis 7+ (for caching and async tasks)
- Docker 20.10+ and Docker Compose 2.0+ (optional)

## 🛠 Installation

### Local Development

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/FILEBOSS.git
   cd FILEBOSS
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e ".[dev,test]"
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   alembic upgrade head
   python -m app.db.init_db
   ```

6. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   
   Interactive API documentation:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### With Docker

1. Clone the repository and navigate to the project directory

2. Copy and configure the environment file:
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```

3. Build and start the services:
   ```bash
   docker-compose up -d --build
   ```

4. Initialize the database:
   ```bash
   docker-compose exec app alembic upgrade head
   docker-compose exec app python -m app.db.init_db
   ```

The application will be available at `http://localhost:8000`

## 🏗 Project Structure

```
FILEBOSS/
├── app/                    # Application package
│   ├── api/                # API routes and endpoints
│   ├── core/               # Core functionality (config, security, etc.)
│   ├── db/                 # Database models and migrations
│   ├── schemas/            # Pydantic models for request/response validation
│   ├── services/           # Business logic and service layer
│   └── utils/              # Utility functions and helpers
├── tests/                  # Test suite
├── alembic/                # Database migrations
├── .github/                # GitHub Actions workflows
├── .env.example            # Example environment variables
├── .gitignore
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Production Dockerfile
├── pyproject.toml          # Project configuration and dependencies
└── README.md               # This file
```

## 🧪 Testing

Run tests with coverage:
```bash
pytest --cov=app --cov-report=term-missing
```

Run specific test file:
```bash
pytest tests/path/to/test_file.py -v
```

## 🛠 Development

### Code Style

- Code formatting with Black and isort
- Type checking with mypy
- Linting with flake8 and pylint

Pre-commit hooks are configured to run these checks before each commit.

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "description of changes"
```

Apply migrations:
```bash
alembic upgrade head
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

Your Name - [@your_twitter](https://twitter.com/your_twitter) - your.email@example.com

Project Link: [https://github.com/your-username/FILEBOSS](https://github.com/your-username/FILEBOSS)

### Local Development Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up the database:
   ```bash
   # Start PostgreSQL and Redis
   docker-compose up -d postgres redis
   
   # Run migrations
   alembic upgrade head
   
   # Initialize database
   python scripts/init_db.py
   ```

## 🚦 Running the Application

### Development Mode

```bash
# Start the development server
uvicorn casebuilder.api.app:app --reload

# Or using the start script
python scripts/start.py
```

### Production Mode

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f
```

### Accessing the Application

- **API Documentation**:
  - Swagger UI: http://localhost:8000/api/docs
  - ReDoc: http://localhost:8000/api/redoc
- **PGAdmin** (if enabled): http://localhost:5050
  - Default credentials: admin@example.com / admin

## 📚 API Documentation

For detailed API documentation, visit the interactive documentation at:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Main API Endpoints

#### Authentication
- `POST /api/v1/auth/token` - Get access token (OAuth2 password flow)
- `POST /api/v1/auth/refresh` - Refresh access token

#### Evidence Management
- `POST /api/v1/evidence/upload` - Upload a new evidence file
- `POST /api/v1/evidence/process-directory` - Process a directory of evidence files
- `GET /api/v1/evidence/{evidence_id}` - Get evidence details
- `PUT /api/v1/evidence/{evidence_id}/status` - Update evidence status
- `POST /api/v1/evidence/organize` - Organize evidence files
- `POST /api/v1/evidence/{evidence_id}/link-timeline` - Link evidence to timeline event

#### Case Management
- `GET /api/v1/cases` - List all cases
- `POST /api/v1/cases` - Create a new case
- `GET /api/v1/cases/{case_id}` - Get case details
- `GET /api/v1/cases/{case_id}/evidence` - Get evidence for a case
- `GET /api/v1/cases/{case_id}/timeline` - Get timeline for a case

#### Timeline Management
- `GET /api/v1/timeline` - List timeline events
- `POST /api/v1/timeline` - Create a new timeline event
- `POST /api/v1/timeline/{event_id}/link-evidence` - Link evidence to a timeline event
- `GET /api/v1/timeline/search` - Search timeline events

## 🔧 Development

### Prerequisites
- Python 3.10+
- Poetry (for dependency management)
- Docker and Docker Compose

### Setup

1. Install Poetry (if not installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

### Code Quality

This project uses several tools to maintain code quality:

```bash
# Format code with Black and isort
poetry run black .
poetry run isort .

# Type checking with mypy
poetry run mypy .

# Linting with pylint
poetry run pylint casebuilder tests

# Run all checks
poetry run pre-commit run --all-files
```

### Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=casebuilder --cov-report=html

# Run a specific test file
pytest tests/test_evidence_processing.py -v
```

### Database Migrations

1. Create a new migration:
   ```bash
   docker-compose exec app python scripts/create_migration.py -m "Your migration message"
   ```

2. Apply migrations:
   ```bash
   docker-compose exec app alembic upgrade head
   ```

## 🚀 Deployment

### Docker Compose (Development/Staging)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Run database migrations
docker-compose exec app alembic upgrade head

# Initialize database
docker-compose exec app python scripts/init_db.py
```

### Production Deployment

For production deployments, we recommend using:

1. **Docker Swarm** or **Kubernetes** for container orchestration
2. **Traefik** or **Nginx** as reverse proxy with Let's Encrypt
3. **PostgreSQL** with replication and backups
4. **Redis** for caching and background tasks
5. **Prometheus** and **Grafana** for monitoring

Example production `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    image: your-registry/fileboss:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    networks:
      - fileboss-network

  # ... other services (postgres, redis, etc.)

networks:
  fileboss-network:
    driver: overlay
```

### CI/CD Pipeline

The project includes a GitHub Actions workflow (`.github/workflows/ci-cd.yml`) that:

1. Runs tests on every push and pull request
2. Builds and pushes Docker images to Docker Hub
3. Deploys to staging when pushing to `develop`
4. Deploys to production when pushing to `main`

Required secrets:
- `DOCKERHUB_USERNAME` - Docker Hub username
- `DOCKERHUB_TOKEN` - Docker Hub access token
- `SSH_PRIVATE_KEY` - SSH key for deployment
- `STAGING_*` - Staging environment variables
- `PRODUCTION_*` - Production environment variables

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Example:
```
feat(api): add user authentication endpoint

- Add POST /auth/login endpoint
- Add JWT token generation
- Add API documentation

Closes #123
```

## 📞 Support

For support, please open an issue in the GitHub issue tracker.
