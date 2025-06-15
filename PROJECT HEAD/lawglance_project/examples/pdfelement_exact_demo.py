"""
Demonstration of the exact PDFelement UI according to the design concept.
This example implements the blue, yellow, and white color scheme with the
specified layout including header, toolbar, workspace, and footer.
"""
import os
import sys
from pathlib import Path
import streamlit as st

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import the PDFelementExact UI
from src.ui.pdfelement_theme_exact import PDFelementExact

# Page configuration
st.set_page_config(
    page_title="LawGlance PDF Editor",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    """Main function demonstrating the exact PDFelement UI design."""
    # Initialize the PDFelement UI
    ui = PDFelementExact()
    
    # Sample document content - a contract template
    sample_contract = """
    <div style="padding: 20px;">
        <h1 style="text-align: center;">CONTRACT AGREEMENT</h1>
        
        <p style="margin-top: 20px;"><strong>THIS AGREEMENT</strong> is made on [DATE] between [PARTY A], located at [ADDRESS] ("Client"), 
        and [PARTY B], located at [ADDRESS] ("Contractor").</p>
        
        <h2>1. SERVICES</h2>
        <p>The Contractor agrees to perform the following services for the Client:</p>
        <p>[DESCRIPTION OF SERVICES]</p>
        
        <h2>2. TERM</h2>
        <p>This Agreement shall commence on [START DATE] and continue until [END DATE], 
        unless terminated earlier in accordance with this Agreement.</p>
        
        <h2>3. COMPENSATION</h2>
        <p>The Client shall pay the Contractor [AMOUNT] for the Services. Payment shall be made as follows:</p>
        <p>[PAYMENT SCHEDULE]</p>
        
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
    </div>
    """
    
    # Render the complete interface
    ui.render_full_interface(sample_contract)
    
    # Add some sidebar content for document properties
    with st.sidebar:
        st.header("Document Properties")
        st.text_input("Title", value="Contract Agreement")
        st.text_input("Author", value="LawGlance Legal")
        st.selectbox("Document Type", ["Contract", "NDA", "Agreement", "Letter", "Other"])
        
        st.markdown("---")
        
        st.header("AI Tools")
        st.button("Analyze Document")
        st.button("Extract Key Terms")
        st.button("Generate Summary")
        st.button("Check for Legal Issues")
        
        st.markdown("---")
        st.caption("LawGlance PDF v1.0")

# Run the app
if __name__ == "__main__":
    main()
