"""
DeepSoul Code Comprehension - Advanced code understanding and analysis capabilities
"""
import os
import sys
import ast
import json
import torch
import numpy as np
from pathlib import Path
from typing import Dict, List, Union, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from transformers import PreTrainedModel, PreTrainedTokenizer
import logging
import networkx as nx
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import OOM protection utilities
from implementation.oom_protected_execution import oom_protected, MemoryEfficientContext
from utils.tensor_optimization import optimize_tensor

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname=s - %(message)s'
)
logger = logging.getLogger("DeepSoul-CodeComprehension")

@dataclass
class CodeEntity:
    """Represents a code entity (function, class, variable, etc.)"""
    name: str
    entity_type: str  # 'function', 'class', 'method', 'variable', etc.
    file_path: str
    start_line: int
    end_line: int
    code: str
    docstring: Optional[str] = None
    parent: Optional[str] = None  # Parent entity, if any
    children: List[str] = field(default_factory=list)  # Child entities
    dependencies: List[str] = field(default_factory=list)  # Names of entities this depends on
    properties: Dict[str, Any] = field(default_factory=dict)  # Additional properties
    embedding: Optional[np.ndarray] = None  # Vector representation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        result = {
            "name": self.name,
            "entity_type": self.entity_type,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "code": self.code,
            "docstring": self.docstring,
            "parent": self.parent,
            "children": self.children,
            "dependencies": self.dependencies,
            "properties": self.properties
        }
        
        # Only include embedding if available
        if self.embedding is not None:
            result["embedding"] = self.embedding.tolist()
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CodeEntity":
        """Create from dictionary representation"""
        embedding = None
        if "embedding" in data:
            embedding = np.array(data["embedding"])
            
        return cls(
            name=data["name"],
            entity_type=data["entity_type"],
            file_path=data["file_path"],
            start_line=data["start_line"],
            end_line=data["end_line"],
            code=data["code"],
            docstring=data["docstring"],
            parent=data["parent"],
            children=data["children"],
            dependencies=data["dependencies"],
            properties=data["properties"],
            embedding=embedding
        )

class PythonCodeParser:
    """Parser for extracting entities and relationships from Python code"""
    
    def __init__(self):
        self.entities = {}
        self.current_file = ""
    
    @oom_protected(retry_on_cpu=True)
    def parse_file(self, file_path: str) -> Dict[str, CodeEntity]:
        """Parse a Python file and extract code entities"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            self.current_file = file_path
            return self.parse_source(source_code, file_path)
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}")
            return {}
    
    def parse_source(self, source_code: str, file_path: str) -> Dict[str, CodeEntity]:
        """Parse Python source code and extract entities"""
        try:
            tree = ast.parse(source_code)
            self.entities = {}  # Reset entities for this file
            self.current_file = file_path
            self._analyze_ast(tree, source_code)
            return self.entities
            
        except SyntaxError as e:
            logger.error(f"Syntax error in file {file_path}: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Error parsing source code: {str(e)}")
            return {}
            
    def _analyze_ast(self, tree: ast.AST, source_code: str, parent: Optional[str] = None):
        """Recursively analyze the AST and extract entities"""
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                # Extract class definition
                class_name = node.name
                qualified_name = f"{parent}.{class_name}" if parent else class_name
                
                # Get line numbers
                start_line = node.lineno
                end_line = self._find_end_line(node, source_code)
                
                # Get code and docstring
                code = self._extract_node_source(node, source_code)
                docstring = ast.get_docstring(node)
                
                # Extract methods and attributes
                methods = []
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        methods.append(f"{qualified_name}.{child.name}")
                
                # Create entity
                self.entities[qualified_name] = CodeEntity(
                    name=qualified_name,
                    entity_type="class",
                    file_path=self.current_file,
                    start_line=start_line,
                    end_line=end_line,
                    code=code,
                    docstring=docstring,
                    parent=parent,
                    children=methods
                )
                
                # Recursively analyze class body
                self._analyze_ast(node, source_code, qualified_name)
                
            elif isinstance(node, ast.FunctionDef):
                # Extract function/method definition
                func_name = node.name
                qualified_name = f"{parent}.{func_name}" if parent else func_name
                
                # Get line numbers
                start_line = node.lineno
                end_line = self._find_end_line(node, source_code)
                
                # Get code and docstring
                code = self._extract_node_source(node, source_code)
                docstring = ast.get_docstring(node)
                
                # Determine entity type (method or function)
                entity_type = "method" if parent and "." in parent else "function"
                
                # Extract dependencies (imported modules and called functions)
                dependencies = self._extract_dependencies(node)
                
                # Create entity
                self.entities[qualified_name] = CodeEntity(
                    name=qualified_name,
                    entity_type=entity_type,
                    file_path=self.current_file,
                    start_line=start_line,
                    end_line=end_line,
                    code=code,
                    docstring=docstring,
                    parent=parent,
                    dependencies=dependencies,
                    properties={
                        "args": [arg.arg for arg in node.args.args],
                        "returns": self._get_return_annotation(node)
                    }
                )
                
                # Add to parent's children
                if parent and parent in self.entities:
                    if qualified_name not in self.entities[parent].children:
                        self.entities[parent].children.append(qualified_name)
                
                # Recursively analyze function body
                self._analyze_ast(node, source_code, qualified_name)
    
    def _extract_node_source(self, node: ast.AST, source_code: str) -> str:
        """Extract the source code for a specific node"""
        # Find the start line of the node
        start_line = node.lineno
        
        # Find the end line by examining the node's children
        end_line = self._find_end_line(node, source_code)
        
        # Extract the source lines
        source_lines = source_code.splitlines()
        if start_line <= len(source_lines) and end_line <= len(source_lines):
            return "\n".join(source_lines[start_line - 1:end_line])
        
        return ""
    
    def _find_end_line(self, node: ast.AST, source_code: str) -> int:
        """Find the end line number for a node"""
        max_line = node.lineno
        
        for child in ast.iter_child_nodes(node):
            if hasattr(child, 'lineno'):
                child_end = self._find_end_line(child, source_code)
                max_line = max(max_line, child_end)
        
        # Find indentation of the node
        lines = source_code.splitlines()
        node_line = lines[node.lineno - 1] if node.lineno - 1 < len(lines) else ""
        node_indent = len(node_line) - len(node_line.lstrip())
        
        # Look for the next line with same or less indentation
        for i in range(node.lineno, len(lines)):
            line = lines[i]
            if line.strip() and len(line) - len(line.lstrip()) <= node_indent:
                return i
        
        # If we can't find a specific end line, use the max child line
        return max_line
    
    def _extract_dependencies(self, node: ast.AST) -> List[str]:
        """Extract function dependencies (called functions, used variables)"""
        dependencies = []
        
        class DependencyExtractor(ast.NodeVisitor):
            def __init__(self):
                self.function_calls = []
                
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    self.function_calls.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    # For method calls like obj.method()
                    self.function_calls.append(f"{self._get_attribute_name(node.func)}")
                self.generic_visit(node)
                
            def _get_attribute_name(self, node):
                if isinstance(node, ast.Name):
                    return node.id
                elif isinstance(node, ast.Attribute):
                    return f"{self._get_attribute_name(node.value)}.{node.attr}"
                return ""
        
        extractor = DependencyExtractor()
        extractor.visit(node)
        dependencies.extend(extractor.function_calls)
        
        return list(set(dependencies))  # Remove duplicates
    
    def _get_return_annotation(self, func_node: ast.FunctionDef) -> Optional[str]:
        """Extract return type annotation if available"""
        if func_node.returns:
            if isinstance(func_node.returns, ast.Name):
                return func_node.returns.id
            elif isinstance(func_node.returns, ast.Constant):
                return str(func_node.returns.value)
            elif hasattr(func_node.returns, 'id'):
                return func_node.returns.id
            else:
                return str(func_node.returns)
        return None

class CodeUnderstandingEngine:
    """Engine for understanding code structure, relationships, and semantics"""
    
    def __init__(self, model: Optional[PreTrainedModel] = None, tokenizer: Optional[PreTrainedTokenizer] = None):
        """Initialize with optional model and tokenizer for embedding generation"""
        self.model = model
        self.tokenizer = tokenizer
        self.parsers = {
            ".py": PythonCodeParser(),
            # Additional parsers for other languages can be added here
        }
        self.entity_store = {}  # Code entities by qualified name
        self.file_entities = defaultdict(list)  # Entities by file path
        self.dependency_graph = nx.DiGraph()  # Directed graph for dependencies
    
    @oom_protected(retry_on_cpu=True)
    def process_file(self, file_path: str) -> List[CodeEntity]:
        """Process a single file and extract code entities"""
        file_path = str(file_path)
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Check if we have a parser for this file type
        if file_extension not in self.parsers:
            logger.warning(f"No parser available for file type: {file_extension}")
            return []
        
        # Parse file with appropriate parser
        parser = self.parsers[file_extension]
        entities = parser.parse_file(file_path)
        
        # Store entities
        for name, entity in entities.items():
            self.entity_store[name] = entity
            self.file_entities[file_path].append(name)
            self.dependency_graph.add_node(name)
        
        # Generate embeddings for entities if model is available
        if self.model is not None and self.tokenizer is not None:
            self._generate_embeddings(entities.values())
        
        # Update dependency graph
        self._update_dependency_graph()
        
        return list(entities.values())
    
    def process_directory(self, 
                         directory: str, 
                         recursive: bool = True,
                         file_extensions: Optional[List[str]] = None) -> Dict[str, List[CodeEntity]]:
        """Process all files in a directory"""
        if file_extensions is None:
            file_extensions = list(self.parsers.keys())
        
        results = {}
        directory = Path(directory)
        
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    if any(file.endswith(ext) for ext in file_extensions):
                        file_path = os.path.join(root, file)
                        entities = self.process_file(file_path)
                        results[file_path] = entities
        else:
            for file in os.listdir(directory):
                if any(file.endswith(ext) for ext in file_extensions):
                    file_path = os.path.join(directory, file)
                    if os.path.isfile(file_path):
                        entities = self.process_file(file_path)
                        results[file_path] = entities
        
        return results
    
    @oom_protected(retry_on_cpu=True)
    def _generate_embeddings(self, entities: List[CodeEntity]):
        """Generate embeddings for code entities using the model"""
        try:
            for entity in entities:
                # Create a representation for the entity
                if entity.entity_type in ["function", "method"]:
                    # For functions/methods: signature + docstring + first few lines
                    text = entity.code[:500]  # Limit to first 500 chars
                    if entity.docstring:
                        text = f"{text}\n{entity.docstring}"
                elif entity.entity_type == "class":
                    # For classes: class definition + docstring
                    class_def = entity.code.split("\n")[0] + "\n"
                    if entity.docstring:
                        class_def = f"{class_def}{entity.docstring}\n"
                    text = class_def
                else:
                    text = entity.code[:500]
                
                # Tokenize and generate embedding
                inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
                
                with torch.no_grad():
                    outputs = self.model(**inputs, output_hidden_states=True)
                    # Use last hidden state of [CLS] token as embedding
                    embedding = outputs.hidden_states[-1][0, 0].cpu().numpy()
                
                # Normalize the embedding
                embedding = embedding / np.linalg.norm(embedding)
                entity.embedding = embedding
                
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
    
    def _update_dependency_graph(self):
        """Update the dependency graph based on stored entities"""
        for name, entity in self.entity_store.items():
            # Add entity node if not already in graph
            if not self.dependency_graph.has_node(name):
                self.dependency_graph.add_node(name)
            
            # Add edges for parent-child relationships
            if entity.parent and entity.parent in self.entity_store:
                self.dependency_graph.add_edge(entity.parent, name, type="parent-child")
            
            # Add edges for dependencies
            for dep in entity.dependencies:
                if dep in self.entity_store:
                    self.dependency_graph.add_edge(name, dep, type="depends-on")
    
    @oom_protected(retry_on_cpu=True)
    def find_similar_entities(self, query: str, entity_type: Optional[str] = None, top_k: int = 5) -> List[Tuple[CodeEntity, float]]:
        """Find entities similar to the query using embeddings"""
        if self.model is None or self.tokenizer is None:
            logger.warning("Model and tokenizer required for semantic search")
            return []
        
        # Generate query embedding
        inputs = self.tokenizer(query, return_tensors="pt", padding=True, truncation=True, max_length=512)
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs, output_hidden_states=True)
            query_embedding = outputs.hidden_states[-1][0, 0].cpu().numpy()
            query_embedding = query_embedding / np.linalg.norm(query_embedding)
        
        # Filter entities by type if specified
        entities = []
        for entity in self.entity_store.values():
            if entity_type is None or entity.entity_type == entity_type:
                if entity.embedding is not None:
                    entities.append(entity)
        
        # Calculate similarity scores
        similarities = []
        for entity in entities:
            similarity = np.dot(query_embedding, entity.embedding)
            similarities.append((entity, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities[:top_k]
    
    def find_dependencies(self, entity_name: str, max_depth: int = 2, direction: str = "outgoing") -> Dict[str, List[str]]:
        """Find dependencies for an entity"""
        if entity_name not in self.entity_store:
            return {}
        
        result = {}
        current_level = [entity_name]
        
        for depth in range(max_depth):
            next_level = []
            for name in current_level:
                if name not in result:
                    result[name] = []
                
                if direction == "outgoing":
                    # Find what this entity depends on
                    neighbors = list(self.dependency_graph.successors(name))
                elif direction == "incoming":
                    # Find what depends on this entity
                    neighbors = list(self.dependency_graph.predecessors(name))
                else:
                    # Find both directions
                    neighbors = list(self.dependency_graph.successors(name))
                    neighbors.extend(list(self.dependency_graph.predecessors(name)))
                
                for neighbor in neighbors:
                    if neighbor != name and neighbor in self.entity_store:
                        if neighbor not in result[name]:
                            result[name].append(neighbor)
                            next_level.append(neighbor)
            
            current_level = next_level
            if not current_level:
                break
        
        return result
    
    @oom_protected(retry_on_cpu=True)
    def analyze_code_complexity(self, entity_name: str) -> Dict[str, Any]:
        """Analyze the complexity of a code entity"""
        if entity_name not in self.entity_store:
            return {}
        
        entity = self.entity_store[entity_name]
        code = entity.code
        
        # Simple complexity metrics
        metrics = {
            "lines_of_code": len(code.split("\n")),
            "character_count": len(code),
            "has_docstring": entity.docstring is not None and len(entity.docstring) > 0
        }
        
        if entity.entity_type in ["function", "method"]:
            # Calculate cyclomatic complexity (simplified)
            complexity = 1  # Base complexity
            complexity += code.count("if ")
            complexity += code.count("elif ")
            complexity += code.count("for ")
            complexity += code.count("while ")
            complexity += code.count("and ")
            complexity += code.count("or ")
            complexity += code.count("except:")
            metrics["cyclomatic_complexity"] = complexity
            
            # Calculate cognitive complexity (simplified)
            cognitive = complexity
            cognitive += code.count("try:")
            cognitive += code.count("finally:")
            cognitive += code.count("with ")
            metrics["cognitive_complexity"] = cognitive
            
            # Count parameters
            metrics["parameter_count"] = len(entity.properties.get("args", []))
            
            # Nesting level (simplified)
            indent_patterns = re.findall(r'^( +)', code, re.MULTILINE)
            if indent_patterns:
                max_indent = max(len(indent) for indent in indent_patterns)
                metrics["max_nesting_level"] = max_indent // 4  # Assuming 4-space indentation
            else:
                metrics["max_nesting_level"] = 0
        
        return metrics
    
    @oom_protected(retry_on_cpu=True)
    def generate_code_summary(self, entity_name: str) -> str:
        """Generate a natural language summary of a code entity"""
        if self.model is None or self.tokenizer is None:
            return "Model required for summary generation"
        
        if entity_name not in self.entity_store:
            return "Entity not found"
        
        entity = self.entity_store[entity_name]
        
        # Create a prompt for the model to generate a summary
        if entity.entity_type in ["function", "method"]:
            prompt = f"Summarize this {entity.entity_type} concisely:\n\n```python\n{entity.code}\n```"
        elif entity.entity_type == "class":
            prompt = f"Summarize this class concisely:\n\n```python\n{entity.code}\n```"
        else:
            prompt = f"Summarize this code concisely:\n\n```python\n{entity.code}\n```"
        
        # Generate summary
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids=inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_length=150,
                do_sample=True,
                top_p=0.95,
                temperature=0.7,
                num_return_sequences=1
            )
        
        summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the summary part (remove the prompt)
        if summary.startswith(prompt):
            summary = summary[len(prompt):].strip()
        
        return summary
    
    def export_project_graph(self, output_path: str = "project_graph.json"):
        """Export the project dependency graph to a JSON file"""
        graph_data = {
            "nodes": [],
            "edges": []
        }
        
        # Add nodes (entities)
        for name, entity in self.entity_store.items():
            node = {
                "id": name,
                "type": entity.entity_type,
                "file": os.path.basename(entity.file_path)
            }
            graph_data["nodes"].append(node)
        
        # Add edges
        for u, v, data in self.dependency_graph.edges(data=True):
            edge = {
                "source": u,
                "target": v,
                "type": data.get("type", "unknown")
            }
            graph_data["edges"].append(edge)
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(graph_data, f, indent=2)
            
        return output_path
    
    def save_to_file(self, output_path: str = "code_understanding.json"):
        """Save the current state to a file"""
        data = {
            "entities": {name: entity.to_dict() for name, entity in self.entity_store.items()},
            "file_entities": {file_path: entities for file_path, entities in self.file_entities.items()}
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
            
        return output_path
    
    def load_from_file(self, input_path: str):
        """Load state from a file"""
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        # Load entities
        self.entity_store = {name: CodeEntity.from_dict(entity_data) 
                            for name, entity_data in data["entities"].items()}
        
        # Load file entities
        self.file_entities = defaultdict(list)
        for file_path, entities in data["file_entities"].items():
            self.file_entities[file_path] = entities
        
        # Rebuild dependency graph
        self.dependency_graph = nx.DiGraph()
        self._update_dependency_graph()
        
        return True


def demo_code_comprehension():
    """Demonstrate code comprehension functionality"""
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import tempfile
    
    print("Initializing code comprehension engine...")
    
    # Create a sample Python file for analysis
    sample_code = """
import math
from datetime import datetime

def calculate_distance(x1, y1, x2, y2):
    \"\"\"Calculate the Euclidean distance between two points.\"\"\"
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

class GeometryCalculator:
    \"\"\"A class for geometry calculations\"\"\"
    
    def __init__(self, precision=2):
        self.precision = precision
    
    def circle_area(self, radius):
        \"\"\"Calculate the area of a circle\"\"\"
        area = math.pi * radius**2
        return round(area, self.precision)
    
    def triangle_area(self, base, height):
        \"\"\"Calculate the area of a triangle\"\"\"
        return round(0.5 * base * height, self.precision)

def main():
    \"\"\"Main function to demonstrate calculations\"\"\"
    calc = GeometryCalculator(precision=4)
    radius = 5
    print(f"Circle area: {calc.circle_area(radius)}")
    
    dist = calculate_distance(0, 0, 3, 4)
    print(f"Distance: {dist}")
    
    timestamp = datetime.now()
    print(f"Calculation time: {timestamp}")

if __name__ == "__main__":
    main()
"""

    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write(sample_code)
        temp_file = f.name
    
    try:
        # Initialize the code understanding engine
        engine = CodeUnderstandingEngine()
        
        # Process the file
        print(f"Processing file: {temp_file}")
        entities = engine.process_file(temp_file)
        
        print(f"Found {len(entities)} code entities:")
        for entity in entities:
            print(f"- {entity.entity_type}: {entity.name}")
            if entity.docstring:
                print(f"  Docstring: {entity.docstring}")
            if entity.dependencies:
                print(f"  Dependencies: {', '.join(entity.dependencies)}")
        
        # Analyze code complexity
        function_name = "calculate_distance"
        if function_name in engine.entity_store:
            print(f"\nAnalyzing complexity of {function_name}:")
            complexity = engine.analyze_code_complexity(function_name)
            for metric, value in complexity.items():
                print(f"- {metric}: {value}")
        
        # Export project graph
        graph_path = "demo_project_graph.json"
        engine.export_project_graph(graph_path)
        print(f"\nProject graph exported to {graph_path}")
        
    finally:
        # Clean up
        os.unlink(temp_file)
        print("\nDemo complete.")

if __name__ == "__main__":
    demo_code_comprehension()
