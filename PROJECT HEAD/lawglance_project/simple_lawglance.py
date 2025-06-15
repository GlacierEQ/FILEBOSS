"""
Simple script to run the Lawglance system directly without dependencies.
This is useful for quick testing when the batch file isn't working.
"""
import os
import sys

# Set the Hugging Face token
os.environ["HUGGINGFACE_API_TOKEN"] = "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"
os.environ["PYTHONIOENCODING"] = "utf-8"

# Find the project path
project_paths = [
    os.getcwd(),
    os.path.join(os.getcwd(), "OneDrive", "Documents", "GitHub", "lawglance"),
    os.path.join(os.path.expanduser("~"), "OneDrive", "Documents", "GitHub", "lawglance")
]

project_path = None
for path in project_paths:
    if os.path.exists(os.path.join(path, "lawglance_main.py")):
        project_path = path
        break

if not project_path:
    print("Error: Could not find lawglance_main.py")
    print("Please navigate to the project directory and try again.")
    sys.exit(1)

# Add the project path to sys.path
if project_path not in sys.path:
    sys.path.append(project_path)

print(f"Found Lawglance at: {project_path}")

try:
    # Import the necessary modules
    from transformers import pipeline
    import langchain

    # Try to import run_lawglance from lawglance_runner
    try:
        from lawglance_runner import setup_environment, run_lawglance
        print("Running Lawglance system...")
        if setup_environment():
            run_lawglance()
    except ImportError:
        # If lawglance_runner is not available, try importing the main class
        try:
            from lawglance_main import Lawglance
            print("Imported Lawglance class. To use it:")
            print("1. Initialize with: lawglance = Lawglance(llm, embeddings, vector_store)")
            print("2. Use with: lawglance.conversational('your query here')")
        except ImportError:
            print("Error: Could not import Lawglance class.")
            print("Make sure the project structure is correct.")

except ImportError as e:
    print(f"Missing dependency: {e}")
    print("\nPlease install the required dependencies with:")
    print("pip install langchain transformers nltk spacy textstat faiss-cpu python-docx networkx scikit-learn numpy torch huggingface_hub")
    print("python -m spacy download en_core_web_sm")
    print("python -c \"import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')\"")

# Keep the window open
input("\nPress Enter to exit...")
