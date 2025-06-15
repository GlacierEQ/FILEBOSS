"""Unit tests for config_manager.py."""
import os
import json
import pytest
from pathlib import Path
from src.utils.config_manager import ConfigManager

class TestConfigManager:
    """Test suite for ConfigManager class."""

    @pytest.fixture
    def temp_config_dir(self, tmp_path):
        """Temporary directory for config files."""
        return tmp_path / "config"

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """ConfigManager instance with temporary directory."""
        return ConfigManager(config_dir=str(temp_config_dir))

    def test_initialization(self, config_manager, temp_config_dir):
        """Test ConfigManager initialization."""
        assert config_manager.config_dir == temp_config_dir
        assert config_manager.config_file == "config.json"
        assert config_manager.config_path == temp_config_dir / "config.json"
        assert isinstance(config_manager.config, dict)
        assert temp_config_dir.exists()

    def test_load_config(self, config_manager, temp_config_dir):
        """Test loading configuration from file."""
        # Create test config file
        test_config = {"key": "value"}
        with open(config_manager.config_path, "w") as f:
            json.dump(test_config, f)

        # Test loading
        assert config_manager.load_config() is True
        assert config_manager.config == test_config

    def test_load_missing_config(self, config_manager):
        """Test loading when config file doesn't exist."""
        assert config_manager.load_config() is False
        assert config_manager.config == {}

    def test_save_config(self, config_manager, temp_config_dir):
        """Test saving configuration to file."""
        test_config = {"key": "value"}
        config_manager.config = test_config

        assert config_manager.save_config() is True
        assert config_manager.config_path.exists()

        with open(config_manager.config_path, "r") as f:
            assert json.load(f) == test_config

    def test_get_set(self, config_manager):
        """Test getting and setting configuration values."""
        # Test getting non-existent key
        assert config_manager.get("non_existent") is None
        assert config_manager.get("non_existent", "default") == "default"

        # Test setting and getting value
        config_manager.set("test_key", "test_value")
        assert config_manager.get("test_key") == "test_value"

    def test_update(self, config_manager):
        """Test updating multiple configuration values."""
        config_manager.update({
            "key1": "value1",
            "key2": "value2"
        })

        assert config_manager.get("key1") == "value1"
        assert config_manager.get("key2") == "value2"

    def test_reset(self, config_manager):
        """Test resetting configuration."""
        config_manager.config = {"key": "value"}
        config_manager.reset()

        assert config_manager.config == {}
        assert config_manager.config_path.exists()
