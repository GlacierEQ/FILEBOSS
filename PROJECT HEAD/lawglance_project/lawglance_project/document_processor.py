"""
Enhanced document processing with improved chunking and caching.
"""
import os
import logging
from typing import Dict, Any, List, Optional, Tuple
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from document_cache import DocumentCache

class DocumentProcessor:
    """Enhanced document processor with improved chunking and caching."""
    
    def __init__(self, config, word_processor, doc_analyzer, concept_extractor, cache=None):
        """Initialize the document processor.
        
        Args:
            config: Configuration object
            word_processor: Word processor for reading documents
            doc_analyzer: Document analyzer for analyzing content
            concept_extractor: Concept extractor for extracting concepts
            cache: Optional document cache
        """
        self.config = config
        self.word_processor = word_processor
        self.doc_analyzer = doc_analyzer
        self.concept_extractor = concept_extractor
        
        # Initialize cache or use provided one
        self.cache = cache or DocumentCache(config)
        
        # Get configuration values
        self.chunk_size = config.get("document_processing", "chunk_size")
        self.chunk_overlap = config.get("document_processing", "chunk_overlap")
        self.max_document_size = config.get("document_processing", "max_document_size")
        
        # Set up logging
        self.logger = logging.getLogger("lawglance.document_processor")
    
    def process_document(self, file_path: str, analyze: bool = False) -> Dict[str, Any]:
        """Process a document with caching and optional analysis.
        
        Args:
            file_path: Path to the document
            analyze: If True, performs deep analysis on the document
            
        Returns:
            Document content and optional analysis
        """
        # Check if document exists
        if not os.path.exists(file_path):
            self.logger.error(f"Document not found: {file_path}")
            return {"error": f"Document not found: {file_path}"}
        
        # Check if file is too large
        if os.path.getsize(file_path) > self.max_document_size:
            self.logger.warning(f"Document too large: {file_path}")
            return {"error": f"Document too large (max {self.max_document_size/1000000:.1f}MB)"}
        
        # Check cache for content
        content = self.cache.get_document_content(file_path)
        
        if content is None:
            # Read document content
            try:
                self.logger.info(f"Reading document: {file_path}")
                content = self.word_processor.read_document(file_path)
                
                # Cache content
                self.cache.cache_document_content(file_path, content)
            except Exception as e:
                self.logger.error(f"Error reading document: {str(e)}")
                return {"error": f"Error reading document: {str(e)}"}
        
        # If no analysis requested, just return content
        if not analyze:
            return {"content": content}
        
        # Check cache for analysis
        analysis = self.cache.get_document_analysis(file_path)
        
        if analysis is None:
            try:
                # Perform deeper document analysis
                self.logger.info(f"Analyzing document: {file_path}")
                doc_analysis = self.doc_analyzer.analyze(content)
                key_concepts = self.concept_extractor.extract_concepts(content)
                
                analysis = {
                    "summary": doc_analysis["summary"],
                    "key_points": doc_analysis["key_points"],
                    "concepts": key_concepts,
                    "complexity_score": doc_analysis["complexity_score"],
                    "document_type": doc_analysis["document_type"]
                }
                
                # Cache analysis
                self.cache.cache_document_analysis(file_path, analysis)
            except Exception as e:
                self.logger.error(f"Error analyzing document: {str(e)}")
                analysis = {"error": f"Error analyzing document: {str(e)}"}
        
        # Return content and analysis
        return {
            "content": content,
            **analysis
        }
    
    def chunk_document(self, text: str, chunk_size: Optional[int] = None, 
                      chunk_overlap: Optional[int] = None) -> List[Dict[str, Any]]:
        """Chunk document with overlap between chunks.
        
        Args:
            text: Document text
            chunk_size: Maximum chunk size (optional, defaults to config value)
            chunk_overlap: Overlap between chunks (optional, defaults to config value)
            
        Returns:
            List of chunks with metadata
        """
        # Use provided values or defaults from config
        chunk_size = chunk_size or self.chunk_size
        chunk_overlap = chunk_overlap or self.chunk_overlap
        
        if not text or len(text.strip()) < chunk_size:
            # Return single chunk for small documents
            return [{"text": text, "chunk_id": 0, "start_char": 0, "end_char": len(text)}]
        
        # Split text into sentences for better chunking
        try:
            sentences = sent_tokenize(text)
        except LookupError:
            # Download NLTK resources if needed
            nltk.download('punkt')
            sentences = sent_tokenize(text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_id = 0
        last_end = 0
        
        for sentence in sentences:
            # Calculate sentence length (approximate token count)
            sentence_size = len(word_tokenize(sentence))
            
            # If adding this sentence would exceed chunk size, start a new chunk
            if current_size + sentence_size > chunk_size and current_chunk:
                # Track document positions
                chunk_text = " ".join(current_chunk)
                start_char = text.find(current_chunk[0], last_end)
                end_char = start_char + len(chunk_text)
                
                chunks.append({
                    "text": chunk_text,
                    "chunk_id": chunk_id,
                    "start_char": start_char,
                    "end_char": end_char
                })
                
                # For overlap, keep some sentences from the end of the previous chunk
                overlap_count = 0
                overlap_size = 0
                for s in reversed(current_chunk):
                    s_size = len(word_tokenize(s))
                    if overlap_size + s_size <= chunk_overlap:
                        overlap_count += 1
                        overlap_size += s_size
                    else:
                        break
                
                # Start new chunk with overlap sentences
                current_chunk = current_chunk[-overlap_count:] if overlap_count > 0 else []
                current_size = overlap_size
                chunk_id += 1
                last_end = end_char - len(" ".join(current_chunk))
            
            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_size += sentence_size
        
        # Add the last chunk if not empty
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            start_char = text.find(current_chunk[0], last_end)
            end_char = start_char + len(chunk_text)
            
            chunks.append({
                "text": chunk_text,
                "chunk_id": chunk_id,
                "start_char": start_char,
                "end_char": end_char
            })
        
        return chunks
    
    def process_question_on_document(self, question: str, file_path: str, 
                                   qa_pipeline) -> Dict[str, Any]:
        """Process a question on a document with chunking and answer synthesis.
        
        Args:
            question: Question to answer
            file_path: Path to the document
            qa_pipeline: QA pipeline for answering
            
        Returns:
            Answer with metadata
        """
        # Process document to get content
        doc_result = self.process_document(file_path, analyze=False)
        
        if "error" in doc_result:
            return doc_result
        
        content = doc_result["content"]
        
        # Chunk document
        chunks = self.chunk_document(content)
        
        if len(chunks) == 1:
            # For single chunk, just use the QA pipeline directly
            result = qa_pipeline(question=question, context=content)
            return {
                "answer": result["answer"],
                "confidence": result["score"],
                "source": file_path,
                "chunk_count": 1
            }
        
        # Process each chunk
        answers = []
        confidences = []
        source_chunks = []
        
        for i, chunk in enumerate(chunks):
            # Get answer for this chunk
            try:
                result = qa_pipeline(question=question, context=chunk["text"])
                answers.append(result["answer"])
                confidences.append(result["score"])
                source_chunks.append(i)
            except Exception as e:
                self.logger.warning(f"Error processing chunk {i}: {str(e)}")
                continue
        
        if not answers:
            return {"error": "Could not generate answer from document"}
        
        # Select best answer
        best_idx = confidences.index(max(confidences))
        best_answer = answers[best_idx]
        best_chunk = source_chunks[best_idx]
        
        # Include top 3 answers for inspection
        top_indices = sorted(range(len(confidences)), key=lambda i: confidences[i], reverse=True)[:3]
        top_answers = [(answers[i], confidences[i]) for i in top_indices]
        
        return {
            "answer": best_answer,
            "confidence": confidences[best_idx],
            "source": file_path,
            "chunk_count": len(chunks),
            "top_answers": top_answers,
            "source_chunk": best_chunk
        }
