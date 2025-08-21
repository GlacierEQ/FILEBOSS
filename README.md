# FILEBOSS - Digital Evidence Management System

FILEBOSS is an advanced digital evidence management system designed for legal, investigative, and forensic professionals. It provides a robust platform for collecting, processing, organizing, and analyzing digital evidence while maintaining a secure chain of custody and comprehensive timeline of events.

## ✨ Features

- **Evidence Management**: Track and manage digital evidence with full audit trails and chain of custody
- **Automated File Processing**: Extract metadata, generate hashes, and process various file types
- **Timeline Integration**: Link evidence to timeline events for comprehensive case analysis
- **Secure Access**: JWT authentication with role-based access control
- **Containerized Deployment**: Easy deployment with Docker and Docker Compose
- **CI/CD Pipeline**: Automated testing and deployment with GitHub Actions
- **RESTful API**: Built with FastAPI for high performance and easy integration
- **Database Migrations**: Alembic for database versioning and schema management

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- Python 3.10+ (for development)
- PostgreSQL 14+ (included in Docker)
- Redis 7+ (included in Docker)

## 🛠 Installation

### With Docker (Recommended)

1. Clone the repository:

   ```bash
   git clone https://github.com/your-username/FILEBOSS.git
   cd FILEBOSS
   ```

2. Copy the example environment file and configure it:

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Start the application with Docker Compose:

   ```bash
   docker-compose up -d
   ```

4. Initialize the database:
   ```bash
   docker-compose exec app python scripts/init_db.py
   ```

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
#

### Production Deployment

For production deployments, we recommend using:

1. **Docker Swarm** or **Kubernetes** for container orchestration
2. **Traefik** or **Nginx** as reverse proxy with Let's Encrypt
3. **PostgreSQL** with replication and backups
4. **Redis** for caching and background tasks
5. **Prometheus** and **Grafana** for monitoring

Example production `docker-compose.prod.yml`:

```yaml
version: "3.8"

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

## 🔮 Codex Resonator Plugin

The optional Codex Resonator plugin helps you generate "resonator scrolls" that
summarize a repository and suggest future improvements.

### Usage

1. (Optional) Install the OpenAI client if you want AI-generated insights:
   ```bash
   pip install openai
   ```
2. Run the plugin:
   ```bash
   python -m plugins.codex_resonator <path-to-repo> --output-dir ./scrolls --openai
   ```
   Omit `--openai` to generate a scroll using only README content.

   When using the `--openai` flag, set your API key with the `OPENAI_API_KEY` environment variable.

The generated scroll will appear in the chosen output directory.

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
 Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Run database migrations
docker-compose exec app alembic upgrade head

# Initialize database
docker-compose exec app python scripts/init_db.py
```
