"""
Legal Data Pipeline - End-to-end system for legal data scraping, processing, and analysis
"""
import os
import sys
import json
import time
import logging
import requests
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from elasticsearch import Elasticsearch
from datetime import datetime
import concurrent.futures
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import DeepSoul components
from implementation.legal_scraping import (
    PlaywrightLegalScraper, UndetectedSeleniumScraper, LegalAPIClient, scrape_court_info
)

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
            elasticsearch_host: Elasticsearch host URL or None to disable
            output_dir: Directory to store scraped data
            max_workers: Maximum number of concurrent workers for scraping
            api_key: API key for legal data services
        """
        self.output_dir = output_dir
        self.max_workers = max_workers
        self.api_key = api_key
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize scrapers
        self.playwright_scraper = PlaywrightLegalScraper(output_dir=output_dir)
        self.selenium_scraper = UndetectedSeleniumScraper(output_dir=output_dir)
        self.api_client = LegalAPIClient(api_key=api_key)
        
        # Initialize Elasticsearch if host provided
        self.elasticsearch = None
        if elasticsearch_host:
            try:
                self.elasticsearch = Elasticsearch(elasticsearch_host)
                logger.info(f"Connected to Elasticsearch at {elasticsearch_host}")
            except Exception as e:
                logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
    
    def scrape_urls(self, urls: List[str], method: str = "playwright", 
                  credentials: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs in parallel
        
        Args:
            urls: List of URLs to scrape
            method: Scraping method to use
            credentials: Optional login credentials
            
        Returns:
            List of dictionaries containing scraped data
        """
        results = []
        
        logger.info(f"Starting parallel scraping of {len(urls)} URLs using {method}")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Create futures for each URL
            future_to_url = {
                executor.submit(scrape_court_info, url, method, credentials): url
                for url in urls
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    data = future.result()
                    results.append(data)
                    logger.info(f"Successfully scraped {url}")
                except Exception as e:
                    logger.error(f"Error scraping {url}: {str(e)}")
                    results.append({"url": url, "error": str(e), "success": False})
        
        return results
    
    def process_legal_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process scraped legal documents to extract structured data
        
        Args:
            documents: List of scraped document data
            
        Returns:
            List of processed documents with structured data
        """
        processed_docs = []
        
        for doc in documents:
            if not doc.get("success", False) or "content" not in doc:
                processed_docs.append(doc)  # Keep error documents unchanged
                continue
            
            try:
                # Extract ID or create one from URL
                doc_id = doc.get("id") or hashlib.md5(doc["url"].encode()).hexdigest()
                
                # Process HTML content
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(doc["content"], 'html.parser')
                
                # Extract clean text content
                main_content = soup.find("main") or soup.find("div", class_="main-content") or soup
                text_content = main_content.get_text(separator="\n", strip=True)
                
                # Basic structure extraction - would be more sophisticated in production
                sections = self._extract_document_sections(soup)
                case_info = self._extract_case_information(soup)
                citations = self._extract_citations(soup)
                
                # Create processed document
                processed_doc = {
                    "id": doc_id,
                    "url": doc["url"],
                    "timestamp": doc["timestamp"],
                    "text_content": text_content,
                    "sections": sections,
                    "case_info": case_info,
                    "citations": citations,
                    "word_count": len(text_content.split()),
                    "processed_at": datetime.now().isoformat()
                }
                
                processed_docs.append(processed_doc)
                logger.info(f"Processed document from {doc['url']}")
                
            except Exception as e:
                logger.error(f"Error processing document from {doc['url']}: {str(e)}")
                doc["processing_error"] = str(e)
                processed_docs.append(doc)
        
        return processed_docs
    
    def _extract_document_sections(self, soup) -> List[Dict[str, str]]:
        """Extract document sections from BeautifulSoup object"""
        sections = []
        
        # Extract sections based on headers
        current_section = {"title": "Introduction", "content": ""}
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p']):
            if element.name.startswith('h'):
                # Save previous section if it has content
                if current_section["content"].strip():
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    "title": element.get_text(strip=True),
                    "content": ""
                }
            elif element.name == 'p':
                # Add paragraph to current section
                current_section["content"] += element.get_text(strip=True) + "\n\n"
        
        # Add the last section if it has content
        if current_section["content"].strip():
            sections.append(current_section)
        
        return sections
    
    def _extract_case_information(self, soup) -> Dict[str, str]:
        """Extract case information from BeautifulSoup object"""
        case_info = {}
        
        # Look for case metadata
        case_name_elem = soup.find("h1") or soup.find("title")
        if case_name_elem:
            case_info["case_name"] = case_name_elem.get_text(strip=True)
        
        # Look for date patterns
        import re
        date_patterns = [
            r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, soup.get_text())
            if match:
                case_info["date"] = match.group(0)
                break
        
        # Look for court name
        court_indicators = ["court of", "district court", "supreme court", "circuit"]
        text = soup.get_text().lower()
        for indicator in court_indicators:
            idx = text.find(indicator)
            if idx != -1:
                # Extract surrounding text
                start = max(0, idx - 20)
                end = min(len(text), idx + len(indicator) + 30)
                court_text = text[start:end]
                case_info["court"] = court_text.strip()
                break
        
        # Look for case number patterns
        case_num_pattern = r'(?:No\.|Case No\.|Docket No\.)?\s*\d+-[A-Za-z]+-\d+'
        match = re.search(case_num_pattern, soup.get_text())
        if match:
            case_info["case_number"] = match.group(0)
        
        return case_info
    
    def _extract_citations(self, soup) -> List[str]:
        """Extract legal citations from BeautifulSoup object"""
        citations = []
        
        # Common citation patterns (simplified)
        citation_patterns = [
            r'\d+\s+U\.S\.\s+\d+',  # US Reports
            r'\d+\s+S\.Ct\.\s+\d+',  # Supreme Court Reporter
            r'\d+\s+F\.\d[d|rd]\s+\d+',  # Federal Reporter
            r'\d+\s+F\.Supp\.\s*\d*\s+\d+'  # Federal Supplement
        ]
        
        import re
        text = soup.get_text()
        
        for pattern in citation_patterns:
            for match in re.finditer(pattern, text):
                citations.append(match.group(0))
        
        return citations
    
    def index_documents(self, documents: List[Dict[str, Any]], index_name: str = "legal_documents") -> bool:
        """
        Index processed documents in Elasticsearch
        
        Args:
            documents: List of processed documents to index
            index_name: Name of the Elasticsearch index
            
        Returns:
            True if successful, False otherwise
        """
        if not self.elasticsearch:
            logger.warning("Elasticsearch not configured. Skipping indexing.")
            return False
        
        # Create index if it doesn't exist
        if not self.elasticsearch.indices.exists(index=index_name):
            logger.info(f"Creating Elasticsearch index '{index_name}'")
            try:
                # Define index mapping
                mapping = {
                    "mappings": {
                        "properties": {
                            "text_content": {"type": "text"},
                            "url": {"type": "keyword"},
                            "case_info.case_name": {"type": "text"},
                            "case_info.court": {"type": "keyword"},
                            "case_info.date": {"type": "date", "format": "yyyy-MM-dd||MM/dd/yyyy||MMMM d, yyyy||date_time"},
                            "processed_at": {"type": "date", "format": "date_time_no_millis||date_time"}
                        }
                    }
                }
                self.elasticsearch.indices.create(index=index_name, body=mapping)
            except Exception as e:
                logger.error(f"Error creating Elasticsearch index: {str(e)}")
                return False
        
        # Index documents
        try:
            logger.info(f"Indexing {len(documents)} documents in Elasticsearch")
            success_count = 0
            
            for doc in documents:
                if not doc.get("id"):
                    doc["id"] = hashlib.md5(doc["url"].encode()).hexdigest()
                
                # Index the document
                result = self.elasticsearch.index(
                    index=index_name,
                    id=doc["id"],
                    body=doc
                )
                
                if result.get("result") in ["created", "updated"]:
                    success_count += 1
            
            logger.info(f"Successfully indexed {success_count}/{len(documents)} documents")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Error indexing documents: {str(e)}")
            return False
    
    def search_legal_documents(self, query: str, index_name: str = "legal_documents", 
                              size: int = 10) -> List[Dict[str, Any]]:
        """
        Search for legal documents in Elasticsearch
        
        Args:
            query: Search query
            index_name: Name of the Elasticsearch index
            size: Maximum number of results to return
            
        Returns:
            List of matching documents
        """
        if not self.elasticsearch:
            logger.warning("Elasticsearch not configured. Cannot search.")
            return []
        
        try:
            search_body = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["text_content^2", "case_info.case_name^3", "sections.content"]
                    }
                },
                "highlight": {
                    "fields": {
                        "text_content": {},
                        "case_info.case_name": {}
                    }
                },
                "size": size
            }
            
            logger.info(f"Searching for '{query}' in Elasticsearch")
            result = self.elasticsearch.search(index=index_name, body=search_body)
            
            # Process and return results
            hits = result.get("hits", {}).get("hits", [])
            documents = []
            
            for hit in hits:
                doc = hit["_source"]
                doc["score"] = hit["_score"]
                doc["highlights"] = hit.get("highlight", {})
                documents.append(doc)
            
            logger.info(f"Found {len(documents)} documents matching '{query}'")
            return documents
            
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def analyze_with_llm(self, 
                       documents: List[Dict[str, Any]], 
                       analysis_type: str = "summary", 
                       model: Optional[Any] = None) -> Dict[str, Any]:
        """
        Analyze legal documents using a language model
        
        Args:
            documents: List of documents to analyze
            analysis_type: Type of analysis to perform (summary, argument_extraction, precedent_analysis)
            model: Optional language model instance (if None, will use LangChain defaults)
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Import required LangChain components for text processing and AI extraction
            try:
                from langchain.llms import OpenAI
                from langchain.chains.summarize import load_summarize_chain
                from langchain.text_splitter import RecursiveCharacterTextSplitter
                from langchain.docstore.document import Document as LangchainDocument
            except ImportError:
                logger.error("LangChain not installed. Please install with: pip install langchain")
                return {"error": "LangChain not installed", "status": "failed"}
            
            # Initialize model if not provided
            if model is None:
                try:
                    model = OpenAI(temperature=0)
                except Exception as e:
                    logger.error(f"Error initializing OpenAI model: {str(e)}")
                    return {"error": str(e), "status": "failed"}
            
            # Initialize text splitter for long documents
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=4000,
                chunk_overlap=400,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
            
            # Process each document
            results = {}
            
            for doc in documents:
                doc_id = doc.get("id")
                if not doc_id:
                    continue
                    
                text_content = doc.get("text_content", "")
                if not text_content:
                    continue
                
                # Split text into chunks
                chunks = text_splitter.split_text(text_content)
                
                # Convert to LangChain documents
                langchain_docs = [LangchainDocument(page_content=chunk) for chunk in chunks]
                
                # Select analysis type
                if analysis_type == "summary":
                    chain = load_summarize_chain(model, chain_type="map_reduce")
                    result = chain.run(langchain_docs)
                    results[doc_id] = {"summary": result}
                    
                elif analysis_type == "argument_extraction":
                    # Specialized prompt for legal argument extraction
                    prompt = """
                    Extract the main legal arguments from this text. For each argument, identify:
                    1. The claim being made
                    2. The evidence or precedent cited
                    3. The reasoning connecting evidence to claim
                    
                    Text: {text}
                    
                    Legal Arguments:
                    """
                    # Process each chunk and combine results
                    all_arguments = []
                    for chunk in chunks:
                        result = model(prompt.format(text=chunk))
                        all_arguments.append(result)
                        
                    results[doc_id] = {"arguments": all_arguments}
                
                elif analysis_type == "precedent_analysis":
                    # Extract and analyze precedents
                    citations = doc.get("citations", [])
                    precedent_analyses = []
                    
                    for citation in citations:
                        analysis = model(f"""
                        Analyze the significance of this legal citation: {citation}
                        Explain what this case established and how it's being applied in the current context.
                        """)
                        precedent_analyses.append({
                            "citation": citation,
                            "analysis": analysis
                        })
                    
                    results[doc_id] = {"precedent_analyses": precedent_analyses}
                
                else:
                    # Generic analysis
                    result = model(f"Analyze this legal text: {text_content[:2000]}...")
                    results[doc_id] = {"analysis": result}
            
            return {
                "status": "success",
                "analysis_type": analysis_type,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error analyzing documents with LLM: {str(e)}")
            return {"error": str(e), "status": "failed"}
    
    def export_to_csv(self, documents: List[Dict[str, Any]], filepath: str = None) -> str:
        """
        Export documents to CSV file
        
        Args:
            documents: List of documents to export
            filepath: Output filepath (if None, generates a timestamped filename)
            
        Returns:
            Path to the exported CSV file
        """
        if not documents:
            logger.warning("No documents to export")
            return None
            
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(self.output_dir, f"legal_data_{timestamp}.csv")
            
        try:
            # Flatten documents for CSV export
            flattened_data = []
            for doc in documents:
                flat_doc = {
                    "id": doc.get("id", ""),
                    "url": doc.get("url", ""),
                    "timestamp": doc.get("timestamp", ""),
                    "word_count": doc.get("word_count", 0),
                    "processed_at": doc.get("processed_at", "")
                }
                
                # Add case info
                case_info = doc.get("case_info", {})
                for key, value in case_info.items():
                    flat_doc[f"case_{key}"] = value
                
                # Add first few citations
                citations = doc.get("citations", [])
                for i, citation in enumerate(citations[:5]):
                    flat_doc[f"citation_{i+1}"] = citation
                
                # Truncate text content for CSV export
                text_content = doc.get("text_content", "")
                if text_content:
                    flat_doc["text_excerpt"] = text_content[:500] + ("..." if len(text_content) > 500 else "")
                
                flattened_data.append(flat_doc)
            
            # Convert to DataFrame and export
            df = pd.DataFrame(flattened_data)
            df.to_csv(filepath, index=False)
            logger.info(f"Exported {len(documents)} documents to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return None
    
    def run_full_pipeline(self, 
                         urls: List[str], 
                         scrape_method: str = "playwright",
                         index_name: str = "legal_documents",
                         analyze: bool = False,
                         export_csv: bool = False) -> Dict[str, Any]:
        """
        Run the complete legal data pipeline
        
        Args:
            urls: List of URLs to scrape
            scrape_method: Method to use for scraping
            index_name: Elasticsearch index name
            analyze: Whether to perform LLM analysis
            export_csv: Whether to export results to CSV
            
        Returns:
            Dictionary with pipeline results
        """
        results = {
            "status": "success",
            "started_at": datetime.now().isoformat(),
            "urls_count": len(urls)
        }
        
        try:
            # 1. Scrape URLs
            logger.info(f"Running full pipeline for {len(urls)} URLs")
            scraped_documents = self.scrape_urls(urls, method=scrape_method)
            results["scraped_count"] = len(scraped_documents)
            results["successful_scrape_count"] = sum(1 for doc in scraped_documents if doc.get("success", False))
            
            # 2. Process documents
            processed_documents = self.process_legal_documents(scraped_documents)
            results["processed_count"] = len(processed_documents)
            
            # 3. Index documents if Elasticsearch is configured
            if self.elasticsearch:
                indexing_success = self.index_documents(processed_documents, index_name=index_name)
                results["indexed"] = indexing_success
            else:
                results["indexed"] = False
            
            # 4. Run LLM analysis if requested
            if analyze:
                analysis_results = self.analyze_with_llm(processed_documents, analysis_type="summary")
                results["analysis"] = analysis_results.get("results", {})
            
            # 5. Export to CSV if requested
            if export_csv:
                csv_path = self.export_to_csv(processed_documents)
                results["csv_export_path"] = csv_path
            
            results["completed_at"] = datetime.now().isoformat()
            
            # Save pipeline results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_path = os.path.join(self.output_dir, f"pipeline_results_{timestamp}.json")
            with open(results_path, "w") as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Pipeline completed successfully. Results saved to {results_path}")
            return results
            
        except Exception as e:
            logger.error(f"Error running pipeline: {str(e)}")
            results["status"] = "failed"
            results["error"] = str(e)
            results["completed_at"] = datetime.now().isoformat()
            return results


def demo():
    """Run a demo of the legal data pipeline"""
    # Example URLs
    urls = [
        "https://www.courtlistener.com/opinion/4801970/oracle-america-inc-v-google-llc/",
        "https://www.courtlistener.com/opinion/2741300/riley-v-california/"
    ]
    
    # Initialize pipeline without Elasticsearch
    pipeline = LegalDataPipeline(output_dir="demo_legal_data")
    
    # Run pipeline with just scraping and processing
    results = pipeline.run_full_pipeline(
        urls=urls,
        scrape_method="playwright",
        export_csv=True
    )
    
    print("Pipeline demo completed!")
    print(f"Scraped: {results['scraped_count']} documents")
    print(f"Successfully scraped: {results['successful_scrape_count']} documents")
    print(f"Processed: {results['processed_count']} documents")
    if "csv_export_path" in results:
        print(f"Results exported to: {results['csv_export_path']}")


if __name__ == "__main__":
    demo()
