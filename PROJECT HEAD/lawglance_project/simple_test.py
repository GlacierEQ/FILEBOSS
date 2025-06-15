"""
A simplified script to test basic functionality without requiring all dependencies.
This is useful if you're having trouble getting all components to work together.
"""
import os
import sys

def simple_test():
    print("Running simple Lawglance test...")
    
    # Check if basic imports work
    try:
        import nltk
        import spacy
        print("Basic imports successful.")
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please install the missing packages.")
        return
    
    # Test document handling with a simple text file
    test_doc = "test_document.txt"
    
    # Create test document if it doesn't exist
    if not os.path.exists(test_doc):
        with open(test_doc, "w") as f:
            f.write("This is a sample legal document.\n")
            f.write("The parties hereby agree to the following terms.\n")
            f.write("The plaintiff argues that the defendant breached the contract.\n")
    
    # Basic document analysis without the full pipeline
    with open(test_doc, "r") as f:
        content = f.read()
        
    # Simple NLP processing
    print("\nProcessing document...")
    sentences = nltk.sent_tokenize(content)
    print(f"Document has {len(sentences)} sentences")
    
    try:
        # Try to use spaCy if installed
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(content)
        
        print("\nEntities found:")
        for ent in doc.ents:
            print(f"- {ent.text}: {ent.label_}")
            
    except Exception as e:
        print(f"Error in spaCy processing: {e}")
    
    print("\nSimple test completed.")

if __name__ == "__main__":
    simple_test()
