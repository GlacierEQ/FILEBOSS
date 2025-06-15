"""
Demonstration of the enhanced UI components for LawGlance.
This example shows how to create a more professional interface.
"""
import os
import sys
from pathlib import Path
import streamlit as st

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import EnhancedUI
from src.ui.enhanced_ui import EnhancedUI

# Page configuration
st.set_page_config(
    page_title="LawGlance Enhanced UI Demo",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize the enhanced UI with theme
theme = st.sidebar.selectbox("Select Theme", ["default", "dark", "legal"])
ui = EnhancedUI(theme=theme)

def main():
    """Main function demonstrating enhanced UI components."""
    # Header
    st.title("LawGlance Enhanced UI")
    st.markdown("A demonstration of professional UI components for document processing")
    
    # Create a toolbar
    tools = [
        {"name": "Open", "icon": "folder-open"},
        {"name": "Save", "icon": "save"},
        {"name": "Print", "icon": "print"},
        {"name": "Scan", "icon": "search"},
        {"name": "Analyze", "icon": "chart-bar"}
    ]
    ui.create_toolbar(tools)
    
    # Split layout example
    def render_document_navigator():
        st.markdown("### Document Navigator")
        
        # Sample document sections
        sections = [
            {"title": "Introduction", "id": "intro"},
            {"title": "Terms and Conditions", "id": "terms"},
            {"title": "Legal Provisions", "id": "legal"},
            {"title": "Signatures", "id": "signatures"}
        ]
        
        for section in sections:
            st.button(section["title"])
    
    def render_document_viewer():
        st.markdown("### Document Viewer")
        
        # Sample document content
        sample_document = """
        <h2>SAMPLE CONTRACT AGREEMENT</h2>
        
        <p>THIS AGREEMENT is made on [DATE] between [PARTY A], located at [ADDRESS] ("Client"), and [PARTY B], located at [ADDRESS] ("Contractor").</p>
        
        <h3>1. SERVICES</h3>
        <p>The Contractor agrees to perform the following services for the Client:<br>
        [DESCRIPTION OF SERVICES]</p>
        
        <h3>2. TERM</h3>
        <p>This Agreement shall commence on [START DATE] and continue until [END DATE], unless terminated earlier in accordance with this Agreement.</p>
        
        <h3>3. COMPENSATION</h3>
        <p>The Client shall pay the Contractor [AMOUNT] for the Services. Payment shall be made as follows:<br>
        [PAYMENT SCHEDULE]</p>
        """
        
        ui.create_document_viewer(sample_document)
        
        # Document actions
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("Download PDF")
        with col2:
            st.button("Share Document")
        with col3:
            st.button("Request Analysis")
    
    ui.create_split_layout(
        left_content_func=render_document_navigator,
        right_content_func=render_document_viewer,
        left_width=1,
        right_width=3
    )
    
    # Cards example
    st.markdown("### Document Tools")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        ui.create_card(
            title="Document Analysis", 
            content="Analyze your legal document for potential issues and opportunities.",
            icon="chart-line"
        )
        
    with col2:
        ui.create_card(
            title="AI Assistant", 
            content="Get AI-powered recommendations and suggestions for your document.",
            icon="robot"
        )
        
    with col3:
        ui.create_card(
            title="Legal Templates", 
            content="Access our library of legal document templates.",
            icon="file-contract"
        )
    
    # Upload section with enhanced styling
    st.markdown("### Document Upload")
    st.markdown("""
    <style>
    .upload-container {
        border: 2px dashed #0066cc;
        border-radius: 8px;
        padding: 30px;
        text-align: center;
        background-color: #f8f9fa;
        margin-bottom: 20px;
        transition: all 0.3s;
    }
    .upload-container:hover {
        background-color: #e6f7ff;
    }
    </style>
    <div class="upload-container">
        <i class="fas fa-cloud-upload-alt" style="font-size: 48px; color: #0066cc;"></i>
        <h4>Drag and drop files here or click to browse</h4>
        <p>Supported formats: .docx, .pdf, .txt</p>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("", type=["docx", "pdf", "txt"], key="enhanced_uploader")
    if uploaded_file:
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
        
        # Show processing progress
        st.markdown("### Processing Document")
        progress_bar = st.progress(0)
        
        # Simulate processing
        for i in range(101):
            # Update progress bar
            progress_bar.progress(i)
            if i == 100:
                st.success("Document processed successfully!")

# Run the app
if __name__ == "__main__":
    # Add FontAwesome for icons
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    """, unsafe_allow_html=True)
    
    main()
