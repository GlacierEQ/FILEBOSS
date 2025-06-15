"""
Tests for the FastAPI application.
"""
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import app after path is set
from app import app, verify_api_key


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_model():
    """Mock the model and tokenizer to avoid loading real models during tests."""
    with patch('app.load_model') as _:
        with patch('app.model') as mock_model:
            with patch('app.tokenizer') as mock_tokenizer:
                # Configure mock model
                mock_outputs = MagicMock()
                mock_model.generate.return_value = mock_outputs
                mock_tokenizer.decode.return_value = "def test_function():\n    return 'Hello, World!'"
                mock_tokenizer.encode.return_value = [1, 2, 3, 4, 5]  # Dummy token IDs
                
                yield


@pytest.fixture
def mock_auth():
    """Disable authentication for tests."""
    with patch('app.ENABLE_AUTH', False):
        yield


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "ok"


@pytest.mark.usefixtures("mock_model", "mock_auth")
def test_completion_endpoint(client):
    """Test the code completion endpoint."""
    test_data = {
        "prompt": "def hello_world():",
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    response = client.post("/api/v1/completion", json=test_data)
    assert response.status_code == 200
    
    response_data = response.json()
    assert "choices" in response_data
    assert len(response_data["choices"]) > 0
    assert "text" in response_data["choices"][0]
    assert "usage" in response_data


@pytest.mark.usefixtures("mock_model", "mock_auth")
def test_insertion_endpoint(client):
    """Test the code insertion endpoint."""
    test_data = {
        "prefix": "def hello_world():",
        "suffix": "    return greeting",
        "max_tokens": 50
    }
    
    response = client.post("/api/v1/insertion", json=test_data)
    assert response.status_code == 200
    
    response_data = response.json()
    assert "choices" in response_data
    assert len(response_data["choices"]) > 0
    assert "text" in response_data["choices"][0]


@pytest.mark.usefixtures("mock_model", "mock_auth")
def test_chat_endpoint(client):
    """Test the chat endpoint."""
    test_data = {
        "messages": [
            {"role": "user", "content": "Write a Python function to calculate factorial"}
        ],
        "max_tokens": 100
    }
    
    response = client.post("/api/v1/chat", json=test_data)
    assert response.status_code == 200
    
    response_data = response.json()
    assert "choices" in response_data
    assert len(response_data["choices"]) > 0
    assert "message" in response_data["choices"][0]
    assert "content" in response_data["choices"][0]["message"]


def test_api_key_validation():
    """Test the API key validation function."""
    with patch('app.ENABLE_AUTH', True):
        with patch('app.API_KEYS', ["test_key"]):
            # Valid API key
            assert verify_api_key("Bearer test_key") is True
            
            # Invalid API key should raise an exception
            with pytest.raises(Exception):
                verify_api_key("Bearer invalid_key")
            
            # Missing API key should raise an exception
            with pytest.raises(Exception):
                verify_api_key(None)
