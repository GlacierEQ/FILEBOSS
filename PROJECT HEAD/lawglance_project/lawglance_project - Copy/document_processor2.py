"""
Enhanced document processing with improved chunking and caching.
"""
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from ..core.document_cache import DocumentCache

class DocumentProcessor:
    # ...existing code...
