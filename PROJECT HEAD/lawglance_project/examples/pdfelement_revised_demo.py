"""
Demonstration of the revised PDFelement UI with specified color scheme.
This example implements the black, blue, and yellow design concept.
"""
import os
import sys
from pathlib import Path
import streamlit as st

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import the revised PDFelement UI
from src.ui.pdfelement_revised import PDFelementRevised

# Page configuration
st.set_page_config(
    page_title="LawGlance PDF Editor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize the PDFelement UI
ui = PDFelementRevised()

def main():
    """Main function demonstrating revised PDFelement UI."""
    # Add FontAwesome for icons
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    """, unsafe_allow_html=True)
    
    # Create the entire UI structure
    ui.create_header()
    ui.create_toolbar()
    
    # Sample document content
    sample_contract = """
    <h1 style="text-align: center;">CONTRACT AGREEMENT</h1>
    
    <p><strong>THIS AGREEMENT</strong> is made on [DATE] between [PARTY A], located at [ADDRESS] ("Client"), 
    and [PARTY B], located at [ADDRESS] ("Contractor").</p>
    
    <h2>1. SERVICES</h2>
    <p>The Contractor agrees to perform the following services for the Client:<br>
    [DESCRIPTION OF SERVICES]</p>
    
    <h2>2. TERM</h2>
    <p>This Agreement shall commence on [START DATE] and continue until [END DATE], 
    unless terminated earlier in accordance with this Agreement.</p>
    
    <h2>3. COMPENSATION</h2>
    <p>The Client shall pay the Contractor [AMOUNT] for the Services. Payment shall be made as follows:<br>
    [PAYMENT SCHEDULE]</p>
    
    <h2>4. INDEPENDENT CONTRACTOR STATUS</h2>
    <p>The Contractor is an independent contractor, not an employee of the Client. 
    The Contractor shall be responsible for all taxes and other costs related to the Contractor's business.</p>
    
    <h2>5. CONFIDENTIALITY</h2>
    <p>The Contractor agrees to keep all information provided by the Client confidential and shall not 
    disclose it to any third party without the prior written consent of the Client.</p>
    
    <h2>6. TERM AND TERMINATION</h2>
    <p>This Agreement may be terminated by either party with written notice if the other party breaches 
    any provision of this Agreement and fails to cure such breach within [NUMBER] days of receiving 
    written notice of such breach.</p>
    
    <div style="margin-top: 60px; display: flex; justify-content: space-between;">
        <div style="width: 45%;">
            <p>________________________<br>
            [CLIENT NAME]<br>
            Date: ________________</p>
        </div>
        <div style="width: 45%;">
            <p>________________________<br>
            [CONTRACTOR NAME]<br>
            Date: ________________</p>
        </div>
    </div>
    """
    
    # Create the document workspace
    ui.create_workspace(sample_contract)
    
    # Create the AI assistant
    ui.create_ai_assistant()
    
    # Create the footer
    ui.create_footer()
    
    # Create some hidden state elements for interactive components
    with st.sidebar:
        st.header("Document Properties")
        st.text_input("Document Title", value="Contract Agreement")
        st.text_input("Author", value="LawGlance User")
        st.selectbox("Permission", ["View & Edit", "View Only", "Comment"])
        
        st.header("AI Tools")
        st.button("Analyze Document")
        st.button("Suggest Improvements")
        st.button("Check Legal Compliance")
        
        # Add version at the bottom
        st.markdown("---")
        st.caption("LawGlance PDF v1.0")

# Run the app
if __name__ == "__main__":
    main()
