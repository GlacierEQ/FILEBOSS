import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from casebuilder.services.ai_analysis import AnthropicAnalyzer, DocumentAnalysis, AnalysisStatus, AIProviderType

@pytest.fixture
def anthropic_analyzer():
    """Provides an instance of AnthropicAnalyzer with a mocked client."""
    with patch('anthropic.AsyncAnthropic') as mock_client:
        analyzer = AnthropicAnalyzer(api_key="test_api_key")
        analyzer.client = mock_client
        return analyzer

@pytest.mark.asyncio
async def test_analyze_document_success(anthropic_analyzer):
    """Test successful document analysis with Anthropic."""
    # Arrange
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="This is a summary.")]
    mock_response.usage.input_tokens = 10
    mock_response.usage.output_tokens = 20

    anthropic_analyzer.client.messages.create = AsyncMock(return_value=mock_response)

    # Act
    result = await anthropic_analyzer.analyze_document("This is a test document.")

    # Assert
    assert isinstance(result, DocumentAnalysis)
    assert result.status == AnalysisStatus.COMPLETED
    assert result.provider == AIProviderType.ANTHROPIC
    assert result.summary == "This is a summary."
    assert result.metadata["usage"]["input_tokens"] == 10
    assert result.metadata["usage"]["output_tokens"] == 20

@pytest.mark.asyncio
async def test_analyze_document_failure(anthropic_analyzer):
    """Test failed document analysis with Anthropic."""
    # Arrange
    anthropic_analyzer.client.messages.create = AsyncMock(side_effect=Exception("API Error"))

    # Act
    result = await anthropic_analyzer.analyze_document("This is a test document.")

    # Assert
    assert isinstance(result, DocumentAnalysis)
    assert result.status == AnalysisStatus.FAILED
    assert result.provider == AIProviderType.ANTHROPIC
    assert result.error == "API Error"
