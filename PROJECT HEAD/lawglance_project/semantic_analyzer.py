from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import re
from collections import defaultdict

class SemanticAnalyzer:
    """Provides deep semantic analysis of legal documents using transformer models."""
    
    def __init__(self, model_name="nlpaueb/legal-bert-base-uncased"):
        """Initialize the semantic analyzer with a legal domain model if possible."""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name)
            self.model_loaded = True
            print(f"Initialized semantic analyzer with {model_name}")
        except Exception as e:
            print(f"Could not load {model_name}: {e}")
            try:
                # Fallback to standard BERT
                self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
                self.model = AutoModel.from_pretrained("bert-base-uncased")
                self.model_loaded = True
                print("Falling back to bert-base-uncased")
            except Exception as e:
                print(f"Could not load fallback model: {e}")
                self.model_loaded = False
                
        # Legal domain concepts for topic modeling
        self.legal_areas = {
            "contract_law": ["contract", "agreement", "consideration", "offer", "acceptance", 
                           "breach", "damages", "term", "condition", "covenant", "warranty"],
            "criminal_law": ["crime", "offense", "prosecution", "defendant", "guilty", "innocent", 
                           "prison", "jail", "sentence", "felony", "misdemeanor", "arrest"],
            "constitutional_law": ["constitution", "amendment", "right", "freedom", "liberty", 
                                 "government", "congress", "president", "supreme court", "equal protection"],
            "property_law": ["property", "estate", "land", "deed", "title", "ownership", 
                           "possession", "conveyance", "easement", "mortgage", "lease"],
            "tort_law": ["tort", "negligence", "liability", "damages", "injury", "harm", 
                       "duty", "breach", "causation", "strict liability", "intentional"],
            "administrative_law": ["agency", "regulation", "rule", "administrative", "hearing", 
                                 "adjudication", "regulatory", "commission", "department"],
            "international_law": ["international", "treaty", "convention", "sovereign", "nation", 
                                "diplomatic", "foreign", "jurisdiction", "international court"],
            "intellectual_property": ["patent", "copyright", "trademark", "trade secret", 
                                    "infringement", "license", "royalty", "intellectual property"]
        }
    
    def extract_embeddings(self, text, max_length=512):
        """Extract embeddings from text using transformer model."""
        if not self.model_loaded:
            return None
            
        # Handle texts longer than model's max length by chunking
        if len(text) > 5000:  # Very long text
            chunks = self._split_into_chunks(text, max_length)
            embeddings = []
            
            for chunk in chunks:
                emb = self._get_embedding(chunk)
                if emb is not None:
                    embeddings.append(emb)
                    
            if embeddings:
                # Average the embeddings from all chunks
                return np.mean(embeddings, axis=0)
            return None
        else:
            return self._get_embedding(text)
    
    def _get_embedding(self, text):
        """Get embedding for a single text chunk."""
        try:
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Use the [CLS] token embedding as the sentence embedding
            embedding = outputs.last_hidden_state[:, 0, :].numpy()
            return embedding.flatten()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None
    
    def _split_into_chunks(self, text, max_length):
        """Split text into chunks based on sentences."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # Tokenize to estimate token length (rough approximation)
            tokens = self.tokenizer.tokenize(current_chunk + " " + sentence)
            
            if len(tokens) < max_length - 10:  # Leave some margin
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
            else:
                chunks.append(current_chunk)
                current_chunk = sentence
                
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
    
    def compare_semantic_similarity(self, text1, text2):
        """Compare the semantic similarity between two texts."""
        emb1 = self.extract_embeddings(text1)
        emb2 = self.extract_embeddings(text2)
        
        if emb1 is None or emb2 is None:
            return {"error": "Could not generate embeddings"}
            
        similarity = cosine_similarity([emb1], [emb2])[0][0]
        
        return {
            "similarity_score": float(similarity),
            "percentage": f"{float(similarity) * 100:.2f}%",
            "interpretation": self._interpret_similarity(similarity)
        }
    
    def _interpret_similarity(self, score):
        """Interpret similarity score with legal domain context."""
        if score > 0.95:
            return "Nearly identical legal concepts and language"
        elif score > 0.9:
            return "Very high similarity - likely discussing the same legal points"
        elif score > 0.8:
            return "Strong similarity - closely related legal concepts"
        elif score > 0.7:
            return "Moderate similarity - related legal topics"
        elif score > 0.5:
            return "Some similarity - overlapping legal domains"
        elif score > 0.3:
            return "Limited similarity - different legal areas with some common terms"
        else:
            return "Low similarity - likely different legal domains entirely"
    
    def identify_legal_topics(self, text):
        """Identify legal topics present in the document."""
        text_lower = text.lower()
        topic_scores = {}
        
        # Count occurrences of terms for each legal area
        for area, terms in self.legal_areas.items():
            count = 0
            for term in terms:
                count += len(re.findall(r'\b' + re.escape(term) + r'\b', text_lower))
            
            topic_scores[area] = count
        
        # Calculate relative scores
        total = sum(topic_scores.values()) or 1  # Avoid division by zero
        relative_scores = {area: count / total for area, count in topic_scores.items()}
        
        # Sort by score
        ranked_topics = sorted(relative_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Format results
        result = {
            "primary_topic": ranked_topics[0][0] if ranked_topics[0][1] > 0 else "unknown",
            "topic_distribution": {area: f"{score * 100:.1f}%" for area, score in ranked_topics if score > 0},
            "top_terms": self._extract_top_terms(text, ranked_topics)
        }
        
        return result
    
    def _extract_top_terms(self, text, ranked_topics):
        """Extract top terms from each identified legal topic."""
        text_lower = text.lower()
        top_terms = {}
        
        # Get the top 3 topics
        for area, _ in ranked_topics[:3]:
            terms = self.legal_areas.get(area, [])
            found_terms = []
            
            for term in terms:
                if re.search(r'\b' + re.escape(term) + r'\b', text_lower):
                    found_terms.append(term)
            
            if found_terms:
                top_terms[area] = found_terms[:5]  # Up to 5 terms per area
        
        return top_terms
    
    def extract_legal_arguments(self, text):
        """Extract potential legal arguments from text."""
        if not text:
            return {"error": "No text provided"}

        # Arguments often start with certain phrases
        argument_patterns = [
            r'(?:plaintiff|defendant|petitioner|respondent)(?:\s\w+){0,3}\s(?:argu|content|asser|claim)s?\s+that\s+([^.!?]+[.!?])',
            r'(?:it is|we|the court)\s+(?:argu|content|asser|claim|reason)(?:ed|s)?\s+that\s+([^.!?]+[.!?])',
            r'(?:the|this|such)\s+(?:argu|content|asser|claim)s?\s+that\s+([^.!?]+[.!?])',
            r'(?:according to|in the opinion of)\s+(?:the\s+)?[A-Z][a-z]+(?:\s[A-Z][a-z]+)?,\s+([^.!?]+[.!?])',
        ]

        found_arguments = []

        for pattern in argument_patterns:
            matches = re.findall(pattern, text)
            found_arguments.extend(matches)

        # Additional heuristic for identifying counter-arguments
        counter_patterns = [
            r'(?:however|nevertheless|conversely|on the other hand|in contrast|yet|but),?\s+([^.!?]+[.!?])',
            r'(?:plaintiff|defendant|petitioner|respondent)(?:\s\w+){0,3}\s+counter(?:s|ed)?\s+that\s+([^.!?]+[.!?])'
        ]

        for pattern in counter_patterns:
            matches = re.findall(pattern, text)
            found_arguments.extend(matches)

        if not found_arguments:
            return {"arguments": [], "message": "No specific arguments found."}

        return {"arguments": found_arguments}