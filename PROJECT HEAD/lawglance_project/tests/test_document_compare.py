import unittest
import logging
from utils.document_compare import compare_documents, analyze_changes

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("lawglance.test_document_compare")

class TestDocumentCompare(unittest.TestCase):
    
    def test_compare_documents(self):
        """Test the document comparison functionality."""
        doc1 = "This is a sample legal document."
        doc2 = "This is a sample legal document."
        
        result = compare_documents(doc1, doc2)
        self.assertEqual(result["similarity"], 1.0)
        
        doc3 = "This is a different document."
        result = compare_documents(doc1, doc3)
        self.assertNotEqual(result["similarity"], 1.0)

    def test_analyze_changes(self):
        """Test the change analysis functionality."""
        original = "This is the original document."
        modified = "This is the modified document."
        
        changes = analyze_changes(original, modified)
        self.assertIn("Document has been modified.", changes)

if __name__ == "__main__":
    unittest.main()
