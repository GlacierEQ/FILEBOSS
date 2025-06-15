from transformers import AutoTokenizer, AutoModelForCausalLM
import langchain
from langchain.llms import HuggingFaceHub
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from lawglance_main import Lawglance

# Setup the required components
def initialize_system():
    print("Initializing Lawglance system...")
    
    # Initialize LLM - using a simple model for testing
    # In production, replace with more powerful models
    llm = HuggingFaceHub(
        repo_id="google/flan-t5-base",
        model_kwargs={"temperature": 0.1, "max_length": 512}
    )
    
    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings()
    
    # Create a simple vector store for testing
    # In production, populate with your legal documents
    texts = ["Sample legal document content for testing"]
    vector_store = FAISS.from_texts(texts, embeddings)
    
    # Initialize the Lawglance system
    lawglance = Lawglance(llm, embeddings, vector_store)
    
    print("Lawglance system initialized successfully!")
    return lawglance

def run_tests(lawglance):
    print("\nRunning basic tests:")
    
    # Test basic query
    print("\nTesting basic query...")
    response = lawglance.conversational("What is a legal contract?")
    print(f"Response: {response}")
    
    # Test document processing (adjust file path as needed)
    try:
        print("\nTesting document processing...")
        print("Note: This requires a valid file path to a document")
        # response = lawglance.conversational("process document C:/path/to/sample_doc.docx analyze")
        # print(f"Document analysis: {response}")
        print("Skipped - replace with actual file path to test")
    except Exception as e:
        print(f"Document processing test error: {e}")
    
    # Test legal argument extraction (adjust file path as needed)
    try:
        print("\nTesting legal argument extraction...")
        # response = lawglance.conversational("extract arguments from C:/path/to/sample_doc.docx")
        # print(f"Extracted arguments: {response}")
        print("Skipped - replace with actual file path to test")
    except Exception as e:
        print(f"Legal argument extraction test error: {e}")
    
    print("\nTest run completed. Add specific test cases for your needs.")

if __name__ == "__main__":
    try:
        lawglance = initialize_system()
        run_tests(lawglance)
    except Exception as e:
        print(f"Error during execution: {e}")
