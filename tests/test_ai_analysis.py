"""
Tests for the AI Analysis Service.
"""
import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

import pytest_asyncio
from pydantic import HttpUrl

from casebuilder.services.ai_analysis import (
    AIAnalysisService,
    AIAnalysisError,
    AIProviderType,
    OpenAIAnalyzer,
    AnalysisStatus,
    DocumentAnalysis,
    ImageAnalysis
)
from casebuilder.utils import utc_now

# Sample test data
SAMPLE_TEXT = """
This is a test document about artificial intelligence and machine learning.
It mentions important concepts like neural networks, deep learning, and natural language processing.
The document is written by Test Author and contains confidential information.
"""

SAMPLE_IMAGE_BYTES = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xfc\xff\xff?\x03\x00\x08\xfc\x02\xfe\x8b\x8f\x1f\x1e\x00\x00\x00\x00IEND\xaeB`\x82"

@pytest.fixture
def mock_openai_response():
    """Mock response from OpenAI API."""
    return {
        "choices": [{
            "message": {
                "content": "This is a test summary of the document. It contains key information about the subject matter.",
                "role": "assistant"
            },
            "finish_reason": "stop",
            "index": 0
        }],
        "model": "gpt-4-turbo-preview",
        "object": "chat.completion",
        "usage": {
            "completion_tokens": 10,
            "prompt_tokens": 100,
            "total_tokens": 110
        }
    }

@pytest.fixture
def mock_aiohttp_client(mock_openai_response):
    """Mock aiohttp client for testing HTTP requests."""
    # Create a mock response for successful API calls
    mock_success_response = MagicMock()
    mock_success_response.status = 200
    mock_success_response.json = AsyncMock(return_value=mock_openai_response)
    
    # Create a mock client that returns our mock response
    mock_client = MagicMock()
    
    # Set up the async context manager chain
    mock_client.__aenter__.return_value = mock_client
    mock_client.post.return_value.__aenter__.return_value = mock_success_response
    
    # Patch the ClientSession to return our mock client
    with patch('aiohttp.ClientSession', return_value=mock_client) as mock_session:
        yield mock_session
        
    # We can't reliably assert this in the fixture due to test teardown timing
    # Instead, we'll verify cleanup in individual tests where needed

@pytest_asyncio.fixture
async def ai_service():
    """Create an AIAnalysisService with a mock OpenAI provider for testing."""
    # Create a mock aiohttp.ClientSession that won't be used directly
    mock_session = MagicMock()
    mock_session.__aenter__.return_value = mock_session
    mock_session.__aexit__.return_value = None
    
    # Patch aiohttp.ClientSession to return our mock
    with patch('aiohttp.ClientSession', return_value=mock_session):
        service = AIAnalysisService(cache_ttl=0)  # Disable cache for tests
        
        # Create a proper mock for the provider
        mock_provider = MagicMock(spec=OpenAIAnalyzer)
        
        # Setup document analysis response
        doc_result = DocumentAnalysis(
            status=AnalysisStatus.COMPLETED,
            provider=AIProviderType.OPENAI,
            model="gpt-4-turbo",
            analysis_type="document_analysis",
            summary="Test summary",
            key_terms=["test", "document"],
            entities=[{"type": "PERSON", "text": "Test User"}],
            sentiment="neutral",
            categories=["test"],
            completed_at=utc_now()
        )
        
        # Setup image analysis response
        img_result = ImageAnalysis(
            status=AnalysisStatus.COMPLETED,
            provider=AIProviderType.OPENAI,
            model="gpt-4-vision-preview",
            analysis_type="image_analysis",
            objects=[
                {"label": "object1", "confidence": 0.95, "bbox": [10, 20, 100, 100]},
                {"label": "object2", "confidence": 0.90, "bbox": [150, 30, 50, 50]}
            ],
            text="Test image description",
            labels=[{"test": 0.95}, {"document": 0.85}],
            completed_at=utc_now()
        )
        
        # Setup the mock provider
        mock_provider.analyze_document.return_value = doc_result
        mock_provider.analyze_image.return_value = img_result
        
        # Add the provider to the service
        service._providers[AIProviderType.OPENAI] = mock_provider
        service._default_provider = AIProviderType.OPENAI
        
        # Patch the service's _session to avoid actual HTTP calls
        service._session = mock_session
        
        yield service, mock_provider, mock_session

@pytest.mark.asyncio
async def test_openai_analyze_document(ai_service, mock_openai_response):
    """Test document analysis with OpenAI provider."""
    # Unpack the fixture
    service, mock_provider, mock_session = ai_service
    
    # Call the method under test
    result = await service.analyze_evidence(
        evidence_content=SAMPLE_TEXT,
        content_type="text/plain"
    )
    
    # Assert the result is as expected
    assert isinstance(result, DocumentAnalysis)
    assert result.status == AnalysisStatus.COMPLETED
    assert result.provider == AIProviderType.OPENAI
    assert result.model == "gpt-4-turbo"
    assert result.summary == "Test summary"
    assert result.key_terms == ["test", "document"]
    
    # Verify the mock was called with expected arguments
    mock_provider.analyze_document.assert_called_once_with(
        SAMPLE_TEXT,
        session=mock_session
    )
    
    # The result summary should match the mocked response
    assert result.summary == "Test summary"

@pytest.mark.asyncio
async def test_openai_analyze_image(mock_aiohttp_client, ai_service):
    """Test image analysis with OpenAI provider."""
    service, _, _ = ai_service
    result = await service.analyze_evidence(
        evidence_content=SAMPLE_IMAGE_BYTES,
        content_type="image/png"
    )
    
    assert isinstance(result, ImageAnalysis)
    assert result.status == AnalysisStatus.COMPLETED
    assert result.provider == AIProviderType.OPENAI
    assert result.model == "gpt-4-vision-preview"

@pytest.mark.asyncio
async def test_ai_service_text_analysis(ai_service):
    """Test text analysis through the AI service."""
    # Unpack the fixture
    service, mock_provider, mock_session = ai_service
    
    # Call the method under test
    result = await service.analyze_evidence(
        evidence_content=SAMPLE_TEXT,
        content_type="text/plain"
    )
    
    # Assert the result is as expected
    assert isinstance(result, DocumentAnalysis)
    assert result.status == AnalysisStatus.COMPLETED
    assert result.provider == AIProviderType.OPENAI
    assert result.model == "gpt-4-turbo"
    assert result.summary == "Test summary"
    assert result.key_terms == ["test", "document"]
    
    mock_provider.analyze_document.assert_called_once_with(
        SAMPLE_TEXT,
        session=mock_session
    )

    # The result summary should match the mocked response
    assert result.summary == "Test summary"

@pytest.mark.asyncio
async def test_ai_service_image_analysis(ai_service, mock_aiohttp_client):
    service, _, _ = ai_service
    result = await service.analyze_evidence(
        evidence_content=SAMPLE_IMAGE_BYTES,
        content_type="image/png"
    )
    
    # Assert the result is as expected
    assert isinstance(result, ImageAnalysis)
    assert result.status == AnalysisStatus.COMPLETED
    assert result.provider == AIProviderType.OPENAI
    assert result.model == "gpt-4-vision-preview"

@pytest.mark.asyncio
async def test_ai_service_invalid_provider():
    """Test that an error is raised for an invalid provider."""
    service = AIAnalysisService()
    with pytest.raises(KeyError):
        service.get_provider(AIProviderType.OPENAI)  # No provider registered
        
    # Test with invalid provider type
    with pytest.raises(KeyError):
        service.get_provider("invalid-provider")

@pytest.mark.asyncio
async def test_ai_service_invalid_content_type(ai_service):
    """Test that an error is handled for invalid content types."""
    service, mock_provider, mock_session = ai_service
    
    # Mock the provider to raise an error for invalid content type
    mock_provider.analyze_document.side_effect = ValueError("Unsupported content type")
    
    with pytest.raises(AIAnalysisError):
        await service.analyze_evidence(
            evidence_content=b"test",
            content_type="invalid/type",
        )

@pytest.mark.asyncio
async def test_ai_service_error_handling(ai_service):
    """Test error handling in the AI service."""
    service, mock_provider, mock_session = ai_service
    
    # Setup the mock to raise an error
    test_error = Exception("Test error")
    mock_provider.analyze_document.side_effect = test_error
    
    with pytest.raises(AIAnalysisError):
        await service.analyze_evidence(
            evidence_content=SAMPLE_TEXT,
            content_type="text/plain",
        )
    
    # Test with non-existent provider - should return error result, not raise
    result = await service.analyze_evidence(
        evidence_content=SAMPLE_TEXT,
        content_type="text/plain",
        provider=AIProviderType.ANTHROPIC  # Not registered
    )
    assert result.status == AnalysisStatus.FAILED
    assert "No provider available" in result.error

@pytest.mark.asyncio
async def test_ai_service_retry_logic():
    """Test that the service retries failed requests."""
    service = AIAnalysisService()
    mock_provider = MagicMock()
    
    # Set up the mock to fail twice then succeed
    mock_provider.analyze_document.side_effect = [
        Exception("First error"),
        Exception("Second error"),
        DocumentAnalysis(
            status=AnalysisStatus.COMPLETED,
            provider=AIProviderType.OPENAI,
            model="test-model",
            analysis_type="document_analysis"
        )
    ]
    
    # Add the provider and set it as default
    service._providers[AIProviderType.OPENAI] = mock_provider
    service._default_provider = AIProviderType.OPENAI
    
    # Should succeed after retries
    result = await service.analyze_evidence(
        evidence_content=SAMPLE_TEXT,
        content_type="text/plain"
    )
    
    # Verify the result
    assert result.status == AnalysisStatus.COMPLETED, f"Expected COMPLETED but got {result.status}"
    assert mock_provider.analyze_document.call_count == 3, \
        f"Expected 3 calls (2 retries + 1 success) but got {mock_provider.analyze_document.call_count}"

@pytest.mark.asyncio
async def test_ai_service_caching():
    """Test that the service properly caches results."""
    # Create a service with a short cache TTL
    service = AIAnalysisService(cache_ttl=60)
    mock_provider = MagicMock()
    mock_provider.analyze_document.return_value = DocumentAnalysis(
        status=AnalysisStatus.COMPLETED,
        provider=AIProviderType.OPENAI,
        model="gpt-4-turbo",
        analysis_type="document_analysis",
        summary="Cached summary",
        completed_at=utc_now()
    )

    service._providers[AIProviderType.OPENAI] = mock_provider
    service._default_provider = AIProviderType.OPENAI

    # Reset call count before starting our test
    mock_provider.analyze_document.reset_mock()

    # First call - should call the provider
    result1 = await service.analyze_evidence(
        evidence_content=SAMPLE_TEXT,
        content_type="text/plain"
    )
    assert mock_provider.analyze_document.call_count == 1

    # Second call with same content - should use cache
    result2 = await service.analyze_evidence(
        evidence_content=SAMPLE_TEXT,
        content_type="text/plain"
    )
    # Still only called once due to caching
    assert mock_provider.analyze_document.call_count == 1
    assert result1 == result2  # Should be the same object from cache

    # Test cache invalidation after TTL
    service._cache_ttl = 0.1  # Very short TTL for testing
    service._cache = {}  # Clear cache

    # Reset call count for the next part of the test
    mock_provider.analyze_document.reset_mock()

    # First call after cache invalidation - should call provider again
    result3 = await service.analyze_evidence(
        evidence_content=SAMPLE_TEXT,
        content_type="text/plain"
    )
    assert mock_provider.analyze_document.call_count == 1

    # Wait for cache to expire
    await asyncio.sleep(0.2)


    # Call after TTL - should call provider again
    result4 = await service.analyze_evidence(
        evidence_content=SAMPLE_TEXT,
        content_type="text/plain"
    )
    # Should have called the provider again after TTL
    assert mock_provider.analyze_document.call_count == 2

def test_create_default_ai_service():
    """Test creation of a default AI service."""
    service = AIAnalysisService()
    assert isinstance(service, AIAnalysisService)
    assert len(service.providers) == 0  # No providers by default
    
    # Test with OpenAI API key
    service = AIAnalysisService()
    openai_provider = OpenAIAnalyzer(api_key="test-key")
    service.add_provider(AIProviderType.OPENAI, openai_provider)
    
    assert AIProviderType.OPENAI in service.providers
    assert service.get_provider(AIProviderType.OPENAI) == openai_provider

@pytest.mark.asyncio
async def test_ai_service_provider_management():
    """Test adding and retrieving providers."""
    service = AIAnalysisService()
    provider = OpenAIAnalyzer(api_key="test-key")
    
    # Add provider
    service.add_provider(AIProviderType.OPENAI, provider)
    assert AIProviderType.OPENAI in service.providers
    
    # Get provider
    retrieved = service.get_provider(AIProviderType.OPENAI)
    assert retrieved == provider
    
    # Test default provider
    service.default_provider = AIProviderType.OPENAI
    assert service.get_provider() == provider
    
    # Test invalid provider
    with pytest.raises(KeyError):
        service.get_provider("invalid-provider")
