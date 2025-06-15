"""
Exact PDFelement-inspired UI theme for LawGlance.
This module implements the exact design concept with the header, toolbar, workspace, and footer
according to the specified blue, yellow, and white color scheme.
"""
import streamlit as st
import os
from typing import List, Dict, Any, Optional, Union, Tuple
import base64
from pathlib import Path

class PDFelementExact:
    """
    PDFelement-inspired UI exactly matching the design concept.
    
    This class implements a UI that faithfully recreates the PDFelement interface
    with the specified blue, yellow, and white color scheme.
    """
    
    # Color definitions as specified in the design concept
    COLORS = {
        "blue": "#2196F3",          # Primary blue for header/footer
        "yellow": "#F7DC6F",        # Yellow for toolbar
        "white": "#FFFFFF",         # White for workspace/background
        "black": "#000000",         # Black for borders
        "text_white": "#FFFFFF",    # White text for header/footer
        "text_dark": "#333333",     # Dark text for document
    }
    
    def __init__(self):
        """Initialize the PDFelementExact UI."""
        self._apply_theme()
    
    def _apply_theme(self):
        """Apply the theme by injecting custom CSS."""
        css = self._get_theme_css()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    
    def _get_theme_css(self) -> str:
        """Get CSS for the PDFelement theme matching exact design concept."""
        return f"""
        /* Reset Streamlit default styles */
        body {{
            font-family: Arial, sans-serif;
            background-color: {self.COLORS["white"]};
            margin: 0;
            padding: 0;
            color: {self.COLORS["text_dark"]};
        }}
        
        .stApp {{
            background-color: {self.COLORS["white"]};
        }}
        
        .main {{
            padding: 0 !important;
            margin: 0 !important;
        }}
        
        /* Header styles */
        .pdfelement-header {{
            background-color: {self.COLORS["blue"]};
            color: {self.COLORS["text_white"]};
            padding: 1em;
            text-align: center;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .pdfelement-header-logo {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 1.2rem;
            font-weight: bold;
        }}
        
        .pdfelement-nav {{
            display: flex;
            gap: 20px;
        }}
        
        .pdfelement-nav-item {{
            color: {self.COLORS["text_white"]};
            cursor: pointer;
        }}
        
        /* Toolbar styles */
        .pdfelement-toolbar {{
            background-color: {self.COLORS["yellow"]};
            padding: 1em;
            border-bottom: 1px solid {self.COLORS["black"]};
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }}
        
        .pdfelement-tool {{
            background-color: {self.COLORS["blue"]};
            color: {self.COLORS["text_white"]};
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .pdfelement-tool:hover {{
            opacity: 0.9;
        }}
        
        /* Workspace styles */
        .pdfelement-workspace {{
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 2em;
        }}
        
        .pdfelement-document-editor {{
            background-color: {self.COLORS["white"]};
            padding: 1em;
            border: 1px solid {self.COLORS["blue"]};
            width: 80%;
            height: 80vh;
            overflow: auto;
            box-shadow: 0 0 10px rgba(33, 150, 243, 0.3);
        }}
        
        /* Document editing toolbar */
        .pdfelement-edit-toolbar {{
            background-color: #f5f5f5;
            padding: 0.5em;
            border-bottom: 1px solid #ddd;
            display: flex;
            gap: 10px;
            margin-bottom: 1em;
        }}
        
        .pdfelement-edit-tool {{
            background-color: #fff;
            border: 1px solid #ddd;
            padding: 5px 10px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 12px;
        }}
        
        /* Footer styles */
        .pdfelement-footer {{
            background-color: {self.COLORS["blue"]};
            color: {self.COLORS["text_white"]};
            padding: 1em;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .pdfelement-copyright {{
            font-size: 14px;
        }}
        
        .pdfelement-social {{
            display: flex;
            gap: 15px;
        }}
        
        .pdfelement-social-icon {{
            color: {self.COLORS["text_white"]};
            font-size: 16px;
        }}
        
        /* AI Assistant */
        .pdfelement-ai {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 300px;
            background-color: white;
            border: 2px solid {self.COLORS["blue"]};
            border-radius: 8px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            z-index: 1000;
        }}
        
        .pdfelement-ai-header {{
            background-color: {self.COLORS["blue"]};
            color: white;
            padding: 10px 15px;
            font-weight: bold;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .pdfelement-ai-body {{
            padding: 15px;
        }}
        
        .pdfelement-ai-suggestion {{
            background-color: #f5f5f5;
            padding: 10px;
            margin-bottom: 10px;
            border-left: 3px solid {self.COLORS["blue"]};
        }}
        
        /* Override Streamlit component styles */
        [data-testid="stSidebar"] {{
            background-color: #f7f7f7;
            border-right: 1px solid #eee;
        }}
        
        .stButton > button {{
            background-color: {self.COLORS["blue"]};
            color: white;
        }}
        """
    
    def render_full_interface(self, document_content: str = None):
        """
        Render the complete PDFelement-inspired interface.
        
        Args:
            document_content: Optional HTML content for the document
        """
        # Add FontAwesome for icons
        st.markdown("""
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
        """, unsafe_allow_html=True)
        
        # Create the header
        self._create_header()
        
        # Create the toolbar
        self._create_toolbar()
        
        # Create the workspace
        self._create_workspace(document_content)
        
        # Create the AI assistant
        self._create_ai_assistant()
        
        # Create the footer
        self._create_footer()
    
    def _create_header(self):
        """Create the PDFelement header with navigation according to the wireframe."""
        header_html = """
        <div class="pdfelement-header">
            <div class="pdfelement-header-logo">
                <i class="fas fa-file-pdf"></i>
                LawGlance PDF
            </div>
            <nav class="pdfelement-nav">
                <div class="pdfelement-nav-item">File</div>
                <div class="pdfelement-nav-item">Edit</div>
                <div class="pdfelement-nav-item">View</div>
                <div class="pdfelement-nav-item">Tools</div>
                <div class="pdfelement-nav-item">Help</div>
            </nav>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)
    
    def _create_toolbar(self):
        """Create the yellow toolbar with blue buttons as specified."""
        toolbar_html = """
        <div class="pdfelement-toolbar">
            <button class="pdfelement-tool">
                <i class="fas fa-file-pdf"></i>
                Create PDF
            </button>
            <button class="pdfelement-tool">
                <i class="fas fa-edit"></i>
                Edit PDF
            </button>
            <button class="pdfelement-tool">
                <i class="fas fa-exchange-alt"></i>
                Convert PDF
            </button>
            <button class="pdfelement-tool">
                <i class="fas fa-object-group"></i>
                Merge PDF
            </button>
            <button class="pdfelement-tool">
                <i class="fas fa-cut"></i>
                Split PDF
            </button>
            <button class="pdfelement-tool">
                <i class="fas fa-copy"></i>
                Extract Pages
            </button>
            <button class="pdfelement-tool">
                <i class="fas fa-tint"></i>
                Add Watermark
            </button>
            <button class="pdfelement-tool">
                <i class="fas fa-signature"></i>
                Add Signature
            </button>
        </div>
        """
        st.markdown(toolbar_html, unsafe_allow_html=True)
    
    def _create_workspace(self, content: str = None):
        """Create the white document workspace with blue border."""
        if not content:
            content = """
            <div style="text-align: center;">
                <h1>Sample Document</h1>
                <p>This is a sample document for editing. Replace with your content.</p>
                <p>This editor includes features for:</p>
                <ul style="text-align: left; display: inline-block;">
                    <li>Text editing</li>
                    <li>Image editing</li>
                    <li>Annotation</li>
                    <li>Highlighting</li>
                    <li>Underlining</li>
                </ul>
            </div>
            """
            
        workspace_html = f"""
        <div class="pdfelement-workspace">
            <div class="pdfelement-document-editor">
                <div class="pdfelement-edit-toolbar">
                    <span class="pdfelement-edit-tool"><i class="fas fa-font"></i> Text</span>
                    <span class="pdfelement-edit-tool"><i class="fas fa-image"></i> Image</span>
                    <span class="pdfelement-edit-tool"><i class="fas fa-comment"></i> Annotate</span>
                    <span class="pdfelement-edit-tool"><i class="fas fa-highlighter"></i> Highlight</span>
                    <span class="pdfelement-edit-tool"><i class="fas fa-underline"></i> Underline</span>
                </div>
                {content}
            </div>
        </div>
        """
        st.markdown(workspace_html, unsafe_allow_html=True)
    
    def _create_ai_assistant(self):
        """Create the AI assistant panel."""
        ai_html = """
        <div class="pdfelement-ai">
            <div class="pdfelement-ai-header">
                AI Assistant
                <i class="fas fa-robot"></i>
            </div>
            <div class="pdfelement-ai-body">
                <div class="pdfelement-ai-suggestion">
                    <strong>Document Analysis:</strong>
                    <p>This document appears to be a contract template. Would you like me to fill in the standard fields?</p>
                </div>
                <div class="pdfelement-ai-suggestion">
                    <strong>Text Recognition:</strong>
                    <p>I've recognized the text in this document. Click here to edit it directly.</p>
                </div>
                <div class="pdfelement-ai-suggestion">
                    <strong>Image Processing:</strong>
                    <p>There are no images in this document. You can add images using the toolbar above.</p>
                </div>
            </div>
        </div>
        """
        st.markdown(ai_html, unsafe_allow_html=True)
    
    def _create_footer(self):
        """Create the blue footer with copyright and social links."""
        footer_html = """
        <div class="pdfelement-footer">
            <div class="pdfelement-copyright">
                &copy; 2023 LawGlance PDF
            </div>
            <div class="pdfelement-social">
                <a href="#" class="pdfelement-social-icon"><i class="fab fa-facebook"></i></a>
                <a href="#" class="pdfelement-social-icon"><i class="fab fa-twitter"></i></a>
                <a href="#" class="pdfelement-social-icon"><i class="fab fa-linkedin"></i></a>
            </div>
        </div>
        """
        st.markdown(footer_html, unsafe_allow_html=True)
