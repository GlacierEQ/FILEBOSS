"""Streamlit UI for LawGlance legal assistant."""
import os
import sys
from src.desktop.webview_app import start_webview_app  # Import the webview app

# Add src directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main function to run the application."""
    print("Starting LawGlance Desktop Application...")
    start_webview_app()  # Start the webview application

if __name__ == "__main__":
    main()
