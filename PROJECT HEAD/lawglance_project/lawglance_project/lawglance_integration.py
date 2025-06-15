"""
Integration module to connect enhanced components with Lawglance.

This module provides convenience functions to initialize and connect
the improved document processing, caching, and configuration components
with the main Lawglance system.
"""
import os
import logging
from typing import Optional, Dict, Any

from config import Config
from document_cache import DocumentCache
from document_processor import DocumentProcessor

class LawglanceIntegration:
    """Integration helper for Lawglance system with enhanced components."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the integration helper.
        
        Args:
            config_path: Path to configuration file (optional)
        """
        # Initialize configuration
        self.config = Config(config_path)
        
        # Set up logging
        logging_config = self.config.get("logging")
        self.logger = logging.getLogger("lawglance.integration")
        
        # Initialize cache
        self.cache = DocumentCache(self.config)
        
        self.logger.info("LawglanceIntegration initialized")
    
    def setup_lawglance(self, lawglance, word_processor=None, doc_analyzer=None, concept_extractor=None):
        """Set up Lawglance with enhanced components.
        
        Args:
            lawglance: Lawglance instance
            word_processor: Optional word processor (uses lawglance's if None)
            doc_analyzer: Optional document analyzer (uses lawglance's if None)
            concept_extractor: Optional concept extractor (uses lawglance's if None)
            
        Returns:
            Updated Lawglance instance
        """
        # Use provided components or get from lawglance
        word_processor = word_processor or lawglance.word_processor
        doc_analyzer = doc_analyzer or lawglance.doc_analyzer
        concept_extractor = concept_extractor or lawglance.concept_extractor
        
        # Create document processor
        self.doc_processor = DocumentProcessor(
            self.config,
            word_processor,
            doc_analyzer,
            concept_extractor,
            self.cache
        )
        
        # Update Lawglance methods to use enhanced components
        self._enhance_process_document(lawglance)
        self._enhance_generate_answer(lawglance)
        
        self.logger.info("Lawglance enhanced with improved document processing and caching")
        
        return lawglance
    
    def _enhance_process_document(self, lawglance):
        """Replace Lawglance's process_document with enhanced version.
        
        Args:
            lawglance: Lawglance instance
        """
        # Store original method for reference
        lawglance._original_process_document = lawglance.process_document
        
        # Replace with enhanced method
        def enhanced_process_document(file_path, analyze=False):
            self.logger.info(f"Enhanced process_document called for {file_path}")
            return self.doc_processor.process_document(file_path, analyze)
        
        lawglance.process_document = enhanced_process_document
    
    def _enhance_generate_answer(self, lawglance):
        """Replace Lawglance's generate_answer with enhanced version.
        
        Args:
            lawglance: Lawglance instance
        """
        # Store original method for reference
        lawglance._original_generate_answer = lawglance.generate_answer
        
        # Replace with enhanced method
        def enhanced_generate_answer(context, question):
            self.logger.info("Enhanced generate_answer called")
            
            # If context is a file path, use process_question_on_document
            if os.path.exists(context):
                result = self.doc_processor.process_question_on_document(
                    question, context, lawglance.qa_pipeline
                )
                return result["answer"] if "answer" in result else str(result)
            
            # Otherwise use the document processor's chunking
            chunks = self.doc_processor.chunk_document(
                context,
                self.config.get("document_processing", "chunk_size"),
                self.config.get("document_processing", "chunk_overlap")
            )
            
            if len(chunks) == 1:
                # For single chunk, just use the QA pipeline directly
                result = lawglance.qa_pipeline(question=question, context=context)
                return result["answer"]
            
            # Process each chunk
            answers = []
            confidences = []
            
            for chunk in chunks:
                # Get answer for this chunk
                try:
                    result = lawglance.qa_pipeline(question=question, context=chunk["text"])
                    answers.append(result["answer"])
                    confidences.append(result["score"])
                except Exception as e:
                    self.logger.warning(f"Error processing chunk: {str(e)}")
                    continue
            
            if not answers:
                return "Could not generate answer from document"
            
            # Return best answer
            best_idx = confidences.index(max(confidences))
            return answers[best_idx]
        
        lawglance.generate_answer = enhanced_generate_answer
