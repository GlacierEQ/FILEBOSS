"""
Pytest configuration file with shared fixtures.
"""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
import torch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session")
def mock_cuda():
    """Mock CUDA availability."""
    with patch("torch.cuda.is_available", return_value=True):
        with patch("torch.cuda.device_count", return_value=1):
            with patch("torch.cuda.get_device_name", return_value="NVIDIA Mock GPU"):
                yield


@pytest.fixture
def mock_models():
    """Create mock models and tokenizers for testing."""
    # Mock tokenizer
    tokenizer = MagicMock()
    tokenizer.encode.return_value = [101, 102, 103, 104, 105]  # Sample token IDs
    tokenizer.decode.return_value = "Sample decoded text"
    tokenizer.eos_token_id = 102
    tokenizer.apply_chat_template.return_value = torch.tensor([[101, 102, 103]])
    
    # Mock model
    model = MagicMock()
    outputs = MagicMock()
    outputs.hidden_states = [torch.zeros(1, 1, 768)]
    model.generate.return_value = torch.tensor([[101, 102, 103, 104, 105]])
    model.device = "cuda:0"
    model.return_value = outputs
    
    return model, tokenizer


@pytest.fixture
def sample_dataset():
    """Create a sample dataset for testing."""
    return [
        {"instruction": "Write a function to calculate factorial", "output": "def factorial(n):\n    if n == 0:\n        return 1\n    return n * factorial(n-1)"},
        {"instruction": "Implement binary search", "output": "def binary_search(arr, target):\n    left, right = 0, len(arr) - 1\n    while left <= right:\n        mid = (left + right) // 2\n        if arr[mid] == target:\n            return mid\n        elif arr[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1"}
    ]


# Mark tests that require GPU
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "gpu: mark test as requiring GPU")
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    """Skip GPU tests if no GPU is available."""
    if not torch.cuda.is_available():
        skip_gpu = pytest.mark.skip(reason="Test requires GPU")
        for item in items:
            if "gpu" in item.keywords:
                item.add_marker(skip_gpu)
