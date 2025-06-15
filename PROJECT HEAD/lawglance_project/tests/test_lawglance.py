"""Basic test file for the LawGlance project."""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.lawglance_main import Lawglance

class TestLawglance(unittest.TestCase):
    """Test cases for the Lawglance class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_llm = MagicMock()
        self.mock_embeddings = MagicMock()
        self.mock_vector_store = MagicMock()
        
        # Configure mock retriever
        self.mock_retriever = MagicMock()
        self.mock_vector_store.as_retriever.return_value = self.mock_retriever
        
        # Mock document return value
        mock_doc = MagicMock()
        mock_doc.page_content = "This is a mock legal document."
        self.mock_retriever.invoke.return_value = [mock_doc]
        
        # Set up mock response
        mock_response = MagicMock()
        mock_response.content = "This is a mock response."
        self.mock_llm.invoke.return_value = mock_response
        
        # Create Lawglance instance
        self.law = Lawglance(self.mock_llm, self.mock_embeddings, self.mock_vector_store)
    
    def test_initialization(self):
        """Test that Lawglance initializes correctly."""
        self.assertEqual(self.law.llm, self.mock_llm)
        self.assertEqual(self.law.embeddings, self.mock_embeddings)
        self.assertEqual(self.law.vector_store, self.mock_vector_store)
        self.assertEqual(self.law.chat_history, [])
    
    def test_conversational(self):
        """Test the conversational method."""
        response = self.law.conversational("What is a contract?")
        
        # Check that retriever was called
        self.mock_retriever.invoke.assert_called_once_with("What is a contract?")
        
        # Check that llm was called
        self.mock_llm.invoke.assert_called_once()
        
        # Check return value
        self.assertEqual(response, "This is a mock response.")
        
        # Check chat history was updated
        self.assertEqual(len(self.law.chat_history), 2)

if __name__ == "__main__":
    unittest.main()
