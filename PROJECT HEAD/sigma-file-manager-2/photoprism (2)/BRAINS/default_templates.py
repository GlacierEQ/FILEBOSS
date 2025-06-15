"""
Default templates for file organization operations
"""

# Default templates for different sorting operations
DEFAULT_TEMPLATES = {
    "chat": [
        {
            "path": "C:/Users/casey/Documents",
            "instruction": "Sort all files into the following structured categories: \n"
                          "- Legal: Court Filings, Evidence, Lawyer Communications, Financial Disclosures, Custody & Visitation, Child Support, Restraining Orders, Appeals & Complaints.\n"
                          "- Financial: Taxes, Bank Statements, Bills & Receipts, Investments & Retirement, Credit Reports, Insurance, Loans & Debts.\n"
                          "- Real Estate: Mortgage & Rent, Home Inspections, Repair & Maintenance, Utilities, Property Documents, Moving & Storage.\n"
                          "- Family: Parenting (Visitation, School Reports, Medical Records), Health & Wellness (Doctor Visits, Fitness & Diet), Travel, Important Contacts, Family History.\n"
                          "- Business: Clients, Contracts & Agreements, Invoices & Payments, Marketing & Branding, Legal & Compliance, Business Plans, HR, Networking.\n"
                          "- Education: Courses, Certificates, Study Notes, Research Papers, Ebooks, AI & Programming, Personal Development.\n"
                          "- Creativity: Photos (Family, Events, Nature), Videos, Music, Graphic Design, Writing & Drafts, Screenplays, AI Projects.\n"
                          "- Technology: Code & Projects (GitHub Repos, AI Dev), Software & Tools, Scripts & Automation, Troubleshooting, Hardware, Cloud Backups.\n"
                          "- Miscellaneous: Random Downloads, Temporary Files, Things to Review, Experimental Projects, Old Stuff.\n"
                          "Use smart rules to rename and organize files based on content, date, and relevance. Apply logical subfolder structures where applicable.",
            "incognito": False
        },
        {
            "path": "C:/Users/casey/Documents",
            "instruction": "Sort all files into folders based on file type: PDFs, Word docs, images, videos, and spreadsheets.",
            "incognito": False
        },
        {
            "path": "C:/Users/casey/Documents",
            "instruction": "Move all files related to legal matters into 'Legal', financial statements into 'Financial', and personal files into 'Personal'.",
            "incognito": False
        },
        {
            "path": "C:/Users/casey/OneDrive/Documents",
            "instruction": "Organize all files into year/month folders based on their last modified date.",
            "incognito": False
        },
        {
            "path": "D:/Work/Projects",
            "instruction": "Group all files into project folders based on keywords in their filename. Use existing folder structures when possible.",
            "incognito": False
        }
    ],
    "batch": [
        {
            "path": "C:/Users/casey/Documents/Reports",
            "instruction": "Rename all report files to match the format 'YYYY-MM-DD_Report_Title.ext'.",
            "incognito": False
        },
        {
            "path": "C:/Users/casey/Downloads",
            "instruction": "Scan for duplicate files and suggest merging or renaming based on content similarity.",
            "incognito": False
        },
        {
            "path": "E:/Photos",
            "instruction": "Sort all images into folders by year and event based on EXIF metadata.",
            "incognito": False
        },
        {
            "path": "D:/Storage",
            "instruction": "Move all files larger than 500MB to a separate 'Large Files' folder.",
            "incognito": False
        }
    ],
    "watch": [
        {
            "path": "C:/Users/casey/Downloads",
            "instruction": "Automatically move new downloads into categorized folders: Documents, Images, Installers, and Videos.",
            "incognito": False
        },
        {
            "path": "C:/Users/casey/Desktop",
            "instruction": "Whenever a new file is added, rename it to follow a standard naming format based on its type.",
            "incognito": False
        },
        {
            "path": "C:/Users/casey/OrganizeFolder",
            "instruction": "Only move non-repository files out of the directory to prevent breaking projects.",
            "incognito": False
        }
    ],
    "commit": [
        {
            "base_path": "C:/Users/casey/Documents",
            "src_path": "OldDocs/report1.docx",
            "dst_path": "Legal/Contracts/report1.docx"
        },
        {
            "base_path": "D:/Organized",
            "src_path": "financial_statement_2024.xlsx",
            "dst_path": "D:/Organized/Financial/2024/financial_statement_2024.xlsx"
        }
    ],
    "feedback": [
        {
            "src_path": "C:/Users/casey/Documents/MisplacedFile.pdf",
            "recommended_path": "C:/Users/casey/Documents/Legal",
            "actual_path": "C:/Users/casey/Documents/Financial",
            "feedback": "This should go under Legal, not Financial."
        },
        {
            "src_path": "D:/NewFiles/NewInvoice.pdf",
            "recommended_path": "D:/Financial/Invoices",
            "actual_path": "D:/RandomFiles",
            "feedback": "Invoices should go into an 'Invoices' folder instead of 'Financial'."
        }
    ],
    "advanced": [
        {
            "path": "C:/Users/casey/Documents",
            "instruction": "Move all files older than 2 years into an 'Archive' folder.",
            "incognito": False
        },
        {
            "path": "D:/ScannedDocs",
            "instruction": "Run OCR on all PDFs and save a searchable version in the same folder.",
            "incognito": False
        },
        {
            "path": "C:/Temp",
            "instruction": "Delete all files in this folder that have not been accessed in 30 days.",
            "incognito": False
        }
    ],
    # Smart folder categories for organizing by topic
    "folder_structures": {
        "general_categories": [
            "Inbox", "Work", "Personal", "School", "Business", 
            "Media", "Archives", "Shared"
        ],
        "legal": [
            "Court_Filings/Motions", "Court_Filings/Orders", "Court_Filings/Hearings",
            "Evidence/Screenshots", "Evidence/Emails", "Evidence/Audio_Video",
            "Lawyer_Communications", "Financial_Disclosures", "Custody_Visitation",
            "Child_Support", "Restraining_Orders", "Appeals_Complaints"
        ],
        "financial": [
            "Taxes/2023", "Taxes/2024", "Bank_Statements", "Bills_Receipts",
            "Investments_Retirement", "Credit_Reports", "Insurance", "Loans_Debts"
        ],
        "real_estate": [
            "Mortgage_Rent", "Home_Inspections", "Repair_Maintenance",
            "Utilities_Bills", "Property_Documents", "Moving_Storage"
        ],
        "family": [
            "Parenting/Visitation", "Parenting/School_Reports", "Parenting/Medical_Records",
            "Health_Wellness/Doctor_Visits", "Health_Wellness/Fitness_Diet",
            "Travel_Vacation", "Important_Contacts", "Family_History_Genealogy", "Personal_Projects"
        ],
        "business": [
            "Clients", "Contracts_Agreements", "Invoices_Payments", "Marketing_Branding",
            "Legal_Compliance", "Business_Plans_Proposals", "Employees_HR",
            "Expenses_Budgeting", "Networking_Contacts"
        ],
        "education": [
            "Courses", "Certificates", "Study_Notes", "Research_Papers",
            "Ebooks_PDFs", "AI_Programming", "Personal_Development"
        ],
        "creativity": [
            "Photos/Family", "Photos/Events", "Photos/Nature", "Videos",
            "Music", "Graphic_Design", "Writing_Drafts", "Screenplays_Scripts", "AI_Projects"
        ],
        "technology": [
            "Code_Projects/GitHub_Repos", "Code_Projects/AI_Development",
            "Software_Tools", "Scripts_Automation", "Troubleshooting_Fixes",
            "Hardware_Builds", "Cloud_Backups"
        ],
        "miscellaneous": [
            "Random_Downloads", "Temporary_Files", "Things_to_Review",
            "Experimental_Projects", "Old_Stuff"
        ]
    }
}

# Helper functions to retrieve templates
def get_template(template_type, index=None):
    """
    Get a specific template or list of templates
    
    Args:
        template_type: Type of template (chat, batch, watch, etc.)
        index: Optional index to get a specific template
        
    Returns:
        Template or list of templates
    """
    if template_type not in DEFAULT_TEMPLATES:
        return None
    
    templates = DEFAULT_TEMPLATES[template_type]
    
    if index is not None and isinstance(templates, list) and 0 <= index < len(templates):
        return templates[index]
    
    return templates


def get_folder_structure(category=None):
    """
    Get a specific folder structure or all structures
    
    Args:
        category: Optional category to filter structures
        
    Returns:
        Folder structure dictionary
    """
    structures = DEFAULT_TEMPLATES.get("folder_structures", {})
    
    if category and category in structures:
        return structures[category]
    
    return structures


def get_all_folder_structures():
    """
    Get all folder structures in a flattened format
    
    Returns:
        Dictionary of all folder paths
    """
    result = {}
    structures = DEFAULT_TEMPLATES.get("folder_structures", {})
    
    for category, folders in structures.items():
        result[category] = folders
    
    return result
