"""Unit tests for lawglance_main.py."""
import pytest
from unittest.mock import Mock, patch
from src.lawglance_main import Lawglance
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, AIMessage

class TestLawglance:
    """Test suite for Lawglance class."""

    @pytest.fixture
    def mock_llm(self):
        """Mock language model."""
        return Mock()

    @pytest.fixture
    def mock_embeddings(self):
        """Mock embeddings."""
        return Mock()

    @pytest.fixture
    def mock_vector_store(self):
        """Mock vector store."""
        return Mock()

    @pytest.fixture
    def lawglance(self, mock_llm, mock_embeddings, mock_vector_store):
        """Lawglance instance with mocked dependencies."""
        return Lawglance(mock_llm, mock_embeddings, mock_vector_store)

    def test_initialization(self, lawglance):
        """Test Lawglance initialization."""
        assert lawglance.llm is not None
        assert lawglance.embeddings is not None
        assert lawglance.vector_store is not None
        assert isinstance(lawglance.prompt, ChatPromptTemplate)
        assert len(lawglance.chat_history) == 0

    def test_conversational(self, lawglance, mock_vector_store):
        """Test conversational method."""
        # Setup mock retriever
        mock_vector_store.as_retriever.return_value.invoke.return_value = [
            Mock(page_content="Test context")
        ]

        # Setup mock LLM response
        lawglance.llm.invoke.return_value = AIMessage(content="Test response")

        # Test conversation
        response = lawglance.conversational("Test question")

        # Verify response
        assert response == "Test response"
        assert len(lawglance.chat_history) == 2
        assert isinstance(lawglance.chat_history[0], HumanMessage)
        assert isinstance(lawglance.chat_history[1], AIMessage)

    def test_manage_history(self, lawglance):
        """Test chat history management."""
        # Add messages to exceed history limit
        for i in range(20):
            lawglance.chat_history.append(HumanMessage(content=f"Message {i}"))
            lawglance.chat_history.append(AIMessage(content=f"Response {i}"))

        # Verify history is trimmed
        lawglance._manage_history()
        assert len(lawglance.chat_history) == lawglance.max_history * 2

    def test_clear_history(self, lawglance):
        """Test clearing chat history."""
        # Add some messages
        lawglance.chat_history.append(HumanMessage(content="Test message"))
        lawglance.chat_history.append(AIMessage(content="Test response"))

        # Clear history
        lawglance.clear_history()
        assert len(lawglance.chat_history) == 0
