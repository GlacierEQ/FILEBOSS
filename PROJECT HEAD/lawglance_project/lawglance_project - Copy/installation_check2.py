"""
Utility script to verify the installation of all required dependencies.
Run this script to check if all packages are properly installed.
"""
import sys
import importlib

def check_packages():
    # List of required packages
    packages = [
        'langchain', 'transformers', 'nltk', 'spacy', 'textstat', 
        'faiss', 'docx', 'networkx', 'sklearn', 'numpy', 'torch'
    ]
    
    missing = []
    for package in packages:
        try:
            importlib.import_module(package)
            print(f"✓ {package} is installed")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} is NOT installed")
    
    # Special check for spaCy models
    if 'spacy' not in missing:
        try:
            import spacy
            nlp = spacy.load("en_core_web_sm")
            print("✓ spaCy model 'en_core_web_sm' is installed")
        except OSError:
            print("✗ spaCy model 'en_core_web_sm' is NOT installed")
            print("  Run: python -m spacy download en_core_web_sm")
    
    # Special check for NLTK resources
    if 'nltk' not in missing:
        import nltk
        resources = ['punkt', 'stopwords', 'wordnet']
        for resource in resources:
            try:
                nltk.data.find(f'tokenizers/{resource}' if resource == 'punkt' else f'corpora/{resource}')
                print(f"✓ NLTK resource '{resource}' is installed")
            except LookupError:
                print(f"✗ NLTK resource '{resource}' is NOT installed")
                print(f"  Run: python -c \"import nltk; nltk.download('{resource}')\"")
    
    if missing:
        print("\nMissing packages. Please install them with:")
        print(f"pip install --user {' '.join(missing)}")
    else:
        print("\nAll package dependencies are installed!")
        
    # Check Python version
    print(f"\nPython version: {sys.version}")

if __name__ == "__main__":
    check_packages()
