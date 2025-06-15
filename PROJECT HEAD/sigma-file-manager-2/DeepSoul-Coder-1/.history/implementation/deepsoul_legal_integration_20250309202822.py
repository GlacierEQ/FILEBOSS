"""
DeepSoul Legal Integration - Integration of legal data capabilities with DeepSoul
"""
import os
import sys
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import DeepSoul components
from implementation.legal_scraping import (
    PlaywrightLegalScraper, UndetectedSeleniumScraper, LegalAPIClient, scrape_court_info
)
from implementation.legal_data_pipeline import LegalDataPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("DeepSoul-LegalIntegration")


class LegalAssistant:
    """
    Legal assistant for DeepSoul that integrates legal data capabilities
    """
    
    def __init__(self, 
                model=None,
                tokenizer=None,
                elasticsearch_host: Optional[str] = None,
                api_keys: Dict[str, str] = None,
                output_dir: str = "legal_assistant"):
        """
        Initialize the legal assistant
        
        Args:
            model: Optional language model 
            tokenizer: Optional tokenizer
            elasticsearch_host: Optional Elasticsearch host
            api_keys: Dictionary of API keys for legal services
            output_dir: Directory to store output
        """
        self.model = model
        self.tokenizer = tokenizer
        self.elasticsearch_host = elasticsearch_host
        self.api_keys = api_keys or {}
        self.output_dir = output_dir
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize pipeline
        self.pipeline = LegalDataPipeline(
            elasticsearch_host=elasticsearch_host,
            output_dir=output_dir,
            api_key=self.api_keys.get("courtlistener")
        )
        
        # Initialize knowledge base for case law
        self.case_knowledge = {}
    
    def research_legal_topic(self, topic: str, 
                           sources: List[str] = None, 
                           depth: int = 1) -> Dict[str, Any]:
        """
        Research a legal topic using available sources
        
        Args:
            topic: The legal topic to research
            sources: List of sources to use (case_law, statutes, articles)
            depth: Depth of research (1=basic, 2=moderate, 3=comprehensive)
            
        Returns:
            Dictionary with research results
        """
        results = {
            "topic": topic,
            "sources_used": [],
            "timestamp": datetime.now().isoformat(),
            "results": {},
            "summary": None
        }
        
        sources = sources or ["case_law"]
        
        try:
            # Search case law if requested
            if "case_law" in sources:
                logger.info(f"Searching case law for topic: {topic}")
                
                # Search for relevant cases using CourtListener API
                api_client = LegalAPIClient(api_key=self.api_keys.get("courtlistener"))
                search_results = api_client.search_courtlistener(topic, page=1)
                
                if "results" in search_results and search_results["results"]:
                    # Process top results based on depth
                    max_cases = 3 if depth == 1 else (6 if depth == 2 else 10)
                    cases_to_process = search_results["results"][:max_cases]
                    
                    case_urls = []
                    for case in cases_to_process:
                        if "absolute_url" in case:
                            base_url = "https://www.courtlistener.com"
                            case_urls.append(base_url + case["absolute_url"])
                    
                    # Scrape and process case data
                    if case_urls:
                        scraped_docs = self.pipeline.scrape_urls(case_urls, method="api")
                        processed_docs = self.pipeline.process_legal_documents(scraped_docs)
                        
                        # Store in results
                        results["results"]["case_law"] = {
                            "count": len(processed_docs),
                            "cases": processed_docs
                        }
                        results["sources_used"].append("case_law")
                
            # Search law journals and articles if requested
            if "articles" in sources and depth >= 2:
                # This would require integration with additional APIs or scrapers
                # Placeholder for now
                results["results"]["articles"] = {
                    "count": 0,
                    "note": "Article search not implemented yet"
                }
            
            # Generate summary if model is available
            if self.model is not None and self.tokenizer is not None:
                # Create a summary prompt based on the collected information
                prompt = f"Summarize the legal research on the topic '{topic}' based on the following information:\n\n"
                
                # Add case law information
                if "case_law" in results["results"]:
                    cases = results["results"]["case_law"]["cases"]
                    for i, case in enumerate(cases[:3]):  # Summarize up to 3 cases
                        if "case_info" in case:
                            case_name = case["case_info"].get("case_name", f"Case {i+1}")
                            prompt += f"Case: {case_name}\n"
                            
                            # Add excerpt if available
                            text = case.get("text_content", "")
                            if text:
                                excerpt = text[:500] + "..." if len(text) > 500 else text
                                prompt += f"Excerpt: {excerpt}\n\n"
                
                # Generate summary
                inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
                outputs = self.model.generate(
                    input_ids=inputs.input_ids,
                    attention_mask=inputs.attention_mask,
                    max_length=500,
                    do_sample=True,
                    top_p=0.95,
                    temperature=0.7
                )
                summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                
                # Extract just the summary part (remove the prompt)
                if summary.startswith(prompt):
                    summary = summary[len(prompt):].strip()
                
                results["summary"] = summary
            
            return results
            
        except Exception as e:
            logger.error(f"Error researching legal topic: {str(e)}")
            results["error"] = str(e)
            return results
    
    def analyze_legal_document(self, document_path: str, analysis_type: str = "summary") -> Dict[str, Any]:
        """
        Analyze a legal document
        
        Args:
            document_path: Path to the document to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            Analysis results
        """
        try:
            # Read document
            with open(document_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Process the document
            processed_doc = {
                "id": os.path.basename(document_path),
                "text_content": text,
                "source": "local_file"
            }
            
            # Use the pipeline's analyze method
            analysis_results = self.pipeline.analyze_with_llm(
                [processed_doc],
                analysis_type=analysis_type,
                model=self.model
            )
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Error analyzing legal document: {str(e)}")
            return {"error": str(e), "status": "failed"}
    
    def extract_citations(self, text: str) -> List[str]:
        """
        Extract legal citations from text
        
        Args:
            text: Text to extract citations from
            
        Returns:
            List of extracted citations
        """
        import re
        
        # Common citation patterns
        citation_patterns = [
            r'\d+\s+U\.S\.\s+\d+',  # US Reports
            r'\d+\s+S\.Ct\.\s+\d+',  # Supreme Court Reporter
            r'\d+\s+F\.\d[d|rd]\s+\d+',  # Federal Reporter
            r'\d+\s+F\.Supp\.\s*\d*\s+\d+'  # Federal Supplement
        ]
        
        citations = []
        for pattern in citation_patterns:
            for match in re.finditer(pattern, text):
                citations.append(match.group(0))
        
        return citations
    
    def get_case_by_citation(self, citation: str) -> Dict[str, Any]:
        """
        Search for a case by citation
        
        Args:
            citation: Citation to search for
            
        Returns:
            Case information if found
        """
        # Use the CourtListener API to search for the citation
        api_client = LegalAPIClient(api_key=self.api_keys.get("courtlistener"))
        search_results = api_client.search_courtlistener(citation, page=1)
        
        if "results" in search_results and search_results["results"]:
            # Process the first result
            case = search_results["results"][0]
            
            # Get the full case data if we have a URL
            if "absolute_url" in case:
                base_url = "https://www.courtlistener.com"
                case_url = base_url + case["absolute_url"]
                
                # Scrape and process case data
                scraped_data = scrape_court_info(case_url, method="api")
                processed_data = self.pipeline.process_legal_documents([scraped_data])
                
                if processed_data:
                    return processed_data[0]
        
        return {"status": "not_found", "citation": citation}
    
    def compare_legal_texts(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Compare two legal texts to identify similarities and differences
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Comparison results
        """
        if not self.model or not self.tokenizer:
            return {"error": "Model required for text comparison"}
        
        # Create a prompt for comparison
        prompt = f"""Compare and contrast the following two legal texts:

TEXT 1:
{text1[:1000]}...

TEXT 2:
{text2[:1000]}...

Provide an analysis of:
1. Key similarities in legal principles or arguments
2. Important differences in reasoning or conclusions
3. Overall assessment of how these texts relate to each other
"""
        
        # Generate comparison
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            input_ids=inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_length=800,
            do_sample=True,
            top_p=0.95,
            temperature=0.7
        )
        comparison = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the comparison part (remove the prompt)
        if comparison.startswith(prompt):
            comparison = comparison[len(prompt):].strip()
        
        return {
            "comparison": comparison,
            "text1_length": len(text1),
            "text2_length": len(text2),
            "text1_citations": self.extract_citations(text1),
            "text2_citations": self.extract_citations(text2)
        }
    
    def generate_legal_document(self, document_type: str, parameters: Dict[str, Any]) -> str:
        """
        Generate a legal document based on provided parameters
        
        Args:
            document_type: Type of document to generate
            parameters: Parameters for document generation
            
        Returns:
            Generated document text
        """
        if not self.model or not self.tokenizer:
            return "Error: Model required for document generation"
        
        # Create a prompt based on document type
        if document_type == "brief":
            prompt = f"""Generate a legal brief with the following parameters:
Title: {parameters.get('title', 'Legal Brief')}
Issue: {parameters.get('issue', 'The legal issue to be addressed')}
Client: {parameters.get('client', 'The client')}
Court: {parameters.get('court', 'The court')}
Key Facts: {parameters.get('facts', 'The key facts of the case')}
Key Arguments: {parameters.get('arguments', 'The key legal arguments')}
Relief Sought: {parameters.get('relief', 'The relief sought')}

Generate a professional legal brief addressing the above issue, suitable for filing with {parameters.get('court', 'the court')}:
"""
        
        elif document_type == "memo":
            prompt = f"""Generate a legal memorandum with the following parameters:
To: {parameters.get('to', 'Recipient')}
From: {parameters.get('from', 'Sender')}
Date: {datetime.now().strftime('%B %d, %Y')}
Re: {parameters.get('subject', 'Legal Issue')}

Issue: {parameters.get('issue', 'The legal issue to be addressed')}
Facts: {parameters.get('facts', 'The relevant facts')}
Question: {parameters.get('question', 'The legal question to be answered')}

Generate a professional legal memorandum addressing the above issue:
"""
        
        else:
            prompt = f"""Generate a generic legal document of type: {document_type}
With the following parameters:
"""
            for key, value in parameters.items():
                prompt += f"{key}: {value}\n"
        
        # Generate document
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            input_ids=inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_length=2000,
            do_sample=True,
            top_p=0.92,
            temperature=0.8
        )
        document = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the document part (remove the prompt)
        if document.startswith(prompt):
            document = document[len(prompt):].strip()
        
        return document
    
    def search_legal_database(self, query: str, database: str = "courtlistener", 
                            max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search a legal database for relevant cases or statutes
        
        Args:
            query: Search query
            database: Database to search
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        if database == "courtlistener":
            # Use the CourtListener API
            api_client = LegalAPIClient(api_key=self.api_keys.get("courtlistener"))
            search_results = api_client.search_courtlistener(query, page=1)
            
            if "results" in search_results:
                # Process results
                results = []
                for case in search_results["results"][:max_results]:
                    results.append({
                        "title": case.get("caseName", "Unknown case"),
                        "date": case.get("dateFiled", "Unknown date"),
                        "court": case.get("court", "Unknown court"),
                        "url": f"https://www.courtlistener.com{case.get('absolute_url', '')}",
                        "snippet": case.get("snippet", ""),
                        "source": "courtlistener"
                    })
                return results
        
        # Default empty response for unsupported databases
        return []

def demo():
    """Run a demonstration of the legal integration"""
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    
    print("Initializing legal assistant...")
    
    # Load a small model for demonstration
    model_name = "deepseek-ai/deepseek-coder-1.3b-instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, 
        trust_remote_code=True,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )
    
    # Move model to appropriate device
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)
    
    # Create legal assistant
    legal_assistant = LegalAssistant(
        model=model,
        tokenizer=tokenizer,
        output_dir="legal_assistant_demo"
    )
    
    # Research a legal topic
    print("\nResearching legal topic: 'fair use copyright'...")
    results = legal_assistant.research_legal_topic(
        topic="fair use copyright",
        depth=1
    )
    
    # Print summary if available
    if results.get("summary"):
        print("\nResearch Summary:")
        print(results["summary"])
    else:
        print("\nNo summary available.")
    
    # Extract citations from a sample text
    sample_text = """
    The court in Sony Corp. of America v. Universal City Studios, Inc., 464 U.S. 417 (1984), 
    established the concept of "time shifting" as fair use. Later, in Campbell v. Acuff-Rose Music, 
    510 U.S. 569 (1994), the Court emphasized the importance of transformative use.
    """
    
    print("\nExtracting citations from sample text...")
    citations = legal_assistant.extract_citations(sample_text)
    print(f"Found {len(citations)} citations:")
    for citation in citations:
        print(f"- {citation}")
    
    print("\nDemo completed!")

if __name__ == "__main__":
    demo()
