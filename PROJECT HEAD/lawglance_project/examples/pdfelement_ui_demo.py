"""
Demonstration of the PDFelement-inspired UI for LawGlance.
This example shows how to create a professional document interface using the 
black, blue, and yellow color scheme similar to PDFelement.
"""
import os
import sys
from pathlib import Path
import streamlit as st
import base64
from tempfile import NamedTemporaryFile

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import PDFelementUI
from src.ui.pdfelement_theme import PDFelementUI

# Page configuration
st.set_page_config(
    page_title="LawGlance PDFelement UI Demo",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize the PDFelement UI
ui = PDFelementUI()

def main():
    """Main function demonstrating PDFelement-style UI."""
    # Add FontAwesome for icons
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    """, unsafe_allow_html=True)
    
    # Create the PDFelement-style header
    ui.create_pdfelement_header(app_title="LawGlance PDF")
    
    # Create the PDFelement-style toolbar with groups
    toolbar_tools = [
        {"name": "Open", "icon": "folder-open", "group": "File"},
        {"name": "Save", "icon": "save", "group": "File"},
        {"name": "Export", "icon": "file-export", "group": "File"},
        
        {"name": "Edit", "icon": "edit", "group": "Edit"},
        {"name": "Text", "icon": "font", "group": "Edit"},
        {"name": "Image", "icon": "image", "group": "Edit"},
        
        {"name": "Comment", "icon": "comment", "group": "Annotate"},
        {"name": "Highlight", "icon": "highlighter", "group": "Annotate"},
        {"name": "Draw", "icon": "pencil-alt", "group": "Annotate"},
        
        {"name": "AI Scan", "icon": "robot", "group": "AI Tools"},
        {"name": "Analyze", "icon": "chart-bar", "group": "AI Tools"},
        {"name": "Summarize", "icon": "file-alt", "group": "AI Tools"},
        
        {"name": "Share", "icon": "share-alt", "group": "Share"},
        {"name": "Print", "icon": "print", "group": "Share"}
    ]
    ui.create_pdfelement_toolbar(toolbar_tools)
    
    # Create the main layout
    main_col, sidebar_col = st.columns([4, 1])
    
    with main_col:
        # Create the document workspace
        sample_contract = """
        <h2 style="text-align: center;">CONTRACT AGREEMENT</h2>
        
        <p><strong>THIS AGREEMENT</strong> is made on [DATE] between [PARTY A], located at [ADDRESS] ("Client"), 
        and [PARTY B], located at [ADDRESS] ("Contractor").</p>
        
        <h3>1. SERVICES</h3>
        <p>The Contractor agrees to perform the following services for the Client:<br>
        [DESCRIPTION OF SERVICES]</p>
        
        <h3>2. TERM</h3>
        <p>This Agreement shall commence on [START DATE] and continue until [END DATE], 
        unless terminated earlier in accordance with this Agreement.</p>
        
        <h3>3. COMPENSATION</h3>
        <p>The Client shall pay the Contractor [AMOUNT] for the Services. Payment shall be made as follows:<br>
        [PAYMENT SCHEDULE]</p>
        
        <h3>4. INDEPENDENT CONTRACTOR STATUS</h3>
        <p>The Contractor is an independent contractor, not an employee of the Client. 
        The Contractor shall be responsible for all taxes and other costs related to the Contractor's business.</p>
        """
        
        ui.create_document_workspace(sample_contract)
    
    with sidebar_col:
        # Create the tools panel
        def render_tools_panel():
            st.button("Edit Text", key="edit_text")
            st.button("Add Image", key="add_image")
            st.button("Add Comment", key="add_comment")
            st.button("Search", key="search")
        
        ui.create_panel("Tools", render_tools_panel)
        
        # Create the AI panel
        def render_ai_tools():
            st.button("AI Analyze Document", key="ai_analyze")
            st.button("Extract Data", key="extract_data")
            st.button("Generate Summary", key="generate_summary")
            st.button("Check Legal Compliance", key="check_legal")
        
        ui.create_panel("AI Tools", render_ai_tools)
    
    # Create the floating AI assistant
    ai_suggestions = [
        {
            "title": "Missing Information",
            "content": "The contract is missing specific payment terms in section 3."
        },
        {
            "title": "Legal Issue Detected",
            "content": "The contract term section doesn't specify termination conditions."
        },
        {
            "title": "Formatting Suggestion",
            "content": "Consider adding page numbers and a signature block at the end."
        }
    ]
    
    ui.create_ai_assistant(ai_suggestions)
    
    # Add footer status bar
    st.markdown("""
    <div style="position: fixed; bottom: 0; left: 0; right: 0; background-color: #0A0A0A; 
    padding: 5px 15px; display: flex; justify-content: space-between; border-top: 1px solid #333; font-size: 12px;">
        <span>Page 1 of 1</span>
        <span>Ready</span>
        <span>100%</span>
    </div>
    """, unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    main()
