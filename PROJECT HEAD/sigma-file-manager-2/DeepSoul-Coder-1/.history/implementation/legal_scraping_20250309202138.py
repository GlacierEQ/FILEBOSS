from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import logging
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DeepSoul-LegalScraping")

class LegalScraperBase:
    """Base class for legal data scrapers"""
    
    def __init__(self, output_dir: str = "legal_data"):
        """Initialize scraper with output directory"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def save_data(self, data: Dict[str, Any], filename: str) -> str:
        """Save scraped data to file"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Data saved to {filepath}")
        return filepath
    
    def scrape(self, url: str) -> Dict[str, Any]:
        """Scrape data from URL - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement scrape method")

class PlaywrightLegalScraper(LegalScraperBase):
    """Legal scraper using Playwright for JavaScript-heavy sites and login handling"""
    
    def __init__(self, output_dir: str = "legal_data", headless: bool = True,
                 captcha_api_key: Optional[str] = None):
        """Initialize Playwright scraper"""
        super().__init__(output_dir)
        self.headless = headless
        self.captcha_api_key = captcha_api_key
        
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
                if self.captcha_api_key:
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
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
    
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
                        # Here you would call 2CAPTCHA API with the site key
                        # and then apply the solution
                        
                        # For now, we'll just log that we would solve it
                        logger.info("Would solve CAPTCHA with 2CAPTCHA API")
                    break
        except Exception as e:
            logger.error(f"Error handling CAPTCHA: {str(e)}")
    
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
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "content": "",
            "metadata": {},
            "success": False
        }
        
        try:
            # Initialize driver
            options = uc.ChromeOptions()
            if self.headless:
                options.add_argument("--headless")
            
            driver = uc.Chrome(options=options)
            driver.get(url)
            
            # Wait for content to load
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, wait_selector))
            )
            
            # Handle login if credentials provided
            if credentials and 'username' in credentials and 'password' in credentials:
                self._handle_login(driver, credentials)
            
            # Extract content
            content = driver.page_source
            result["content"] = content
            
            # Extract metadata
            result["metadata"]["title"] = driver.title
            result["metadata"]["url"] = driver.current_url
            result["success"] = True
            
            # Close driver
            driver.quit()
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            result["error"] = str(e)
            
        return result
    
    def _handle_login(self, driver, credentials: Dict[str, str]) -> None:
        """Handle login with Selenium WebDriver"""
        try:
            # Look for common login elements
            username_selectors = ["input[name='username']", "input[name='email']", "input[type='email']"]
            password_selectors = ["input[type='password']"]
            login_button_selectors = ["button[type='submit']", "input[type='submit']", 
                                    "button:contains('Login')", "button:contains('Sign In')"]
            
            # Try to find username field
            for selector in username_selectors:
                try:
                    username_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    username_field.send_keys(credentials["username"])
                    break
                except:
                    continue
            
            # Try to find password field
            for selector in password_selectors:
                try:
                    password_field = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    password_field.send_keys(credentials["password"])
                    break
                except:
                    continue
            
            # Try to find login button
            for selector in login_button_selectors:
                try:
                    login_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    login_button.click()
                    break
                except:
                    continue
            
            # Wait for login to complete
            time.sleep(5)
            logger.info("Login attempt completed")
            
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")

class LegalAPIClient:
    """Client for accessing legal data APIs (CourtListener, Justia, etc.)"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize API client with optional API key"""
        self.api_key = api_key
        self.session = requests.Session()
        
        # Add API key to headers if provided
        if api_key:
            self.session.headers.update({"Authorization": f"Token {api_key}"})
    
    def get_court_listener_case(self, case_id: str) -> Dict[str, Any]:
        """Get case data from CourtListener API"""
        url = f"https://www.courtlistener.com/api/rest/v3/opinions/{case_id}/"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching case {case_id}: {str(e)}")
            return {"error": str(e)}
    
    def search_courtlistener(self, query: str, page: int = 1) -> Dict[str, Any]:
        """Search for cases on CourtListener"""
        url = "https://www.courtlistener.com/api/rest/v3/search/"
        params = {
            "q": query,
            "page": page,
            "format": "json"
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error searching for '{query}': {str(e)}")
            return {"error": str(e)}

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
