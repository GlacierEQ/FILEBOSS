from pathlib import Path
import ast
import networkx as nx
from typing import Dict, List

class ProjectAnalyzer:
    """Deep Soul Code Analyzer for comprehensive project understanding"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.dependency_graph = nx.DiGraph()
        self.modules: Dict[str, Dict] = {}
        self.api_endpoints: List[Dict] = []
        self.database_models: List[Dict] = []
        self.tech_debt_items: List[Dict] = []

    # -----------------------------------------------------
    # Public API
    # -----------------------------------------------------
    def analyze(self) -> Dict:
        """Perform deep recursive analysis of the entire codebase"""
        self._scan_files()
        self._build_dependency_graph()
        self._identify_api_endpoints()
        self._extract_database_models()
        self._assess_technical_debt()

        return {
            "modules": self.modules,
            "dependency_graph": self.dependency_graph,
            "api_endpoints": self.api_endpoints,
            "database_models": self.database_models,
            "tech_debt": self.tech_debt_items,
            "integration_points": self._identify_integration_points(),
            "test_coverage": self._analyze_test_coverage(),
        }

    # -----------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------
    def _scan_files(self):
        """Recursively scan all project files"""
        python_files = list(self.project_root.glob("**/*.py"))
        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                module_ast = ast.parse(content)
                self.modules[str(file_path.relative_to(self.project_root))] = {
                    "ast": module_ast,
                    "classes": [node.name for node in ast.walk(module_ast) if isinstance(node, ast.ClassDef)],
                    "functions": [node.name for node in ast.walk(module_ast) if isinstance(node, ast.FunctionDef)],
                    "imports": self._extract_imports(module_ast),
                }
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")

    def _extract_imports(self, module_ast) -> List[str]:
        """Extract all imports from an AST"""
        imports: List[str] = []
        for node in ast.walk(module_ast):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.append(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    for name in node.names:
                        imports.append(f"{node.module}.{name.name}")
        return imports

    def _build_dependency_graph(self):
        """Build a dependency graph of all modules"""
        for module_path, module_info in self.modules.items():
            self.dependency_graph.add_node(module_path)
            for imported_module in module_info["imports"]:
                # Handle relative imports and map to actual files
                resolved_module = self._resolve_import(module_path, imported_module)
                if resolved_module:
                    self.dependency_graph.add_edge(module_path, resolved_module)

    def _resolve_import(self, importing_module: str, imported_name: str) -> str:
        """Resolve an import statement to an actual file in the project"""
        # Map Python import paths to actual files. Simplified approach:
        for module_path in self.modules.keys():
            normalized = module_path.replace("/", ".").replace("\\", ".").rsplit(".py", 1)[0]
            if normalized == imported_name:
                return module_path
        return ""

    def _identify_api_endpoints(self):
        """Identify all FastAPI endpoints"""
        for module_path, module_info in self.modules.items():
            for node in ast.walk(module_info["ast"]):
                if isinstance(node, ast.FunctionDef):
                    decorators = []
                    for d in node.decorator_list:
                        if isinstance(d, ast.Call):
                            if isinstance(d.func, ast.Attribute):
                                decorators.append(d.func.attr)
                            elif isinstance(d.func, ast.Name):
                                decorators.append(d.func.id)
                    if any(d in {"get", "post", "put", "delete", "patch"} for d in decorators):
                        self.api_endpoints.append(
                            {
                                "module": module_path,
                                "function": node.name,
                                "methods": [d for d in decorators if d in {"get", "post", "put", "delete", "patch"}],
                            }
                        )

    def _extract_database_models(self):
        """Extract SQLAlchemy/database models"""
        for module_path, module_info in self.modules.items():
            for node in ast.walk(module_info["ast"]):
                if isinstance(node, ast.ClassDef):
                    bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
                    if "Base" in bases or any("Model" in base for base in bases):
                        self.database_models.append(
                            {
                                "module": module_path,
                                "class": node.name,
                                "fields": self._extract_model_fields(node),
                            }
                        )

    def _extract_model_fields(self, class_node) -> List[Dict]:
        """Extract fields from a database model class"""
        fields = []
        for node in ast.walk(class_node):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if (
                            isinstance(node.value, ast.Call)
                            and hasattr(node.value.func, "id")
                            and node.value.func.id == "Column"
                        ):
                            fields.append({
                                "name": target.id,
                                "type": self._extract_column_type(node.value),
                            })
        return fields

    def _extract_column_type(self, column_node) -> str:
        """Extract the type from a Column definition"""
        if column_node.args:
            first_arg = column_node.args[0]
            if hasattr(first_arg, "id"):
                return first_arg.id
        return "Unknown"

    def _assess_technical_debt(self):
        """Identify areas of technical debt"""
        for module_path, module_info in self.modules.items():
            # Look for TODO, FIXME comments
            file_fs_path = self.project_root / module_path
            try:
                with open(file_fs_path, "r", encoding="utf-8") as f:
                    lines = f.read().split("\n")
                for i, line in enumerate(lines, start=1):
                    if "TODO" in line or "FIXME" in line:
                        self.tech_debt_items.append({
                            "module": module_path,
                            "line": i,
                            "comment": line.strip(),
                        })
            except FileNotFoundError:
                continue

            # Look for complex functions (high cyclomatic complexity)
            for node in ast.walk(module_info["ast"]):
                if isinstance(node, ast.FunctionDef):
                    complexity = self._calculate_complexity(node)
                    if complexity > 10:  # Threshold
                        self.tech_debt_items.append(
                            {
                                "module": module_path,
                                "function": node.name,
                                "issue": f"High complexity ({complexity})",
                            }
                        )

    def _calculate_complexity(self, func_node) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base
        for node in ast.walk(func_node):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With, ast.AsyncWith, ast.Try)):
                complexity += 1
            elif isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And):
                complexity += len(node.values) - 1
        return complexity

    def _identify_integration_points(self):
        """Identify potential integration points for new components"""
        integration_points: List[Dict] = []
        # Service classes or factories
        for module_path, module_info in self.modules.items():
            for class_name in module_info["classes"]:
                if any(p in class_name.lower() for p in ["service", "factory", "manager", "provider", "client"]):
                    integration_points.append(
                        {
                            "module": module_path,
                            "class": class_name,
                            "type": "service",
                        }
                    )
        # Hooks in API routes
        for endpoint in self.api_endpoints:
            if any(k in endpoint["function"].lower() for k in ["callback", "hook"]):
                integration_points.append(
                    {
                        "module": endpoint["module"],
                        "function": endpoint["function"],
                        "type": "api_hook",
                    }
                )
        return integration_points

    def _analyze_test_coverage(self) -> Dict:
        """Analyze test coverage (rudimentary)"""
        test_files = list(self.project_root.glob("**/test_*.py"))
        tests_by_module: Dict[str, List[str]] = {}
        for test_file in test_files:
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()
            test_ast = ast.parse(content)
            test_functions = [
                node.name
                for node in ast.walk(test_ast)
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
            ]
            test_module_name = test_file.stem[5:]  # drop test_
            target_module = next((m for m in self.modules.keys() if test_module_name in m), None)
            if target_module:
                tests_by_module[target_module] = test_functions

        return {
            "test_files": len(test_files),
            "test_functions": sum(len(funcs) for funcs in tests_by_module.values()),
            "modules_with_tests": len(tests_by_module),
            "modules_without_tests": len(self.modules) - len(tests_by_module),
            "tests_by_module": tests_by_module,
        }
