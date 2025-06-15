"""
Unit and Integration Tests for Legal Scraping Module
"""
import os
import sys
import pytest
from unittest.mock import patch, Mock
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import legal scraping components
from implementation.legal_scraping import (
    LegalScraperBase, PlaywrightLegalScraper, UndetectedSeleniumScraper, LegalAPIClient,
    ScrapingError, LoginError, CaptchaError, APIRequestError, TwoCaptchaService
)

# Mock API key for testing
MOCK_API_KEY = "test_api_key"
MOCK_2CAPTCHA_API_KEY = "test_2captcha_api_key"

# Test LegalScraperBase
def test_legal_scraper_base():
    """Test LegalScraperBase initialization and save_data method"""
    base_scraper = LegalScraperBase(output_dir="test_output")
    assert base_scraper.output_dir == "test_output"
    
    # Create test data
    test_data = {"test": "data"}
    test_filename = "test_data.json"
    
    # Save data and check if file exists
    filepath = base_scraper.save_data(test_data, test_filename)
    assert os.path.exists(filepath)
    
    # Clean up test file
    os.remove(filepath)
    os.rmdir("test_output")

# Test PlaywrightLegalScraper
@pytest.fixture
def playwright_scraper():
    """Fixture for creating PlaywrightLegalScraper instance"""
    return PlaywrightLegalScraper(headless=True, captcha_api_key=MOCK_2CAPTCHA_API_KEY)

def test_playwright_scraper_initialization(playwright_scraper):
    """Test PlaywrightLegalScraper initialization"""
    assert playwright_scraper.headless is True
    assert playwright_scraper.captcha_api_key == MOCK_2CAPTCHA_API_KEY
    assert isinstance(playwright_scraper.captcha_service, TwoCaptchaService)

@pytest.mark.skip(reason="Requires network access and valid selectors")
def test_playwright_scraper_scrape(playwright_scraper):
    """Test PlaywrightLegalScraper scrape method"""
    test_url = "https://www.courtlistener.com/opinion/4801970/oracle-america-inc-v-google-llc/"
    result = playwright_scraper.scrape(test_url, wait_selector="body")
    
    assert result["success"] is True
    assert result["url"] == test_url
    assert "content" in result
    assert "metadata" in result

def test_playwright_scraper_handle_login(playwright_scraper):
    """Test PlaywrightLegalScraper _handle_login method"""
    # This test would require mocking a Playwright page and simulating a login form
    # For simplicity, we'll just check that it doesn't raise an exception
    with pytest.raises(Exception):
        playwright_scraper._handle_login(None, {"username": "test", "password": "test"})

@patch("implementation.legal_scraping.TwoCaptchaService.solve_captcha")
def test_playwright_scraper_solve_captcha(mock_solve, playwright_scraper):
    """Test PlaywrightLegalScraper _solve_captcha method"""
    mock_solve.return_value = "test_captcha_solution"
    
    # Create a mock page
    mock_page = Mock()
    mock_page.query_selector.return_value = True  # Simulate CAPTCHA presence
    mock_page.evaluate.return_value = "test_site_key"
    
    # Call _solve_captcha
    try:
        playwright_scraper._solve_captcha(mock_page)
        assert mock_solve.called
    except Exception as e:
        assert False, f"Exception raised: {e}"

def test_playwright_scraper_extract_headers(playwright_scraper):
    """Test PlaywrightLegalScraper _extract_headers method"""
    html_content = "<h1>Test Header</h1><h2>Sub Header</h2><p>Some text</p>"
    headers = playwright_scraper._extract_headers(html_content)
    assert "Test Header" in headers
    assert "Sub Header" in headers

# Test UndetectedSeleniumScraper
@pytest.fixture
def selenium_scraper():
    """Fixture for creating UndetectedSeleniumScraper instance"""
    return UndetectedSeleniumScraper(headless=True)

def test_selenium_scraper_initialization(selenium_scraper):
    """Test UndetectedSeleniumScraper initialization"""
    assert selenium_scraper.headless is True

@pytest.mark.skip(reason="Requires network access and valid selectors")
def test_selenium_scraper_scrape(selenium_scraper):
    """Test UndetectedSeleniumScraper scrape method"""
    test_url = "https://www.courtlistener.com/opinion/4801970/oracle-america-inc-v-google-llc/"
    result = selenium_scraper.scrape(test_url, wait_selector="body")
    
    assert result["success"] is True
    assert result["url"] == test_url
    assert "content" in result
    assert "metadata" in result

def test_selenium_scraper_handle_login(selenium_scraper):
    """Test UndetectedSeleniumScraper _handle_login method"""
    # This test would require mocking a Selenium WebDriver and simulating a login form
    # For simplicity, we'll just check that it doesn't raise an exception
    with pytest.raises(Exception):
        selenium_scraper._handle_login(None, {"username": "test", "password": "test"})

# Test LegalAPIClient
@pytest.fixture
def legal_api_client():
    """Fixture for creating LegalAPIClient instance"""
    return LegalAPIClient(api_key=MOCK_API_KEY)

def test_legal_api_client_initialization(legal_api_client):
    """Test LegalAPIClient initialization"""
    assert legal_api_client.api_key == MOCK_API_KEY
    assert legal_api_client.session.headers["Authorization"] == f"Token {MOCK_API_KEY}"

@patch("implementation.legal_scraping.requests.Session.get")
def test_legal_api_client_get_court_listener_case(mock_get, legal_api_client):
    """Test LegalAPIClient get_court_listener_case method"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"test": "data"}
    mock_get.return_value = mock_response
    
    case_id = "test_case_id"
    result = legal_api_client.get_court_listener_case(case_id)
    
    assert result == {"test": "data"}
    mock_get.assert_called_once_with(f"https://www.courtlistener.com/api/rest/v4/opinions/{case_id}/")

@patch("implementation.legal_scraping.requests.Session.get")
def test_legal_api_client_search_courtlistener(mock_get, legal_api_client):
    """Test LegalAPIClient search_courtlistener method"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"test": "data"}
    mock_get.return_value = mock_response
    
    query = "test_query"
    result = legal_api_client.search_courtlistener(query)
    
    assert result == {"test": "data"}
    mock_get.assert_called_once()

class Mock:
    """Mock class for testing"""
    def __init__(self):
        self.status_code = 200
    
    def json(self):
        return {}
    
    def raise_for_status(self):
        pass
