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
from utils.config_manager import ConfigManager

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
            # Placeholder implementation
            results["status"] = "success"
            results["message"] = f"Research complete for topic: {topic}"
            return results
            
        except Exception as e:
            logger.error(f"Error researching legal topic: {str(e)}")
            results["status"] = "error"
            results["message"] = str(e)
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
            # Placeholder implementation
            return {"status": "success", "message": f"Document analyzed ({analysis_type})"}
        except Exception as e:
            logger.error(f"Error analyzing legal document: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def extract_citations(self, text: str) -> List[str]:
        """
        Extract legal citations from text
        
        Args:
            text: Text to extract citations from
            
        Returns:
            List of extracted citations
        """
        citations = []
        
        # Common citation patterns
        citation_patterns = [
            r'\d+\s+U\.S\.\s+\d+',            r'\d+\s+S\.Ct\.\s+\d+',            r'\d+\s+F\.\d[d|rd]\s+\d+',            r'\d+\s+F\.Supp\.\s*\d*\s+\d+'        ]
        
        citations = []
        for pattern in citation_patterns:
            # Placeholder implementation
            pass
        
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
            # Placeholder implementation
            return {"status": "success", "citation": citation, "case_name": "Sample Case"}
        
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
            return {"status": "error", "message": "Model and tokenizer are required for text comparison"}
        
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
            return "Error: Model and tokenizer are required for document generation"
        
        # Create a prompt based on document type
        if document_type == "brief":
            prompt = f"""Generate a legal brief with the following parameters:
            {json.dumps(parameters, indent=2)}"""
        
        elif document_type == "memo":
            prompt = f"""Generate a legal memo with the following parameters:
            {json.dumps(parameters, indent=2)}"""
        
        else:
            return f"Error: Unknown document type: {document_type}"
        
        # Generate document
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            input_ids=inputs.input_ids,
            attention_mask=inputs.attention_mask,
            max_length=1024,
            do_sample=True,
            top_p=0.95,
            temperature=0.7
        )
        document = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return document
    
    def search_legal_database(self, query: str, database: str = "courtlistener", 
                            max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search a legal database for relevant documents
        
        Args:
            query: Search query
            database: Database to search (default: courtlistener)
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        try:
            # Use the CourtListener API to search for the query
            api_client = LegalAPIClient(api_key=self.api_keys.get("courtlistener"))
            search_results = api_client.search_courtlistener(query, page=1)
            
            if "results" in search_results and search_results["results"]:
                # Return the results
                return search_results["results"][:max_results]
            else:
                return []
        except Exception as e:
            logger.error(f"Error searching legal database: {str(e)}")
            return []

    def _parse_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """Parse analysis text into structured format"""
        # Simple parsing - in production this would use more sophisticated parsing
        sections = {
            "overview": "",
            "components": [],
            "bugs": [],
            "improvements": [],
            "full_analysis": analysis_text
        }
        
        # Extract components
        if "components" in analysis_text.lower() or "functions" in analysis_text.lower():
            # Simple extraction based on bullet points or numbered lists
            components_section = self._extract_section(analysis_text, ["components", "functions"])
            sections["components"] = self._extract_list_items(components_section)
        
        # Extract bugs
        if "bugs" in analysis_text.lower() or "issues" in analysis_text.lower():
            bugs_section = self._extract_section(analysis_text, ["bugs", "issues"])
            sections["bugs"] = self._extract_list_items(bugs_section)
        
        # Extract improvements
        if "improvements" in analysis_text.lower() or "suggestions" in analysis_text.lower():
            improvements_section = self._extract_section(analysis_text, ["improvements", "suggestions"])
            sections["improvements"] = self._extract_list_items(improvements_section)
        
        # Extract overview
        overview = analysis_text.split("\n\n")[0] if analysis_text else ""
        sections["overview"] = overview.strip()
        
        return sections

    def _extract_section(self, text: str, section_names: List[str]) -> str:
        """Extract a section from analysis text"""
        lines = text.split("\n")
        section_content = []
        in_section = False
        
        for i, line in enumerate(lines):
            # Check if this line starts a section
            lower_line = line.lower()
            if any(name in lower_line for name in section_names) and (":" in line or "#" in line):
                in_section = True
                continue
            
            # Check if this line starts the next section
            if in_section and i < len(lines) - 1:
                next_line = lines[i+1].lower()
                if next_line.strip().endswith(":") or next_line.startswith("#"):
                    break
            
            # Add line to section if we're in the section
            if in_section:
                section_content.append(line)
        
        return "\n".join(section_content)

    def _extract_list_items(self, text: str) -> List[str]:
        """Extract list items from text"""
        items = []
        lines = text.split("\n")
        
        for line in lines:
            # Check for bullet points or numbered list items
            stripped = line.strip()
            if stripped.startswith("- ") or stripped.startswith("* "):
                items.append(stripped[2:])
            elif stripped.startswith("• "):
                items.append(stripped[2:])
            elif stripped.startswith(("1. ", "2. ", "3. ", "4. ", "5. ")):
                items.append(stripped[3:])
        
        return items

    def enhance_code(self, code: str, language: str, 
                    enhancement_type: str = "general",
                    max_tokens: int = 1024) -> Dict[str, Any]:
        """
        Enhance code with improvements or fixes
        
        Args:
            code: Code to enhance
            language: Programming language of the code
            enhancement_type: Type of enhancement (general, optimize, fix, document)
            max_tokens: Maximum number of tokens for the response
            
        Returns:
            Dictionary with enhanced code and explanation
        """
        # Check if model is loaded
        if not self.status["model_loaded"]:
            raise RuntimeError("Model is not loaded")
        
        # Create prompt
        prompt = self._create_enhancement_prompt(code, language, enhancement_type)
        
        # Generate enhanced code
        with self.lock:
            enhancement_text = self.generator.generate(
                prompt=prompt,
                max_new_tokens=max_tokens,
                temperature=0.2,
                top_p=0.95
            )
        
        # Parse enhanced code
        enhanced_code, explanation = self._parse_enhancement(enhancement_text, language)
        
        # Build result
        result = {
            "original_code": code,
            "enhanced_code": enhanced_code,
            "explanation": explanation,
            "enhancement_type": enhancement_type,
            "language": language,
            "timestamp": time.time()
        }
        
        return result

    def _create_enhancement_prompt(self, code: str, language: str, enhancement_type: str) -> str:
        """Create prompt for code enhancement"""
        enhancement_instructions = {
            "general": "Improve this code with better practices, optimizations, and clearer structure.",
            "optimize": "Optimize this code for better performance and efficiency.",
            "fix": "Fix any bugs or issues in this code.",
            "document": "Add comprehensive documentation to this code."
        }
        
        instruction = enhancement_instructions.get(
            enhancement_type, 
            enhancement_instructions["general"]
        )
        
        return f"""{instruction}

Code:
{code}
"""

def demo():rse_knowledge_items(self, analysis_text: str, source: str) -> List[Dict[str, Any]]:
    """Run a demonstration of the legal integration"""""
    from transformers import AutoTokenizer, AutoModelForCausalLM
        items = []
    print("Initializing legal assistant...")
        # Split by knowledge items (assuming they're separated by titles)
    # Load a small model for demonstrationt would need improvement
    model_name = "deepseek-ai/deepseek-coder-1.3b-instruct"
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, 
        trust_remote_code=True,:
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    )           continue
                
    # Move model to appropriate devicetem (starts with a title-like line)
    device = "cuda" if torch.cuda.is_available() else "cpu"th("## ") or ":" in section.split("\n")[0]:
    model = model.to(device)ous item if exists
                if current_item:
    # Create legal assistantpend(current_item)
    legal_assistant = LegalAssistant(
        model=model,art new item
        tokenizer=tokenizer, = {
        output_dir="legal_assistant_demo"t("\n")[0].strip("# :"),
    )               "description": "",
                    "category": "Unknown",
    # Research a legal topic": "",
    print("\nResearching legal topic: 'fair use copyright'...")
    results = legal_assistant.research_legal_topic(
        topic="fair use copyright",
        depth=1 
    )           # Add remaining lines to description
                if "\n" in section:
    # Print summary if available["description"] = "\n".join(section.split("\n")[1:]).strip()
    if results.get("summary"):
        print(f"Summary: {results['summary']}") a category
    else:       if "Category:" in section:
        print("No summary available.")ction.split("Category:")[1].split("\n")[0].strip()
                    current_item["category"] = category_line
    # Extract citations from a sample text
    sample_text = """ Remove category line from section
    The court in Sony Corp. of America v. Universal City Studios, Inc., 464 U.S. 417 (1984), 
    established the concept of "time shifting" as fair use. Later, in Campbell v. Acuff-Rose Music, 
    510 U.S. 569 (1994), the Court emphasized the importance of transformative use.
    """         if "```" in section:
                    current_item["snippet"] = section.split("```")[1].strip()
    print("\nExtracting citations from sample text...")
    citations = legal_assistant.extract_citations(sample_text)
    print(f"Found {len(citations)} citations:")"```{current_item['snippet']}```", "").strip()
    for citation in citations:
        print(f"  - {citation}")content to description
                if section.strip():
    print("\nDemo completed!")em["description"] += "\n\n" + section.strip()
        
if __name__ == "__main__": exists
    demo() current_item:
            items.append(current_item)
        
        return items

    def add_task(self, task_type: str, params: Dict[str, Any], priority: int = 1) -> str:
        """
        Add a task to the queue
        
        Args:
            task_type: Type of task (analyze, enhance, generate)
            params: Task parameters
            priority: Task priority (higher is more important)
            
        Returns:
            Task ID
        """
        task_id = f"{int(time.time())}_{id(params)}"
        
        task = {
            "id": task_id,
            "type": task_type,
            "params": params,
            "priority": priority,
            "status": "pending",
            "created_at": time.time(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None
        }
        
        with self.task_lock: