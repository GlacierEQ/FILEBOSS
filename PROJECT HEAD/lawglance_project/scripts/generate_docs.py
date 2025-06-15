"""Generate API documentation from docstrings."""
import os
import sys
import inspect
import importlib
import argparse
from typing import List, Dict, Any, Optional, Set
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

def get_module_list(base_path: str) -> List[str]:
    """
    Get list of Python modules in the project.
    
    Args:
        base_path: Base path to search for modules
        
    Returns:
        List of module paths
    """
    modules = []
    base_path = Path(base_path)
    
    for path in base_path.glob("**/*.py"):
        if path.name == "__init__.py":
            # Add the package
            rel_path = path.relative_to(base_path).parent
            module_path = str(rel_path).replace(os.sep, '.')
            if module_path:
                modules.append(module_path)
        else:
            # Add the module
            rel_path = path.relative_to(base_path).with_suffix('')
            module_path = str(rel_path).replace(os.sep, '.')
            modules.append(module_path)
    
    return sorted(modules)

def import_module(module_path: str) -> Any:
    """
    Import a module by its path.
    
    Args:
        module_path: Path to the module
        
    Returns:
        Imported module or None if import fails
    """
    try:
        return importlib.import_module(module_path)
    except ImportError as e:
        print(f"Error importing {module_path}: {e}")
        return None

def get_module_members(module: Any) -> Dict[str, Any]:
    """
    Get classes and functions from a module.
    
    Args:
        module: Module to inspect
        
    Returns:
        Dictionary of module members
    """
    if not module:
        return {}
    
    members = {}
    
    # Get all classes and functions
    for name, obj in inspect.getmembers(module):
        # Skip private members and imported objects
        if name.startswith('_') or inspect.getmodule(obj) != module:
            continue
        
        # Only include classes and functions
        if inspect.isclass(obj) or inspect.isfunction(obj):
            members[name] = obj
    
    return members

def generate_module_docs(module_path: str, module: Any) -> str:
    """
    Generate documentation for a module.
    
    Args:
        module_path: Path to the module
        module: Module object
        
    Returns:
        Documentation string for the module
    """
    if not module:
        return f"# {module_path}\n\nCould not import module.\n\n"
    
    doc = f"# {module_path}\n\n"
    
    # Add module docstring
    if module.__doc__:
        doc += f"{module.__doc__.strip()}\n\n"
    
    # Add classes
    for name, obj in get_module_members(module).items():
        if inspect.isclass(obj):
            doc += generate_class_docs(name, obj)
        elif inspect.isfunction(obj):
            doc += generate_function_docs(name, obj)
    
    return doc

def generate_class_docs(name: str, cls: Any) -> str:
    """
    Generate documentation for a class.
    
    Args:
        name: Class name
        cls: Class object
        
    Returns:
        Documentation string for the class
    """
    doc = f"## Class: {name}\n\n"
    
    # Add class docstring
    if cls.__doc__:
        doc += f"{cls.__doc__.strip()}\n\n"
    
    # Add methods
    for method_name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        if not method_name.startswith('_') or method_name == '__init__':
            doc += generate_method_docs(method_name, method)
    
    return doc

def generate_method_docs(name: str, method: Any) -> str:
    """
    Generate documentation for a method.
    
    Args:
        name: Method name
        method: Method object
        
    Returns:
        Documentation string for the method
    """
    if name == '__init__':
        doc = f"### Constructor\n\n"
    else:
        doc = f"### {name}\n\n"
    
    # Add method docstring
    if method.__doc__:
        doc += f"{method.__doc__.strip()}\n\n"
    
    # Add signature
    try:
        signature = inspect.signature(method)
        doc += f"```python\n{name}{signature}\n```\n\n"
    except ValueError:
        pass
    
    return doc

def generate_function_docs(name: str, func: Any) -> str:
    """
    Generate documentation for a function.
    
    Args:
        name: Function name
        func: Function object
        
    Returns:
        Documentation string for the function
    """
    doc = f"## Function: {name}\n\n"
    
    # Add function docstring
    if func.__doc__:
        doc += f"{func.__doc__.strip()}\n\n"
    
    # Add signature
    try:
        signature = inspect.signature(func)
        doc += f"```python\n{name}{signature}\n```\n\n"
    except ValueError:
        pass
    
    return doc

def generate_project_docs(base_path: str, output_dir: str) -> None:
    """
    Generate documentation for all modules in a project.
    
    Args:
        base_path: Base path of the project
        output_dir: Directory to write documentation files
    """
    modules = get_module_list(base_path)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate index.md
    with open(os.path.join(output_dir, "index.md"), "w") as f:
        f.write("# LawGlance API Documentation\n\n")
        f.write("## Modules\n\n")
        
        for module_path in modules:
            f.write(f"* [{module_path}]({module_path.replace('.', '_')}.md)\n")
    
    # Generate documentation for each module
    for module_path in modules:
        module = import_module(module_path)
        doc = generate_module_docs(module_path, module)
        
        # Write to file
        output_file = os.path.join(output_dir, f"{module_path.replace('.', '_')}.md")
        with open(output_file, "w") as f:
            f.write(doc)
        
        print(f"Generated documentation for {module_path}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate API documentation from docstrings")
    parser.add_argument("--src", type=str, default="src", help="Source directory")
    parser.add_argument("--output", type=str, default="docs/api", help="Output directory")
    
    args = parser.parse_args()
    
    generate_project_docs(args.src, args.output)
    print(f"Documentation generated in {args.output}")

if __name__ == "__main__":
    main()
