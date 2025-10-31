import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class MCPSettings(BaseSettings):
    """Application settings for the MCP Ecosystem, loaded from environment variables."""
    
    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

    # General Application Settings
    APP_NAME: str = "WindsurfMCP"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Database Configuration
    DATABASE_TYPE: str = "postgresql"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "windsurf_mcp_db"
    DATABASE_USER: str = "mcp_user"
    DATABASE_PASSWORD: str = "super_secret_db_password"
    DATABASE_URL: str = (
        f"{DATABASE_TYPE}://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
    )

    # API Keys & External Service Integrations
    EXTERNAL_API_KEY: str = "your_external_api_key_here"
    AUTH_SECRET_KEY: str = "super_secret_auth_key_for_jwt_or_sessions"

    # Observability - Logging
    LOG_COLLECTOR_URL: str = "http://localhost:3100/loki/api/v1/push"
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_SERVICE_NAME: str = "windsurf-mcp-service"

    # Observability - Metrics
    METRICS_COLLECTOR_URL: str = "http://localhost:9091/metrics/job/windsurf-mcp-app"
    METRICS_ENABLED: bool = True
    METRICS_INTERVAL_SECONDS: int = 15

    # Observability - Tracing
    TRACING_COLLECTOR_HOST: str = "localhost"
    TRACING_COLLECTOR_PORT: int = 4317
    TRACING_ENABLED: bool = True
    TRACING_SERVICE_NAME: str = "windsurf-mcp-tracer"
    TRACING_EXPORTER_PROTOCOL: str = "grpc"

    # Cloud Provider Credentials (Example for AWS)
    AWS_ACCESS_KEY_ID: str = "YOUR_AWS_ACCESS_KEY_ID"
    AWS_SECRET_ACCESS_KEY: str = "YOUR_AWS_SECRET_ACCESS_KEY"
    AWS_REGION: str = "us-east-1"

    # Secrets Management (e.g., HashiCorp Vault)
    VAULT_ADDR: str = "http://127.0.0.1:8200"
    VAULT_TOKEN: str = "your_vault_token"
    VAULT_PATH: str = "secret/data/windsurf-mcp/app"

    # Docker / Container Orchestration
    DOCKER_REGISTRY_USERNAME: str = "your_docker_username"
    DOCKER_REGISTRY_PASSWORD: str = "your_docker_password"
    DOCKER_IMAGE_TAG: str = "latest"

    # AI / ML Integrations
    OPENAI_API_KEY: str = "your_openai_api_key"
    HUGGINGFACE_API_TOKEN: str = "your_huggingface_api_token"
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"

    # CI/CD Specific (GitHub Actions, Jenkins, GitLab CI)
    CI_COMMIT_SHA: str = "unknown"
    CI_RUN_ID: str = "unknown"
    CI_WORKFLOW_NAME: str = "unknown"

# Use lru_cache for efficient settings loading
@lru_cache
def get_settings():
    """Returns a cached instance of application settings."""
    return MCPSettings()

# Example usage:
if __name__ == "__main__":
    settings = get_settings()
    print(f"App Name: {settings.APP_NAME}")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Log Level: {settings.LOG_LEVEL}")
    print(f"Tracing Enabled: {settings.TRACING_ENABLED}")
    
    # To test loading from .env:
    # Create a file named .env in the same directory as this script with:
    # APP_ENV=test
    # LOG_LEVEL=DEBUG
    # python -m pip install python-dotenv
    # then run this script.
