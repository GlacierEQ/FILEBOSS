# Contributing to FILEBOSS

Thank you for your interest in contributing to FILEBOSS! This document provides guidelines and instructions for contributing.

## 🌟 Ways to Contribute

- **Report Bugs**: Use the bug report template to report issues
- **Suggest Features**: Use the feature request template for new ideas
- **Submit Pull Requests**: Fix bugs or implement features
- **Improve Documentation**: Help make our docs better
- **Review Pull Requests**: Provide feedback on others' contributions
- **Answer Questions**: Help other users in issues and discussions

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Familiarity with FastAPI and SQLAlchemy (for backend work)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/glaciereq/FILEBOSS.git
cd FILEBOSS

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest
```

## 📝 Development Workflow

### 1. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or a bugfix branch
git checkout -b fix/bug-description
```

### 2. Make Your Changes

- Write clean, readable code
- Follow PEP 8 style guidelines
- Add type hints to all functions
- Write comprehensive docstrings
- Add tests for new functionality

### 3. Test Your Changes

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=casebuilder

# Run linting
ruff check .
black --check .
isort --check .
mypy casebuilder
```

### 4. Commit Your Changes

We use conventional commits for clear history:

```bash
# Format: type(scope): description
git commit -m "feat(api): add user authentication endpoint"
git commit -m "fix(database): resolve connection pool issue"
git commit -m "docs(readme): update installation instructions"
```

**Commit Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions or changes
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

### 5. Push and Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create a pull request on GitHub
# Fill out the PR template completely
```

## 🎨 Code Style

### Python Style Guide

- Follow PEP 8
- Use Black for formatting (line length: 100)
- Use isort for import sorting
- Add type hints to all functions
- Write docstrings in Google style

### Example Code Style

```python
from typing import Optional, List
from pydantic import BaseModel


class User(BaseModel):
    """User model for authentication.
    
    Attributes:
        id: Unique user identifier
        username: User's username
        email: User's email address
        is_active: Whether the user account is active
    """
    
    id: int
    username: str
    email: str
    is_active: bool = True
    
    def validate_email(self) -> bool:
        """Validate the user's email address.
        
        Returns:
            True if email is valid, False otherwise
            
        Raises:
            ValueError: If email format is invalid
        """
        # Implementation
        pass
```

## 🧪 Testing Guidelines

### Writing Tests

- Write tests for all new features
- Maintain at least 80% code coverage
- Use pytest fixtures for setup/teardown
- Mock external dependencies
- Test edge cases and error conditions

### Test Structure

```python
import pytest
from casebuilder.models import User


class TestUser:
    """Test suite for User model."""
    
    @pytest.fixture
    def user(self):
        """Create a test user."""
        return User(
            id=1,
            username="testuser",
            email="test@example.com"
        )
    
    def test_user_creation(self, user):
        """Test user can be created with valid data."""
        assert user.username == "testuser"
        assert user.is_active is True
    
    def test_email_validation(self, user):
        """Test email validation logic."""
        assert user.validate_email() is True
```

## 📚 Documentation

### Docstring Format

Use Google-style docstrings:

```python
def process_file(file_path: str, encoding: str = "utf-8") -> dict:
    """Process a file and return its metadata.
    
    Args:
        file_path: Path to the file to process
        encoding: Character encoding of the file (default: utf-8)
        
    Returns:
        Dictionary containing file metadata:
        - name: File name
        - size: File size in bytes
        - modified: Last modified timestamp
        
    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If encoding is invalid
        
    Example:
        >>> metadata = process_file("/path/to/file.txt")
        >>> print(metadata['name'])
        'file.txt'
    """
    pass
```

### README Updates

- Update README.md if you add new features
- Include usage examples
- Update API documentation links
- Add screenshots for UI changes

## 🔒 Security

### Security Best Practices

- Never commit secrets, API keys, or passwords
- Use environment variables for sensitive data
- Validate and sanitize all user inputs
- Use parameterized queries for database operations
- Keep dependencies up to date

### Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. Email security concerns to: [security email]
3. Include detailed information about the vulnerability
4. Allow time for the issue to be fixed before public disclosure

## 📋 Pull Request Review Process

### What Reviewers Look For

- Code quality and readability
- Test coverage
- Documentation completeness
- Performance implications
- Security considerations
- Breaking changes
- Backward compatibility

### Review Timeline

- Initial review: Within 2-3 business days
- Follow-up reviews: Within 1-2 business days
- Merge: After approval from at least one maintainer

## 🤝 Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Provide constructive feedback
- Focus on the issue, not the person
- Assume good intentions

### Getting Help

- **Questions**: Open a discussion or issue
- **Chat**: [Discord/Slack link if available]
- **Email**: [Contact email]

## 🏆 Recognition

Contributors are recognized in:
- README.md contributors section
- Release notes
- GitHub contributors page

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

Thank you for contributing to FILEBOSS! Your efforts help make this project better for everyone. 🚀
