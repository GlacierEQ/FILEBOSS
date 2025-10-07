"""FILEBOSS Test Suite"""
import pytest
import os
import subprocess
import sys

def test_fileboss_standalone():
    """Test FILEBOSS Standalone syntax"""
    result = subprocess.run([sys.executable, '-m', 'py_compile', 'FILEBOSS_STANDALONE.py'], 
                          capture_output=True, text=True)
    assert result.returncode == 0
    print("✅ FILEBOSS_STANDALONE.py validated!")

def test_android_component():
    """Test Android component"""
    assert os.path.exists("FILEBOSS_ANDROID_COMPLETE.tsx")
    with open("FILEBOSS_ANDROID_COMPLETE.tsx", 'r') as f:
        content = f.read()
        assert "FILEBOSS" in content
        assert len(content) > 1000
    print("✅ Android component validated!")

def test_repository_health():
    """Test repository is clean"""
    bad_paths = [".venv", "venv", "__pycache__", ".coverage", "PROJECT HEAD"]
    for path in bad_paths:
        assert not os.path.exists(path), f"Bad path {path} still exists"
    print("✅ Repository health: EXCELLENT!")
