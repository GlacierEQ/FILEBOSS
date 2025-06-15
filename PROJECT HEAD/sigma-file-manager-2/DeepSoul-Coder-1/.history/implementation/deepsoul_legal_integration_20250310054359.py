"""
DeepSoul Legal Integration - Integration of legal data capabilities with DeepSoul
"""
import os
import sys
import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import DeepSoul components
from implementation.legal_scraping import LegalAPIClient
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
        
        # Initialize lock for thread safety
        self.lock = threading.Lock()
        
        # Initialize generator and knowledge store
        self.generator = None  # Will be set when model is loaded
        self.knowledge_store = {}
        self.status = {"model_loaded": False}
    
    def research_legal_topic(self, topic: str, 
                           sources: List[str] = None) -> Dict[str, Any]:
        """
        Research a legal topic using available sources
        
        Args:
            topic: The legal topic to research
            sources: List of sources to use (case_law, statutes, articles)
            
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
        # Common citation patterns
        citation_patterns = [
            r'\d+\s+U\.S\.\s+\d+',
            r'\d+\s+S\.Ct\.\s+\d+',
            r'\d+\s+F\.\d[d|rd]\s+\d+',
            r'\d+\s+F\.Supp\.\s*\d*\s+\d+'
        ]
        
        return re.findall('|'.join(citation_patterns), text)
    
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
        enhanced_code, explanation = self._parse_enhancement(enhancement_text)
        
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

    def _parse_enhancement(self, enhancement_text: str) -> Tuple[str, str]:
        """Parse enhanced code and explanation"""
        return self._parse_generation(enhancement_text)

    def _parse_generation(self, generation_text: str) -> Tuple[str, str]:
        """Parse generated code and explanation"""
        code_block_markers = [
            "```python", "```javascript", 
            "```java", "```typescript", "```c++", "```cpp", "```"
        ]
        
        code = ""
        explanation = generation_text
        
        # Extract code from code blocks
        for marker in code_block_markers:
            if marker in generation_text:
                parts = generation_text.split(marker)
                if len(parts) >= 3:
                    # Extract code from middle section
                    code = parts[1].strip()
                    
                    # Extract explanation (combine text before and after code block)
                    explanation_parts = []
                    if parts[0].strip():
                        explanation_parts.append(parts[0].strip())
                    
                    for part in parts[2:]:
                        # Skip any additional code blocks
                        if "```" in part:
                            part = part.split("```", 1)[-1]
                        if part.strip():
                            explanation_parts.append(part.strip())
                    
                    explanation = "\n\n".join(explanation_parts)
                    break
        
        return code, explanation

    def acquire_knowledge(self, source: str, source_type: str = "auto") -> List[Dict[str, Any]]:
        """
        Acquire knowledge from a source
        
        Args:
            source: Source to acquire knowledge from (file path, URL, etc.)
            source_type: Type of source (file, repo, doc, auto)
            
        Returns:
            List of knowledge items acquired
        """
        if source_type == "auto":
            # Determine source type automatically
            source_type = self._determine_source_type(source)
        
        # Process based on source type
        if source_type == "file":
            return self._acquire_from_file(source)
        elif source_type == "repo":
            return self._acquire_from_repo(source)
        elif source_type == "doc":
            return self._acquire_from_doc(source)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

    def _determine_source_type(self, source: str) -> str:
        """Determine the type of knowledge source"""
        return "file" if os.path.isfile(source) else "repo" if os.path.isdir(source) else "doc" if source.startswith(("http://", "https://")) else "file"

    def _acquire_from_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Acquire knowledge from a file"""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine language from file extension
            language = self._detect_language(file_path)
            
            # Create prompt for knowledge extraction
            prompt = self._create_knowledge_extraction_prompt(content, language, file_path)
            
            # Generate analysis
            with self.lock:
                analysis_text = self.generator.generate(
                    prompt=prompt,
                    max_new_tokens=1024,
                    temperature=0.1,
                    top_p=0.95
                )
            
            # Parse knowledge items
            knowledge_items = self._parse_knowledge_items(analysis_text, file_path)
            
            # Store in knowledge store
            for item in knowledge_items:
                item_id = f"{time.time()}_{id(item)}"
                self.knowledge_store[item_id] = item
            
            return knowledge_items
            
        except Exception as e:
            logger.error(f"Error acquiring knowledge from file {file_path}: {str(e)}")
            return []

    def _acquire_from_repo(self, repo_path: str) -> List[Dict[str, Any]]:
        """Acquire knowledge from a code repository"""
        all_knowledge = []
        
        # Get list of code files
        code_files = self._find_code_files(repo_path)
        
        # Process each file
        for file_path in code_files[:10]:  # Limit to first 10 files to avoid overloading
            try:
                knowledge_items = self._acquire_from_file(file_path)
                all_knowledge.extend(knowledge_items)
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
        
        return all_knowledge

    def _acquire_from_doc(self, url: str) -> List[Dict[str, Any]]:
        """Acquire knowledge from a documentation URL"""
        # This would require web scraping functionality
        # For now, return empty list
        logger.warning("Document knowledge acquisition not yet implemented")
        return []

    def _find_code_files(self, directory: str) -> List[str]:
        """Find code files in a directory"""
        code_extensions = [
            ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
            ".c", ".cpp", ".h", ".hpp", ".cs", ".java", ".kt", ".rb", ".go",
            ".rs", ".php", ".swift", ".m", ".dart"
        ]
        
        code_files = []
        
        for root, _, files in os.walk(directory):
            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    file_path = os.path.join(root, file)
                    code_files.append(file_path)
        
        return code_files

    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        extension = os.path.splitext(file_path)[1].lower()
        
        language_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "JavaScript (React)",
            ".tsx": "TypeScript (React)",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".c": "C",
            ".cpp": "C++",
            ".h": "C/C++ Header",
            ".hpp": "C++ Header",
            ".cs": "C#",
            ".java": "Java",
            ".kt": "Kotlin",
            ".rb": "Ruby",
            ".go": "Go",
            ".rs": "Rust",
            ".php": "PHP",
            ".swift": "Swift",
            ".m": "Objective-C",
            ".dart": "Dart"
        }
        
        return language_map.get(extension, "Unknown")

    def _create_knowledge_extraction_prompt(self, content: str, language: str, file_path: str) -> str:
        """Create prompt for knowledge extraction"""
        return f"""Please analyze this code file and extract key knowledge:

File: {file_path}

{content[:5000]}  # Limit content size if needed

Please provide:
1. Overall functionality and purpose
2. Key components, classes, and functions
3. Dependencies and external integrations
4. Potential issues or improvement areas

Format your response with clear sections:
- OVERVIEW: Brief description of the file
- COMPONENTS: List the main components with bullet points
- BUGS: List any bugs or issues with bullet points
- IMPROVEMENTS: List potential improvements with bullet points
"""

    def _parse_knowledge_items(self, analysis_text: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse knowledge items from analysis text"""
        # Use the existing analysis parser
        parsed_sections = self._parse_analysis(analysis_text)
        
        knowledge_items = []
        
        # Create a knowledge item for overall understanding
        if parsed_sections["overview"]:
            knowledge_items.append({
                "type": "overview",
                "content": parsed_sections["overview"],
                "source": file_path,
                "confidence": 0.9,
                "timestamp": time.time()
            })
        
        # Create knowledge items for components
        for component in parsed_sections["components"]:
            knowledge_items.append({
                "type": "component",
                "content": component,
                "source": file_path,
                "confidence": 0.8,
                "timestamp": time.time()
            })
        
        # Create knowledge items for bugs
        for bug in parsed_sections["bugs"]:
            knowledge_items.append({
                "type": "bug",
                "content": bug,
                "source": file_path,
                "confidence": 0.7,
                "timestamp": time.time()
            })
            
        # Create knowledge items for improvements
        for improvement in parsed_sections["improvements"]:
            knowledge_items.append({
                "type": "improvement",
                "content": improvement,
                "source": file_path,
                "confidence": 0.7,
                "timestamp": time.time()
            })
        
        return knowledge_items