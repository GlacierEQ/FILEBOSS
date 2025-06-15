"""
Legal Data Pipeline - End-to-end system for legal data scraping, processing, and analysis
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup # Fixed import
import pandas as pd
from elasticsearch import Elasticsearch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import DeepSoul components
from implementation.legal_scraping import LegalAPIClient

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("legal_pipeline.log")
    ]
)
logger = logging.getLogger("DeepSoul-LegalPipeline")

class LegalDataPipeline:
    """
    End-to-end pipeline for scraping, processing, storing, and analyzing legal data
    """
    
    def __init__(self, 
                 elasticsearch_host: Optional[str] = None,
                 output_dir: str = "legal_data",
                 max_workers: int = 4,
                 api_key: Optional[str] = None):
        """
        Initialize the legal data pipeline
        
        Args:
            elasticsearch_host: Host URL for Elasticsearch (optional)
            output_dir: Directory to store output files
            max_workers: Maximum number of concurrent workers
            api_key: API key for legal data services
        """
        self.elasticsearch_host = elasticsearch_host
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.api_key = api_key
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize Elasticsearch client if host is provided
        self.es_client = None
        if elasticsearch_host:
            try:
                self.es_client = Elasticsearch(hosts=[elasticsearch_host])
                if not self.es_client.ping():
                    logger.warning(f"Could not connect to Elasticsearch at {elasticsearch_host}")
                    self.es_client = None
                else:
                    logger.info(f"Connected to Elasticsearch at {elasticsearch_host}")
            except Exception as e:
                logger.error(f"Error connecting to Elasticsearch: {str(e)}")
                self.es_client = None
    
    def run_full_pipeline(self, 
                          urls: List[str], 
                          scrape_method: str = "playwright",
                          index_name: str = "legal_documents",
                          export_csv: bool = False) -> Dict[str, Any]:
        """
        Run the full legal data pipeline
        
        Args:
            urls: List of URLs to process
            scrape_method: Method to use for scraping (playwright, selenium, api)
            index_name: Elasticsearch index name
            export_csv: Whether to export results to CSV
            
        Returns:
            Dictionary with pipeline results
        """
        results = {
            "status": "pending",
            "urls_count": len(urls),
            "scraped_count": 0,
            "successful_scrape_count": 0,
            "processed_count": 0,
            "indexed": False,
            "csv_export_path": None
        }
        
        try:
            # Scrape URLs
            results["status"] = "scraping"
            scraped_data = self.scrape_urls(urls, method=scrape_method)
            results["scraped_count"] = len(scraped_data)
            results["successful_scrape_count"] = sum(r.get("success", False) for r in scraped_data)
            
            # Process legal documents
            results["status"] = "processing"
            processed_docs = self.process_legal_documents(scraped_data)
            results["processed_count"] = len(processed_docs)
            
            # Index in Elasticsearch
            if self.es_client:
                results["status"] = "indexing"
                indexed = self.index_documents(processed_docs, index_name)
                results["indexed"] = indexed
            else:
                logger.warning("Elasticsearch is not configured, skipping indexing")
            
            # Export to CSV
            if export_csv:
                results["status"] = "exporting"
                csv_path = self.export_to_csv(processed_docs)
                results["csv_export_path"] = csv_path
            
            results["status"] = "success"
            logger.info("Full pipeline completed successfully")
            
        except Exception as e:
            logger.error(f"Error in full pipeline: {str(e)}")
            results["status"] = "error"
        
        return results
    
    def scrape_urls(self, urls: List[str], method: str = "playwright", 
                    credentials: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Scrape content from a list of URLs
        
        Args:
            urls: List of URLs to scrape
            method: Scraping method (playwright, selenium, api)
            credentials: Optional credentials for login
            
        Returns:
            List of dictionaries with scraping results
        """
        from implementation.legal_scraping import PlaywrightLegalScraper, UndetectedSeleniumScraper
        scraped_data = []
        
        for url in urls:
            try:
                # Select scraper based on method
                if method == "playwright":
                    scraper = PlaywrightLegalScraper()
                elif method == "selenium":
                    scraper = UndetectedSeleniumScraper()
                elif method == "api":
                    scraper = LegalAPIClient(api_key=self.api_key)
                else:
                    raise ValueError(f"Invalid scraping method: {method}")
                
                # Handle login if needed
                if credentials:
                    scraper._handle_login(None, credentials)
                
                # Scrape the URL
                result = scraper.scrape(url, wait_selector="body")
                scraped_data.append(result)
                
            except Exception as e:
                logger.error(f"Error scraping {url}: {str(e)}")
                scraped_data.append({
                    "success": False,
                    "url": url,
                    "error": str(e)
                })
        
        return scraped_data
    
    def process_legal_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process scraped legal documents to extract key information
        
        Args:
            documents: List of scraped documents
            
        Returns:
            List of processed documents
        """
        processed_documents = []
        
        for document in documents:
            try:
                if document.get("success", False):
                    # Create BeautifulSoup object
                    soup = BeautifulSoup(document["content"], 'html.parser')
                    
                    # Extract case information
                    case_info = self._extract_case_information(soup)
                    
                    # Extract citations
                    citations = self._extract_citations(soup)
                    
                    # Add to document
                    document["case_info"] = case_info
                    document["citations"] = citations
                    
                    processed_documents.append(document)
                else:
                    logger.warning(f"Skipping processing for failed scrape: {document.get('url')}")
                    processed_documents.append(document)
            except Exception as e:
                logger.error(f"Error processing document: {str(e)}")
                document["processing_error"] = str(e)
                processed_documents.append(document)
        
        return processed_documents
    
    def _extract_case_information(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract key information from a legal case using BeautifulSoup
        
        Args:
            soup: BeautifulSoup object representing the HTML content
            
        Returns:
            Dictionary with extracted case information
        """
        case_info = {}
        
        try:
            # Extract title
            title = soup.find("h1", class_="case_title")
            if title:
                case_info["title"] = title.text.strip()
            
            # Extract court
            court = soup.find("span", class_="court_name")
            if court:
                case_info["court"] = court.text.strip()
            
            # Extract date
            date = soup.find("span", class_="date_filed")
            if date:
                case_info["date"] = date.text.strip()
            
            # Extract citations
            citations = soup.find_all("span", class_="citation")
            if citations:
                case_info["citations"] = [c.text.strip() for c in citations]
        
        except Exception as e:
            logger.error(f"Error extracting case information: {str(e)}")
        
        return case_info
    
    def _extract_citations(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract legal citations from a BeautifulSoup object
        
        Args:
            soup: BeautifulSoup object representing the HTML content
            
        Returns:
            List of extracted citations
        """
        citations = []
        
        try:
            # Find all elements with citation class
            citation_elements = soup.find_all("span", class_="citation")
            
            # Extract text from citation elements
            citations = [c.text.strip() for c in citation_elements]
        
        except Exception as e:
            logger.error(f"Error extracting citations: {str(e)}")
        
        return citations
    
    def index_documents(self, documents: List[Dict[str, Any]], index_name: str) -> bool:
        """
        Index legal documents in Elasticsearch
        
        Args:
            documents: List of legal documents
            index_name: Elasticsearch index name
            
        Returns:
            True if indexing was successful, False otherwise
        """
        if not self.es_client:
            logger.warning("Elasticsearch client not initialized, skipping indexing")
            return False
        
        try:
            # Create index if it doesn't exist
            if not self.es_client.indices.exists(index=index_name):
                self.es_client.indices.create(index=index_name)
                logger.info(f"Created Elasticsearch index: {index_name}")
            
            # Index documents
            for document in documents:
                if document.get("success", False):
                    self.es_client.index(index=index_name, document=document)
            
            logger.info(f"Indexed {len(documents)} documents in Elasticsearch")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing documents in Elasticsearch: {str(e)}")
            return False
    
    def export_to_csv(self, documents: List[Dict[str, Any]]) -> Optional[str]:
        """
        Export processed legal documents to a CSV file
        
        Args:
            documents: List of processed legal documents
            
        Returns:
            Path to the CSV file or None if export failed
        """
        try:
            # Create a Pandas DataFrame from the documents
            df = pd.DataFrame(documents)
            
            # Create a timestamped filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            csv_filename = f"legal_data_{timestamp}.csv"
            csv_path = os.path.join(self.output_dir, csv_filename)
            
            # Export to CSV
            df.to_csv(csv_path, index=False)
            logger.info(f"Exported data to CSV: {csv_path}")
            return csv_path
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return None

def demo():
    """Run a demonstration of the legal data pipeline"""
    # Example usage
    pipeline = LegalDataPipeline()
    
    # Sample URLs
    urls = [
        "https://www.courtlistener.com/opinion/4801970/oracle-america-inc-v-google-llc/",
        "https://law.justia.com/cases/federal/appellate-courts/ca9/10-15612/10-15612-2012/"]
    
    # Scrape URLs
    scraped_data = pipeline.scrape_urls(urls)
    
    # Process legal documents
    processed_data = pipeline.process_legal_documents(scraped_data)
    
    # Print results
    print(json.dumps(processed_data, indent=2))

if __name__ == "__main__":
    demo()
