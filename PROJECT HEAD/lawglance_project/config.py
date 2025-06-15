"""
Configuration management for Lawglance system.
Centralizes all configurable parameters and provides loading/saving functionality.
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
