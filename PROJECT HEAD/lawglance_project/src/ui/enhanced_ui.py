"""
Enhanced UI components for LawGlance using Streamlit.
This module provides professional UI components and layouts.
"""
import os
import base64
from typing import List, Dict, Any, Optional
import streamlit as st

class EnhancedUI:
    """Enhanced UI components for creating professional interfaces in Streamlit."""

    def __init__(self, theme: str = "default"):
        """
        Initialize the EnhancedUI system.

        Args:
            theme: UI theme to apply (default, dark, legal)
        """
        self.theme = theme
        self._apply_theme()

    def _apply_theme(self):
        """Apply the selected theme by injecting custom CSS."""
        css = self._get_theme_css(self.theme)


        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    def _get_default_theme_css(self) -> str:
        """Get CSS for the default theme."""
        return """
        /* Base styles */
        .main {
            background-color: #f9f9f9;
            color: #333;
            font-family: 'Arial', sans-serif;
        }

        /* Card component */
        .stcard {
            background-color: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 20px;
            border: 1px solid #eaeaea;
        }

        /* Button styling */
        .stButton > button {
            background-color: #0066cc;
            color: white;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            background-color: #0052a3;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #f8f9f8;
            border-right: 1px solid #e9ecef;
        }

        /* Headings */
        h1, h2, h3 {
            color: #0a2540;
            font-weight: 600;
        }

        /* Custom file uploader */
        [data-testid="stFileUploader"] {
            border: 2px dashed #ccc;
            border-radius: 8px;
            padding: 10px;
            background-color: #f8f9fa;
        }

        /* Progress bar */
        .stProgress > div > div {
            background-color: #0066cc;
        }
        """

    def _get_dark_theme_css(self) -> str:
        """Get CSS for the dark theme."""
        return """
        /* Dark theme */
        .main {
            background-color: #1e1e1e;
            color: #e0e0e0;
            font-family: 'Arial', sans-serif;
        }

        /* Card component */
        .stcard {
            background-color: #2d2d2d;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            margin-bottom: 20px;
            border: 1px solid #3d3d3d;
        }

        /* Button styling */
        .stButton > button {
            background-color: #0078d4;
            color: white;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            background-color: #0066b8;
            box-shadow: 0 4px 8px rgba(0,0,0,0.4);
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #252525;
            border-right: 1px solid #3d3d3d;
        }

        /* Headings */
        h1, h2, h3 {
            color: #e0e0e0;
            font-weight: 600;
        }

        /* Custom file uploader */
        [data-testid="stFileUploader"] {
            border: 2px dashed #555;
            border-radius: 8px;
            padding: 10px;
            background-color: #2d2d2d;
        }

        /* Progress bar */
        .stProgress > div > div {
            background-color: #0078d4;
        }
        """

    def _get_legal_theme_css(self) -> str:
        """Get CSS for the legal theme."""
        return """
        /* Legal theme */
        .main {
            background-color: #f9f9f9;
            color: #333;
            font-family: 'Georgia', serif;
        }

        /* Card component */
        .stcard {
            background-color: white;
            border-radius: 4px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            margin-bottom: 20px;
            border: 1px solid #e0e0e0;
        }

        /* Button styling */
        .stButton > button {
            background-color: #003366;
            color: white;
            border-radius: 2px;
            padding: 0.5rem 1rem;
            font-weight: 500;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            background-color: #002244;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }

        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: #f0f0f0;
            border-right: 1px solid #e0e0e0;
        }

        /* Headings */
        h1, h2, h3 {
            color: #003366;
            font-weight: 600;
        }

        /* Custom file uploader */
        [data-testid="stFileUploader"] {
            border: 2px dashed #ccc;
            border-radius: 4px;
            padding: 10px;
            background-color: #f8f9fa;
        }

        /* Progress bar */
        .stProgress > div > div {
            background-color: #003366;
        }
        """

    def create_card(self, title: str, content: str, icon: Optional[str] = None, background_color: str = "white", border_radius: int = 8):

        """
        Create a styled card component with customizable options.


        Args:
            title: Card title.
            content: Card content.
            icon: Optional icon name (FontAwesome).
            background_color: Background color of the card (default is white).
            border_radius: Border radius of the card (default is 8).

        """
        st.markdown(f"""
        <div class="stcard" style="background-color: {background_color}; border-radius: {border_radius}px;">
            <h3>{f'<i class="fas fa-{icon}"></i> ' if icon else ''}{title}</h3>
            <p>{content}</p>
        </div>
        """, unsafe_allow_html=True)

    def create_split_layout(self, left_content_func, right_content_func, left_width=1, right_width=2):
        """
        Create a split layout with content on left and right.

        Args:
            left_content_func: Function to render left content
            right_content_func: Function to render right content
            left_width: Relative width of left panel
            right_width: Relative width of right panel
        """
        col1, col2 = st.columns([left_width, right_width])

        with col1:
            left_content_func()

        with col2:
            right_content_func()

    def create_document_viewer(self, content: str):
        """
        Create a styled document viewer.

        Args:
            content: Document content
        """
        st.markdown("""
        <style>
        .document-viewer {
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 20px;
            font-family: 'Georgia', serif;
            line-height: 1.6;
            max-height: 600px;
            overflow-y: auto;
            box-shadow: inset 0 0 5px rgba(0,0,0,0.1);
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="document-viewer">
            {content}
        </div>
        """, unsafe_allow_html=True)

    def create_toolbar(self, tools: List[Dict[str, Any]]):
        """
        Create a toolbar with specified tools.

        Args:
            tools: List of tool definitions (name, icon, action)
        """
        st.markdown("""
        <style>
        .toolbar {
            display: flex;
            background-color: #f0f0f0;
            border-radius: 4px;
            padding: 8px;
            margin-bottom: 15px;
            flex-wrap: wrap;
        }
        .tool-button {
            background-color: transparent;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            margin-right: 8px;
            cursor: pointer;
            display: flex;
            align-items: center;
            color: #333;
            transition: background-color 0.2s;
        }
        .tool-button:hover {
            background-color: #e0e0e0;
        }
        .tool-button i {
            margin-right: 6px;
        }
        </style>
        """, unsafe_allow_html=True)

        toolbar_html = '<div class="toolbar">'

        for i, tool in enumerate(tools):
            toolbar_html += f"""
            <button class="tool-button" onclick="tool_click_{i}()">
                <i class="fas fa-{tool.get('icon', 'wrench')}"></i>
                {tool.get('name', 'Tool')}
            </button>
            """

        toolbar_html += '</div>'

        st.markdown(toolbar_html, unsafe_allow_html=True)

        # Add JavaScript for handling clicks
        js = """
        <script>
        """

        for i, tool in enumerate(tools):
            js += f"""
            function tool_click_{i}() {{
                // Using Streamlit's custom events to communicate with Python
                window.parent.postMessage({{
                    type: "streamlit:toolClick",
                    tool: "{tool.get('name', 'Tool')}"
                }}, "*");
            }}
            """

        js += """
        </script>
        """

        st.components.v1.html(js, height=0)

    def create_document_sidebar(self, sections: List[Dict[str, Any]]):
        """
        Create a document navigation sidebar.

        Args:
            sections: List of document sections
        """
        st.sidebar.markdown("### Document Sections")

        for section in sections:
            if st.sidebar.button(section.get('title', 'Section')):
                # This will trigger a rerun with the selected section
                st.session_state.active_section = section.get('id')

        st.sidebar.markdown("---")
