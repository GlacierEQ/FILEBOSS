import re
import nltk
from nltk.corpus import wordnet
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from collections import defaultdict, Counter
import networkx as nx

class ConceptExtractor:
    """Extracts and relates concepts from legal documents."""
    
    def __init__(self):
        """Initialize the concept extractor."""
        # Ensure NLTK resources are available
        try:
            nltk.data.find("corpora/stopwords")
        except LookupError:
            nltk.download("stopwords")
        try:
            nltk.data.find("corpora/wordnet")
        except LookupError:
            nltk.download("wordnet")
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt")
        
        self.lemmatizer = WordNetLemmatizer()
        self.stopwords = set(nltk.corpus.stopwords.words('english'))
        
        # Legal concept dictionary with related terms
        self.legal_concepts = {
            "liability": ["responsible", "negligence", "fault", "obligation", "duty"],
            "contract": ["agreement", "offer", "acceptance", "consideration", "term", "clause"],
            "evidence": ["proof", "testimony", "witness", "exhibit", "discovery"],
            "jurisdiction": ["authority", "venue", "court", "forum", "territorial"],
            "damages": ["compensation", "remedy", "award", "relief", "restitution"],
            "property": ["ownership", "possession", "title", "estate", "deed"],
            "rights": ["entitle", "privilege", "claim", "freedom", "liberty"],
            "statute": ["legislation", "law", "enactment", "provision", "code"],
            "tort": ["injury", "harm", "wrongful", "misconduct", "negligence"],
            "procedure": ["process", "motion", "pleading", "filing", "hearing"]
        }
        
        # Expand dictionary with WordNet synonyms
        self._expand_concept_dictionary()
        
    def _expand_concept_dictionary(self):
        """Expand the concept dictionary using WordNet synonyms."""
        expanded_dict = {}
        for concept, terms in self.legal_concepts.items():
            all_terms = set(terms)
            for term in terms:
                for syn in wordnet.synsets(term):
                    for lemma in syn.lemmas():
                        all_terms.add(lemma.name().lower())
            expanded_dict[concept] = list(all_terms)
        self.legal_concepts = expanded_dict
    
    def extract_concepts(self, text):
        """Extract key concepts from the document."""
        if not text or len(text.strip()) < 10:
            return {}
        # Tokenize and preprocess text
        tokens = word_tokenize(text.lower())
        lemmatized = [
            self.lemmatizer.lemmatize(token)
            for token in tokens
            if token.isalpha() and token not in self.stopwords
        ]
        concept_references = defaultdict(list)
        # Get sentences for context
        sentences = nltk.sent_tokenize(text)
        # Check for matches in each sentence
        for sent in sentences:
            sent_lower = sent.lower()
            for concept, synonyms in self.legal_concepts.items():
                if any(syn in sent_lower for syn in synonyms):
                    concept_references[concept].append(sent.strip())
        # Build relationships (placeholder)
        self._build_concept_relationships(concept_references, sentences)
        return concept_references
    
    def _build_concept_relationships(self, concept_references, sentences):
        """Build relationships between concepts based on co-occurrence in sentences."""
        relationships = defaultdict(list)
        for concept1, sentences1 in concept_references.items():
            for concept2, sentences2 in concept_references.items():
                if concept1 != concept2:
                    # Check if concepts co-occur in the same sentences
                    common_sentences = set(sentences1).intersection(sentences2)
                    if common_sentences:
                        relationships[concept1].append({
                            "related_concept": concept2,
                            "sentences": list(common_sentences)
                        })
        return relationships
    
    def explain_concept(self, concept):
        """Return a simple explanation of the concept."""
        # Just an example placeholder
        return f"Explanation for {concept} might describe legal definitions and context."
