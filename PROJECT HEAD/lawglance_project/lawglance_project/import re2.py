import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import spacy
from textstat import textstat

class DocumentAnalyzer:
    """Analyzes legal documents for deeper understanding and comparison."""
    
    # ...existing code...
