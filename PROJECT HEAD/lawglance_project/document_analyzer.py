import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import spacy
from textstat import textstat
import logging

class DocumentAnalyzer:
    """Analyzes legal documents for deeper understanding and comparison."""
    
    def __init__(self, embeddings=None):
        """Initialize the document analyzer.
        
        Args:
            embeddings: Optional embeddings model for semantic analysis
        """
        self.embeddings = embeddings
        self.vectorizer = TfidfVectorizer()
        self.nlp = None
        self.logger = logging.getLogger("lawglance.document_analyzer")
        
        try:
            # Load English language model with NER capabilities
            self.nlp = spacy.load("en_core_web_lg")
        except Exception as e:
            self.logger.warning(f"Could not load large model: {e}")
            try:
                self.nlp = spacy.load("en_core_web_sm")
                self.logger.info("Using smaller language model. For better results install: python -m spacy download en_core_web_lg")
            except Exception as e:
                self.logger.error(f"Spacy model not available: {e}")
        
        # Legal document classification patterns
        self.document_patterns = {
            "contract": ["agreement", "parties", "terms", "obligations", "hereby agrees", 
                         "in witness whereof", "consideration", "hereinafter"],
            "statute": ["section", "subsection", "paragraph", "legislature", "enacted", 
                        "provision", "amendment", "shall be", "pursuant to"],
            "court_decision": ["plaintiff", "defendant", "petitioner", "respondent", "court", 
                              "judge", "ruling", "opinion", "held that", "judgment"],
            "legal_memo": ["memorandum", "issue", "brief", "analysis", "conclusion", 
                          "recommendation", "matter", "advise"],
        }
        
        # Legal entity categories
        self.legal_entities = {
            "PERSON": [],
            "ORG": [],
            "DATE": [],
            "GPE": [],  # Countries, cities, etc.
            "LAW": [],
            "LEGAL_TERM": []
        }
        
        # Common legal terms regex
        self.legal_terms_pattern = re.compile(
            r'\b(plaintiff|defendant|court|judge|statute|regulation|'
            r'provision|clause|contract|agreement|stipulation|'
            r'jurisdiction|testimony|evidence|exhibit|'
            r'objection|indemnity|warranty|verdict|ruling|'
            r'motion|appeal|petitioner|respondent|settlement)\b',
            re.IGNORECASE
        )

    def analyze(self, text):
        """Analyze the document and return summary, key points, complexity, and type."""
        if not text or len(text.strip()) < 30:
            return {"summary": "Document too short to analyze", "key_points": [], "complexity_score": 0, "document_type": "unknown"}

        # Basic reading ease metrics
        try:
            complexity_score = textstat.flesch_reading_ease(text)
        except Exception as e:
            complexity_score = 50  # Default value
            self.logger.warning(f"Error calculating complexity: {e}")

        # Simple summary by taking first few lines
        summary = "\n".join(text.split('\n')[:3])

        # Extract some key points by top TF-IDF terms
        try:
            tokens = self.vectorizer.fit_transform([text])
            feature_names = self.vectorizer.get_feature_names_out()
            scores = zip(feature_names, tokens.toarray()[0])
            sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)[:5]
            key_points = [term for term, score in sorted_scores]
        except Exception as e:
            key_points = ["Could not extract key points"]
            self.logger.error(f"Error extracting key points: {e}")

        # Naive classification based on keywords
        doc_type = "General Legal Document"
        try:
            text_lower = text.lower()
            if any(keyword in text_lower for keyword in ["contract", "agreement", "terms", "obligations"]):
                doc_type = "Contract Document"
            elif any(keyword in text_lower for keyword in ["statute", "regulation", "code", "law"]):
                doc_type = "Statutory Document"
            elif any(keyword in text_lower for keyword in ["court", "judge", "ruling", "judgment"]):
                doc_type = "Court Decision"
        except Exception as e:
            self.logger.error(f"Error classifying document type: {e}")

        return {
            "summary": summary,
            "key_points": key_points,
            "complexity_score": complexity_score,
            "document_type": doc_type
        }

    def compare_documents(self, text1, text2):
        """Compare two documents and return basic similarity scores."""
        if not text1 or not text2:
            return {"similarity": 0.0, "details": "One or both documents are empty"}
        # Calculate TF-IDF similarity
        docs = [text1, text2]
        tfidf_matrix = self.vectorizer.fit_transform(docs)
        sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        return {"similarity": round(float(sim), 2)}

    def extract_legal_entities(self, text):
        """Extract naive placeholders for legal entities."""
        if not text or len(text.strip()) < 10:
            return {}
        # Very simplistic entity extraction by capital words
        words = text.split()
        capitalized = [w for w in words if w[:1].isupper() and len(w) > 3]
        return {"entities": Counter(capitalized)}
