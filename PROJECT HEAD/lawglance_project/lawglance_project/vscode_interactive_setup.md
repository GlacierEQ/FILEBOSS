# Setting Up VS Code Interactive Window for Lawglance

## Required Extensions and Setup

1. **Install the Python Extension for VS Code**
   - Search for "Python" in the Extensions view (Ctrl+Shift+X)
   - Install the official Microsoft Python extension

2. **Install IPyKernel**
   - Open a terminal in VS Code (Ctrl+`)
   - Run: `pip install ipykernel`
   - This allows Python to run in interactive mode

3. **Configure Python Interpreter**
   - Press Ctrl+Shift+P to open the command palette
   - Type "Python: Select Interpreter" and choose your Python installation

## Using the Interactive Window with Lawglance

1. **Open the Interactive Window**
   - Option 1: Right-click in any Python file and select "Run Current File in Interactive Window"
   - Option 2: Use the keyboard shortcut Shift+Enter to run the selected code
   - Option 3: Use the command palette (Ctrl+Shift+P) and type "Python: Start REPL"

2. **Import Lawglance Components**
   ```python
   import os
   import sys
   
   # Set the Hugging Face token
   os.environ["HUGGINGFACE_API_TOKEN"] = "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"
   
   # Add the project directory to path if needed
   project_path = r"C:/Users/casey/OneDrive/Documents/GitHub/lawglance"
   if project_path not in sys.path:
       sys.path.append(project_path)
   
   # Now you can import components
   from lawglance_main import Lawglance
   ```

3. **Testing Components Individually**
   ```python
   # Test document analyzer
   from document_analyzer import DocumentAnalyzer
   analyzer = DocumentAnalyzer()
   
   # Create a simple test document
   with open("test_doc.txt", "w") as f:
       f.write("This is a test legal document.\nIt contains some sample text for analysis.")
   
   # Analyze the document
   result = analyzer.analyze(open("test_doc.txt").read())
   print(result)
   ```

## Troubleshooting

- If the Interactive Window shows errors importing modules, make sure your project directory is in the Python path
- If you see "ModuleNotFoundError", check that all dependencies are installed by running `pip install -r requirements.txt`
- For Hugging Face API errors, verify that your token is set correctly in the environment variables

## Useful Keyboard Shortcuts

- `Shift+Enter`: Run the current line or selection
- `Ctrl+Enter`: Run the current cell (code between `# %%` markers)
- `Alt+Enter`: Run the current line or selection and insert a new cell below
- `Ctrl+K Ctrl+C`: Add cell marker (`# %%`)
