"""
Motion Templates for Legal Document Generation

This module provides templates for generating common legal documents
such as motions, pleadings, and other court filings.
"""

from datetime import datetime
from typing import Dict, Any, Optional

# Template for a motion to vacate
MOTION_TO_VACATE_TEMPLATE = """IN THE {court_name}

{case_caption}

MOTION TO VACATE {order_type}

COMES NOW {moving_party}, {party_name}, {party_role}, and moves this Court to vacate the {order_type} entered on {order_date}. In support of this Motion, {moving_party} states as follows:

I. INTRODUCTION
{introduction}

II. STATEMENT OF FACTS
{statement_of_facts}

III. ARGUMENT
{argument}

IV. CONCLUSION
WHEREFORE, {moving_party} respectfully requests that this Court:
1. Vacate the {order_type} entered on {order_date};
2. Grant such other and further relief as the Court deems just and proper.

Respectfully submitted,

{signature_block}
"""

# Template for a motion for summary judgment
MOTION_FOR_SUMMARY_JUDGMENT = """IN THE {court_name}

{case_caption}

MOTION FOR SUMMARY JUDGMENT

COMES NOW {moving_party}, {party_name}, {party_role}, and moves this Court for summary judgment in {his_her} favor. In support of this Motion, {moving_party} states as follows:

I. INTRODUCTION
{introduction}

II. STATEMENT OF UNDISPUTED MATERIAL FACTS
{statement_of_facts}

III. ARGUMENT
{argument}

IV. CONCLUSION
WHEREFORE, {moving_party} respectfully requests that this Court:
1. Grant summary judgment in favor of {moving_party};
2. Award {moving_party} {relief_sought};
3. Grant such other and further relief as the Court deems just and proper.

Respectfully submitted,

{signature_block}
"""

# Template for a notice of appearance
NOTICE_OF_APPEARANCE = """IN THE {court_name}

{case_caption}

NOTICE OF APPEARANCE

COMES NOW {attorney_name}, {attorney_title}, and hereby enters {his_her} appearance as counsel for {party_name} in the above-captioned matter.

{attorney_contact}

CERTIFICATE OF SERVICE
I hereby certify that on {date}, I electronically filed the foregoing with the Clerk of the Court using the {court_efiling_system} which will send notification of such filing to all counsel of record.

{signature_block}
"""

# Legal standards for common motions
LEGAL_STANDARDS = {
    'motion_to_vacate': (
        "A court may vacate a judgment or order for various reasons, including "
        "mistake, inadvertence, surprise, excusable neglect, newly discovered "
        "evidence, or fraud. See [Rule 60(b) of the Federal Rules of Civil Procedure]."
    ),
    'motion_for_summary_judgment': (
        "Summary judgment is appropriate when there is no genuine dispute as to any "
        "material fact and the movant is entitled to judgment as a matter of law. "
        "See [Rule 56(a) of the Federal Rules of Civil Procedure]."
    ),
    'motion_to_dismiss': (
        "A motion to dismiss tests the legal sufficiency of the complaint. The court "
        "must accept all well-pleaded facts as true and construe them in the light "
        "most favorable to the plaintiff. See [Rule 12(b)(6) of the Federal Rules "
        "of Civil Procedure]."
    )
}

# Common court headers
COURT_HEADERS = {
    'supreme_court': 'SUPREME COURT OF THE UNITED STATES',
    'federal_district': 'UNITED STATES DISTRICT COURT FOR THE [DISTRICT] OF [STATE]',
    'state_supreme': 'SUPREME COURT OF [STATE]',
    'state_appellate': 'COURT OF APPEALS OF [STATE]',
    'state_trial': '[COUNTY] [DIVISION] COURT, [STATE]',
}

class MotionTemplate:
    """Class for generating legal documents from templates."""
    
    def __init__(self):
        self.templates = {
            'motion_to_vacate': MOTION_TO_VACATE_TEMPLATE,
            'motion_for_summary_judgment': MOTION_FOR_SUMMARY_JUDGMENT,
            'notice_of_appearance': NOTICE_OF_APPEARANCE
        }
    
    def generate_document(
        self, 
        template_name: str, 
        context: Dict[str, Any],
        custom_template: Optional[str] = None
    ) -> str:
        """Generate a legal document from a template.
        
        Args:
            template_name: Name of the template to use
            context: Dictionary of template variables
            custom_template: Optional custom template string
            
        Returns:
            str: The generated document
        """
        template = self.templates.get(template_name.lower(), custom_template)
        if not template:
            raise ValueError(f"No template found for {template_name}")
        
        # Add default values for common fields
        context.setdefault('date', datetime.now().strftime('%B %d, %Y'))
        context.setdefault('his_her', 'his or her')
        context.setdefault('he_she', 'he or she')
        
        # Apply the template
        try:
            return template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing required template variable: {e}")
    
    def get_legal_standard(self, motion_type: str) -> str:
        """Get the legal standard for a specific type of motion.
        
        Args:
            motion_type: Type of motion (e.g., 'motion_to_vacate')
            
        Returns:
            str: The legal standard text
        """
        return LEGAL_STANDARDS.get(motion_type.lower(), "")
    
    def get_court_header(self, court_type: str, **kwargs) -> str:
        """Get a formatted court header.
        
        Args:
            court_type: Type of court (e.g., 'federal_district')
            **kwargs: Additional context for the header
            
        Returns:
            str: Formatted court header
        """
        header = COURT_HEADERS.get(court_type.lower(), '')
        if not header:
            return ''
        
        # Replace placeholders in the header
        for key, value in kwargs.items():
            header = header.replace(f'[{key.upper()}]', str(value).upper())
            
        return header
