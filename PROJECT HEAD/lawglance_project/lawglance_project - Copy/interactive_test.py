"""This file provides interactive testing capabilities for Lawglance components.
Run this in VS Code's interactive window to test individual components.
"""

import os
import sys
import traceback
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lawglance.interactive_test")

# Set environment variables and paths
os.environ["HUGGINGFACE_API_TOKEN"] = os.getenv("HUGGINGFACE_API_TOKEN", "YOUR_DEFAULT_TOKEN")

# Add project path - adjust if needed
project_path = r"C:/Users/casey/OneDrive/Documents/GitHub/lawglance"
if project_path not in sys.path:
    sys.path.append(project_path)

def test_document_analyzer():
    """Test the document analyzer component."""
    try:
        from document_analyzer import DocumentAnalyzer
        
        logger.info("Creating test document...")
        with open("test_legal_doc.txt", "w") as f:
            f.write("This contract is made between Party A and Party B.\n")
            f.write("The parties hereby agree to the following terms and conditions:\n")
            f.write("1. Party A shall deliver the goods within 30 days.\n")
            f.write("2. Party B shall make payment within 15 days of delivery.\n")
        
        logger.info("Initializing DocumentAnalyzer...")
        analyzer = DocumentAnalyzer()
        
        logger.info("Analyzing document...")
        with open("test_legal_doc.txt", "r") as f:
            content = f.read()
            result = analyzer.analyze(content)
        
        logger.info("Analysis result:")
        for key, value in result.items():
            logger.info(f"{key}: {value}")
        
        return result
    except Exception as e:
        logger.error(f"Error in test_document_analyzer: {e}")
        logger.error(traceback.format_exc())
        return None

def test_concept_extractor():
    """Test the concept extractor component."""
    try:
        from concept_extractor import ConceptExtractor
        
        logger.info("Creating test document with legal concepts...")
        with open("test_concepts.txt", "w") as f:
            f.write("The contract imposes liability on the defendant for breach.\n")
            f.write("Evidence was presented showing negligence in fulfilling obligations.\n")
            f.write("The court has jurisdiction over this case as per statute 42.3.\n")
        
        logger.info("Initializing ConceptExtractor...")
        extractor = ConceptExtractor()
        
        logger.info("Extracting concepts...")
        with open("test_concepts.txt", "r") as f:
            content = f.read()
            concepts = extractor.extract_concepts(content)
        
        logger.info("Extracted concepts:")
        for concept, references in concepts.items():
            logger.info(f"\nConcept: {concept}")
            logger.info(f"References: {len(references)}")
            for ref in references[:2]:  # Show just first two references
                logger.info(f"  - {ref}")
        
        return concepts
    except Exception as e:
        logger.error(f"Error in test_concept_extractor: {e}")
        logger.error(traceback.format_exc())
        return None

def test_document_editor():
    """Test the document editor component."""
    try:
        from document_editor import DocumentEditor
        
        logger.info("Creating test document for editing...")
        with open("test_edit_doc.txt", "w") as f:
            f.write("This is a sample legal document.\n")
            f.write("It contains some text that will be modified.\n")
            f.write("End of document.")
        
        logger.info("Initializing DocumentEditor...")
        editor = DocumentEditor()
        
        logger.info("Performing edits...")
        instructions = "replace 'sample legal document' with 'test contract'"
        result = editor.edit_document("test_edit_doc.txt", instructions)
        
        logger.info(f"Edit result: {result}")
        
        logger.info("Modified document content:")
        with open("test_edit_doc.txt", "r") as f:
            logger.info(f.read())
        
        return result
    except Exception as e:
        logger.error(f"Error in test_document_editor: {e}")
        logger.error(traceback.format_exc())
        return None

def test_semantic_analyzer():
    """Test the semantic analyzer component."""
    try:
        from semantic_analyzer import SemanticAnalyzer
        
        logger.info("Creating test documents for semantic comparison...")
        text1 = "The party shall be liable for damages resulting from breach of contract."
        text2 = "The defendant must pay compensation due to violating the agreement terms."
        
        logger.info("Initializing SemanticAnalyzer...")
        analyzer = SemanticAnalyzer()
        
        logger.info("Comparing semantic similarity...")
        similarity = analyzer.compare_semantic_similarity(text1, text2)
        
        logger.info("Similarity result:")
        for key, value in similarity.items():
            logger.info(f"{key}: {value}")
        
        return similarity
    except Exception as e:
        logger.error(f"Error in test_semantic_analyzer: {e}")
        logger.error(traceback.format_exc())
        return None

# This structure allows running tests individually in interactive mode
if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("Lawglance Component Testing")
    logger.info("=" * 80)
    logger.info("Run individual test functions in the interactive window:")
    logger.info("  test_document_analyzer()")
    logger.info("  test_concept_extractor()")
    logger.info("  test_document_editor()")
    logger.info("  test_semantic_analyzer()")
    logger.info("=" * 80)

# Code cells for interactive window
# %% Test Document Analyzer
# test_document_analyzer()

# %% Test Concept Extractor
# test_concept_extractor()

# %% Test Document Editor
# test_document_editor()

# %% Test Semantic Analyzer
# test_semantic_analyzer()
