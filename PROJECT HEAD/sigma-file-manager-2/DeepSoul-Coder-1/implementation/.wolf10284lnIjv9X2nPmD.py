"""
Legal Scraping Module - Handles scraping of legal websites with advanced capabilities
"""
import os
import sys
import time
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import utilities
from utils.memory_manager import get_memory_manager
from utils.retry import retry

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DeepSoul-LegalScraping")

# Configuration
DEFAULT_API_TOKEN = os.environ.get("COURTLISTENER_API_TOKEN")
COURTLISTENER_API_BASE = "https://www.courtlistener.com/api/rest/v4"

# Custom Exceptions
class ScrapingError(Exception):
    """Base class for scraping-related exceptions"""
    pass

class LoginError(ScrapingError):
    """Exception raised when login fails"""
    pass

class CaptchaError(ScrapingError):
    """Exception raised when CAPTCHA solving fails"""
    pass

class APIRequestError(ScrapingError):
    """Exception raised when API request fails"""
    pass

class CaptchaSolvingService:
    """Abstract base class for CAPTCHA solving services"""
    def solve_captcha(self, page, site_key) -> Optional[str]:
        """Solve CAPTCHA and return the solution"""
        raise NotImplementedError

class TwoCaptchaService(CaptchaSolvingService):
    """2Captcha API integration for CAPTCHA solving"""
    def __init__(self, api_key: str):
        """Initialize with 2Captcha API key"""
        self.api_key = api_key
        self.api_url = "http://2captcha.com/in.php"
        self.response_url = "http://2captcha.com/res.php"
    
    @retry(exceptions=(requests.exceptions.RequestException,), tries=3, delay=2)
    def solve_captcha(self, page, site_key) -> Optional[str]:
        """Solve CAPTCHA using 2Captcha API"""
        try:
            # Send CAPTCHA details to 2Captcha
            payload = {
                "key": self.api_key,
                "method": "userrecaptcha",
                "googlekey": site_key,
                "pageurl": page.url,
                "json": 1
            }
            response = requests.get(self.api_url, params=payload)
            response.raise_for_status()
            result = response.json()
            
            if result["status"] != 1:
                logger.error(f"2Captcha API error: {result['request']}")
                return None
            
            captcha_id = result["request"]
            logger.info(f"2Captcha task created with ID: {captcha_id}")
            
            # Poll for the solution
            solution = self._get_solution(captcha_id)
            return solution
            
        except requests.exceptions.RequestException as e:
            logger.error(f"2Captcha API request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error solving CAPTCHA: {str(e)}")
            return None
    
    @retry(exceptions=(requests.exceptions.RequestException,), tries=10, delay=5)
    def _get_solution(self, captcha_id: str) -> Optional[str]:
        """Poll 2Captcha API for the CAPTCHA solution"""
        payload = {
            "key": self.api_key,
            "action": "get",
            "id": captcha_id,
            "json": 1
        }
        
        time.sleep(10)  # Initial delay
        
        response = requests.get(self.response_url, params=payload)
        response.raise_for_status()
        result = response.json()
        
        if result["status"] == 1:
            logger.info("2Captcha solution received")
            return result["request"]
        else:
            logger.warning(f"2Captcha pending: {result['request']}")
            raise requests.exceptions.RequestException(f"2Captcha pending: {result['request']}")

class LegalScraperBase:
    """Base class for legal data scrapers"""
    
    def __init__(self, output_dir: str = "legal_data"):
        """Initialize scraper with output directory"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.memory_manager = get_memory_manager()
        
    def save_data(self, data: Dict[str, Any], filename: str) -> str:
        """Save scraped data to file"""
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Data saved to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving data to {filepath}: {str(e)}")
            raise
    
class PlaywrightLegalScraper(LegalScraperBase):
    """Legal scraper using Playwright for JavaScript-heavy sites and login handling"""
    
    def __init__(self, output_dir: str = "legal_data", headless: bool = True,
                 captcha_api_key: Optional[str] = None):
        """Initialize Playwright scraper"""
        super().__init__(output_dir)
        self.headless = headless
        self.captcha_api_key = captcha_api_key
        self.captcha_service = None
        if captcha_api_key:
            self.captcha_service = TwoCaptchaService(captcha_api_key)
    
    @retry(exceptions=(ScrapingError, requests.exceptions.RequestException), tries=3, delay=2)
    def scrape(self, url: str, wait_selector: str = "body", 
              credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Scrape legal data from URL using Playwright
        
        Args:
            url: The URL to scrape
            wait_selector: CSS selector to wait for before scraping content
            credentials: Optional dict with 'username' and 'password' keys for login
            
        Returns:
            Dictionary with scraped data
        """
        result = {
            "url": url,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "content": "",
            "metadata": {},
            "success": False
        }
        
        with sync_playwright() as p:
            try:
                # Launch browser
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                )
                page = context.new_page()
                
                # Go to URL
                logger.info(f"Navigating to {url}")
                page.goto(url)
                
                # Handle login if credentials provided
                if credentials and 'username' in credentials and 'password' in credentials:
                    self._handle_login(page, credentials)
                
                # Handle captcha if needed and API key provided
                if self.captcha_service:
                    self._solve_captcha(page)
                
                # Wait for content to load
                logger.info(f"Waiting for selector: {wait_selector}")
                page.wait_for_selector(wait_selector, timeout=30000)
                
                # Extract content
                content = page.content()
                result["content"] = content
                
                # Extract metadata
                result["metadata"]["title"] = page.title()
                result["metadata"]["headers"] = self._extract_headers(content)
                result["success"] = True
                
                # Close browser
                browser.close()
                
            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                result["error"] = str(e)
                raise ScrapingError(f"Failed to scrape {url}: {str(e)}")
        
        return result
    
    def _handle_login(self, page, credentials: Dict[str, str]) -> None:
        """Handle login process on legal websites"""
        try:
            # Common login form patterns - adjust selectors based on target site
            # Check if login form is present
            if page.query_selector("input[type='password']"):
                logger.info("Login form detected")
                
                # Find username/email field
                for selector in ["input[name='username']", "input[name='email']", "input[type='email']"]:
                    username_field = page.query_selector(selector)
                    if username_field:
                        break
                
                # Find password field
                password_field = page.query_selector("input[type='password']")
                
                # Find login button
                for selector in ["button[type='submit']", "input[type='submit']", 
                               "button:has-text('Login')", "button:has-text('Sign In')"]:
                    login_button = page.query_selector(selector)
                    if login_button:
                        break
                
                # Fill credentials if fields found
                if username_field and password_field and login_button:
                    username_field.fill(credentials["username"])
                    password_field.fill(credentials["password"])
                    login_button.click()
                    
                    # Wait for navigation after login
                    page.wait_for_load_state("networkidle")
                    logger.info("Login completed")
                else:
                    logger.warning("Could not find all login elements")
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            raise LoginError(f"Login failed: {str(e)}")
    
    def _solve_captcha(self, page) -> None:
        """Solve CAPTCHA if present using 2CAPTCHA API"""
        try:
            # Check for common CAPTCHA patterns
            captcha_selectors = [
                "iframe[src*='recaptcha']", 
                "iframe[src*='captcha']",
                ".g-recaptcha",
                "#captcha"
            ]
            
            for selector in captcha_selectors:
                captcha = page.query_selector(selector)
                if captcha:
                    logger.info("CAPTCHA detected, attempting to solve")
                    
                    # This is a simplified implementation
                    # For actual 2CAPTCHA integration, you would:
                    # 1. Extract the site key
                    # 2. Send to 2CAPTCHA API
                    # 3. Wait for solution
                    # 4. Apply solution to the form
                    
                    # Example with reCAPTCHA:
                    site_key = page.evaluate("""() => {
                        if (document.querySelector('.g-recaptcha')) {
                            return document.querySelector('.g-recaptcha').getAttribute('data-sitekey');
                        }
                        return null;
                    }""")
                    
                    if site_key:
                        logger.info(f"Found reCAPTCHA site key: {site_key}")
                        
                        # Solve CAPTCHA using 2Captcha API
                        solution = self.captcha_service.solve_captcha(page, site_key)
                        if solution:
                            logger.info("Applying CAPTCHA solution")
                            
                            # Inject the solution into the page
                            page.evaluate("""(solution) => {
                                const textarea = document.createElement('textarea');
                                textarea.id = 'g-recaptcha-response';
                                textarea.style.display = 'none';
                                textarea.value = solution;
                                document.body.appendChild(textarea);
                            }""", solution)
                            
                            # Submit the form (you may need to adjust this)
                            page.evaluate("""() => {
                                // Find the form and submit it
                                const form = document.querySelector('form');
                                if (form) {
                                    form.submit();
                                } else {
                                    console.warn('Could not find form to submit');
                                }
                            }""")
                            
                            # Wait for navigation
                            page.wait_for_load_state("networkidle")
                            logger.info("CAPTCHA solved successfully")
                        else:
                            logger.error("Failed to solve CAPTCHA with 2Captcha")
                            raise CaptchaError("Failed to solve CAPTCHA with 2Captcha")
                    break
        except Exception as e:
            logger.error(f"Error handling CAPTCHA: {str(e)}")
            raise CaptchaError(f"CAPTCHA solving failed: {str(e)}")
    
    def _extract_headers(self, html_content: str) -> List[str]:
        """Extract header text from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        headers = []
        
        for tag in ["h1", "h2", "h3"]:
            for header in soup.find_all(tag):
                if header.text.strip():
                    headers.append(header.text.strip())
        
        return headers

class UndetectedSeleniumScraper(LegalScraperBase):
    """Legal scraper using Undetected ChromeDriver for bypassing anti-bot measures"""
    
    def __init__(self, output_dir: str = "legal_data", headless: bool = True):
        """Initialize Undetected ChromeDriver scraper"""
        super().__init__(output_dir)
        self.headless = headless
        
    @retry(exceptions=(ScrapingError, requests.exceptions.RequestException), tries=3, delay=2)
    def scrape(self, url: str, wait_selector: str = "body",
              credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Scrape legal data from URL using Undetected ChromeDriver
        
        Args:
            url: The URL to scrape
            wait_selector: CSS selector to wait for before scraping content
            credentials: Optional dict with 'username' and 'password' keys
            
        Returns:
            Dictionary with scraped data
        """
        result = {
            "url": url,
            self.session.headers.update({"Authorization": f"Token {self.api_key}"})
    
    @retry(exceptions=(APIRequestError, requests.exceptions.RequestException), tries=3, delay=2)
    def get_court_listener_case(self, case_id: str) -> Dict[str, Any]:
        """Get case data from CourtListener API"""
        url = f"{COURTLISTENER_API_BASE}/opinions/{case_id}/"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for case {case_id}: {str(e)}")
            raise APIRequestError(f"API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching case {case_id}: {str(e)}")
            raise
    
    @retry(exceptions=(APIRequestError, requests.exceptions.RequestException), tries=3, delay=2)
    def search_courtlistener(self, query: str, page: int = 1) -> Dict[str, Any]:
        """Search for cases on CourtListener"""
        url = f"{COURTLISTENER_API_BASE}/search/"
        params = {
            "q": query,
            "page": page,
            "format": "json"
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for query '{query}': {str(e)}")
            raise APIRequestError(f"API request failed: {str(e)}")
        except Exception as e:
            logger.error(f"Error searching for '{query}': {str(e)}")
            raise

def scrape_court_info(url: str, method: str = "playwright", 
                     credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Scrape court-related information from a given URL using the specified method.
    This method can overcome sign-in restrictions and CAPTCHA by automating browsers.
    
    Args:
        url: The URL to scrape
        method: Scraping method ('playwright', 'selenium', or 'api')
        credentials: Optional credentials for login (dict with 'username' and 'password')
        
    Returns:
        Dictionary with scraped data
    """
    if method == "playwright":
        scraper = PlaywrightLegalScraper()
        return scraper.scrape(url, credentials=credentials)
    elif method == "selenium":
        scraper = UndetectedSeleniumScraper()
        return scraper.scrape(url, credentials=credentials)
    elif method == "api":
        client = LegalAPIClient()
        # This is a simplified approach - in reality would need to parse the URL
        case_id = url.split("/")[-2] if url.endswith("/") else url.split("/")[-1]
        return client.get_court_listener_case(case_id)
    else:
        raise ValueError(f"Unsupported scraping method: {method}")

if __name__ == "__main__":
    # Example usage
    test_url = "https://www.courtlistener.com/opinion/4801970/oracle-america-inc-v-google-llc/"
    data = scrape_court_info(test_url)
    print(f"Scraped Data: {data.keys()}")
    
    # Example with login credentials (commented out)
    # protected_url = "https://example-court-website.com/cases"
    # credentials = {"username": "user@example.com", "password": "password"}
    # data = scrape_court_info(protected_url, credentials=credentials)
