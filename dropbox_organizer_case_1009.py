#!/usr/bin/env python3
"""
🔥 DROPBOX LEGAL ORGANIZER - CASE 1FDV-23-0001009 🔥
GitHub MCP-Powered | Hybrid Local + Cloud Deployment
Author: Casey del Carpio Barton (GlacierEQ)
Repository: https://github.com/GlacierEQ/FILEBOSS

Organizes 2,703+ legal files into structured 10-category system
for February 19, 2025 hearing and July 28-29, 2025 trial prep.

Usage:
  python dropbox_organizer_case_1009.py --dry-run  # Test mode
  python dropbox_organizer_case_1009.py            # Live execution
"""

import os
import re
import json
import hashlib
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════
# 🔥 CONFIGURATION
# ═══════════════════════════════════════════════════════════════

CASE_CONFIG = {
    "case_number": "1FDV-23-0001009",
    "case_name": "Barton v. Barton (Divorce/Custody)",
    "child_name": "Kekoa",
    "father": "Casey del Carpio Barton",
    "mother": "Teresa del Carpio Barton",
    "feb_hearing": "2025-02-19T13:30:00-10:00",
    "july_trial": "2025-07-28",
    "github_repo": "https://github.com/GlacierEQ/FILEBOSS"
}

# Master folder structure (10 top-level categories)
MASTER_STRUCTURE = {
    "01_COURT_FILINGS": {
        "01a_Docket_Entries": {"2023": {}, "2024": {}, "2025": {}},
        "01b_Casey_Motions": {
            "Motion_to_Quash_Rule58": {},
            "Motion_Audio_Recording": {},
            "Motion_Reconsideration": {},
            "Other_Motions": {}
        },
        "01c_Teresa_Brower_Motions": {
            "Sanctions_Motions": {},
            "Trial_Setting_Motions": {},
            "Other_Motions": {}
        },
        "01d_Court_Orders": {
            "Scheduling_Orders": {},
            "Protective_Orders": {},
            "Trial_Orders": {},
            "Other_Orders": {}
        },
        "01e_Notices": {
            "NEF_Notices": {},
            "Hearing_Notices": {},
            "Service_Notices": {}
        }
    },
    "02_EVIDENCE": {
        "02a_Teresa_Exhibits": {
            "Exhibit_A-J_General": {},
            "Exhibit_T_OFW_Communications": {},
            "Exhibit_U_Medical": {},
            "Exhibit_V_School": {},
            "Exhibit_W-Z_Other": {}
        },
        "02b_Casey_Counter_Evidence": {
            "Counter_to_T_OFW": {},
            "Counter_to_U_Medical": {},
            "Counter_to_V_School": {},
            "General_Counter_Evidence": {}
        },
        "02c_Medical_Records": {
            "Kekoa_Medical": {},
            "Casey_Medical": {},
            "Teresa_Medical": {}
        },
        "02d_School_Records": {
            "Report_Cards": {},
            "Teacher_Communications": {},
            "Attendance": {},
            "Behavioral_Reports": {}
        },
        "02e_Financial": {
            "Asset_Debt_Statements": {},
            "Bank_Statements": {},
            "Tax_Returns": {},
            "Child_Support_CSEA": {},
            "Income_Documentation": {}
        },
        "02f_Communications": {
            "OurFamilyWizard": {},
            "Emails": {},
            "Text_Messages": {},
            "Social_Media": {}
        },
        "02g_Photos_Videos": {
            "Kekoa_with_Casey": {},
            "Activities": {},
            "Home_Environment": {}
        }
    },
    "03_DISCOVERY": {
        "03a_Requests_Sent": {},
        "03b_Responses_Received": {},
        "03c_Objections": {},
        "03d_Subpoenas": {
            "School_Subpoenas": {},
            "Medical_Subpoenas": {},
            "Other_Subpoenas": {}
        }
    },
    "04_LEGAL_RESEARCH": {
        "04a_Hawaii_Case_Law": {},
        "04b_Statutes": {
            "HRS_Hawaii_Revised_Statutes": {},
            "HFCR_Family_Court_Rules": {},
            "HRPC_Prof_Conduct_Rules": {},
            "HRE_Rules_Evidence": {}
        },
        "04c_Motion_Templates": {},
        "04d_Legal_Memoranda": {}
    },
    "05_STRATEGY": {
        "05a_Case_Analysis": {},
        "05b_Timeline_Documentation": {},
        "05c_Trial_Strategy": {
            "Feb19_Hearing_Prep": {},
            "July28-29_Trial_Prep": {}
        },
        "05d_Settlement_Analysis": {}
    },
    "06_AI_ANALYSIS": {
        "06a_Chat_Transcripts": {
            "ChatGPT_Exports": {},
            "Perplexity_Sessions": {},
            "Claude_Conversations": {}
        },
        "06b_JSON_Strategy_Files": {},
        "06c_AI_Generated_Motions": {},
        "06d_Evidence_Analysis": {}
    },
    "07_TRIAL_NOTEBOOKS": {
        "07a_February_19_2025_Hearing": {
            "Exhibit_List": {},
            "Witness_List": {},
            "Legal_Arguments": {},
            "Opening_Statement": {},
            "Closing_Argument": {}
        },
        "07b_July_28-29_2025_Trial": {
            "Exhibit_List": {},
            "Witness_List": {},
            "Legal_Arguments": {},
            "Opening_Statement": {},
            "Closing_Argument": {},
            "Direct_Examinations": {},
            "Cross_Examinations": {}
        }
    },
    "08_CORRESPONDENCE": {
        "08a_Attorney_Communications": {},
        "08b_Court_Clerk": {},
        "08c_Opposing_Counsel": {},
        "08d_Witnesses": {},
        "08e_Experts": {}
    },
    "09_REFERENCE": {
        "09a_Master_Timeline": {},
        "09b_Exhibit_Index": {},
        "09c_Contact_Directory": {},
        "09d_Important_Dates": {},
        "09e_Tracking_Spreadsheets": {}
    },
    "10_ARCHIVE": {
        "10a_Superseded_Documents": {},
        "10b_Old_Versions": {},
        "10c_Unclassified": {}
    }
}

# Classification rules (pattern, destination, subfolder_rule)
CLASSIFICATION_RULES = [
    (r"^\d{10}\.pdf$", "01_COURT_FILINGS/01a_Docket_Entries", "year_subfolder"),
    (r"NEF|Notice of Electronic Filing", "01_COURT_FILINGS/01e_Notices/NEF_Notices", None),
    (r"Motion to Quash.*Rule 58", "01_COURT_FILINGS/01b_Casey_Motions/Motion_to_Quash_Rule58", None),
    (r"Motion.*Audio Record", "01_COURT_FILINGS/01b_Casey_Motions/Motion_Audio_Recording", None),
    (r"Motion.*Reconsideration", "01_COURT_FILINGS/01b_Casey_Motions/Motion_Reconsideration", None),
    (r"Plaintiff.*Motion|Casey.*Motion", "01_COURT_FILINGS/01b_Casey_Motions/Other_Motions", None),
    (r"Motion.*Sanctions", "01_COURT_FILINGS/01c_Teresa_Brower_Motions/Sanctions_Motions", None),
    (r"Motion.*Trial.*Date", "01_COURT_FILINGS/01c_Teresa_Brower_Motions/Trial_Setting_Motions", None),
    (r"Defendant.*Motion|Teresa.*Motion|Brower.*Motion", "01_COURT_FILINGS/01c_Teresa_Brower_Motions/Other_Motions", None),
    (r"ORDER|Approved.*Order|Signed.*Order", "01_COURT_FILINGS/01d_Court_Orders", "order_type"),
    (r"Scheduling Order", "01_COURT_FILINGS/01d_Court_Orders/Scheduling_Orders", None),
    (r"Protective Order|TRO|Restraining", "01_COURT_FILINGS/01d_Court_Orders/Protective_Orders", None),
    (r"Exhibit[_\s-]T|OFW", "02_EVIDENCE/02a_Teresa_Exhibits/Exhibit_T_OFW_Communications", None),
    (r"Exhibit[_\s-]U|MyChart|Doctor", "02_EVIDENCE/02a_Teresa_Exhibits/Exhibit_U_Medical", None),
    (r"Exhibit[_\s-]V|School.*Report|Teaching Strategies", "02_EVIDENCE/02a_Teresa_Exhibits/Exhibit_V_School", None),
    (r"Nanoa.*Science|Exhibit[_\s-][W-Z]", "02_EVIDENCE/02a_Teresa_Exhibits/Exhibit_W-Z_Other", None),
    (r"EXHIBIT.*LIST.*Teresa", "02_EVIDENCE/02a_Teresa_Exhibits", None),
    (r"Asset.*Debt", "02_EVIDENCE/02e_Financial/Asset_Debt_Statements", None),
    (r"CSEA|Child Support", "02_EVIDENCE/02e_Financial/Child_Support_CSEA", None),
    (r"Subpoena|Return of Service", "03_DISCOVERY/03d_Subpoenas", "subpoena_type"),
    (r"[Cc]hat.*[Tt]otal|ChatGPT.*[Ee]xporter", "06_AI_ANALYSIS/06a_Chat_Transcripts/ChatGPT_Exports", None),
    (r"Aloha.*Kai.*Chat", "06_AI_ANALYSIS/06a_Chat_Transcripts/Perplexity_Sessions", None),
    (r"Evidence.*Management.*Setup", "06_AI_ANALYSIS/06b_JSON_Strategy_Files", None),
    (r"Legal.*Case.*Tracker", "06_AI_ANALYSIS/06b_JSON_Strategy_Files", None),
    (r"Custody.*Case.*Strategy", "06_AI_ANALYSIS/06b_JSON_Strategy_Files", None),
    (r"Motion.*Request\.json", "06_AI_ANALYSIS/06c_AI_Generated_Motions", None),
    (r"christmas.*strategy", "05_STRATEGY/05c_Trial_Strategy/Feb19_Hearing_Prep", None),
    (r"Ex Parte|Expedite.*Hearing|Withdraw.*Counsel", "07_TRIAL_NOTEBOOKS/07a_February_19_2025_Hearing", None),
    (r"February.*19.*2025|Feb.*19", "07_TRIAL_NOTEBOOKS/07a_February_19_2025_Hearing", None),
    (r".*", "10_ARCHIVE/10c_Unclassified", None)
]

# ═══════════════════════════════════════════════════════════════
# 🧠 INTELLIGENT CLASSIFICATION ENGINE
# ═══════════════════════════════════════════════════════════════

def get_file_year(filepath: str) -> str:
    """Extract year from filename or metadata"""
    year_match = re.search(r'(202[3-5])', filepath)
    if year_match:
        return year_match.group(1)
    try:
        stat = os.stat(filepath)
        mod_time = datetime.fromtimestamp(stat.st_mtime)
        return str(mod_time.year)
    except:
        return "2024"

def classify_file(filename: str, description: str = "") -> Tuple[str, str]:
    """Classify file and return (destination, suggested_name)"""
    full_text = f"{filename} {description}".lower()
    
    for pattern, destination, subfolder_rule in CLASSIFICATION_RULES:
        if re.search(pattern, filename, re.IGNORECASE) or re.search(pattern, description, re.IGNORECASE):
            # Apply subfolder rules
            if subfolder_rule == "year_subfolder":
                year = get_file_year(filename)
                destination = f"{destination}/{year}"
            elif subfolder_rule == "order_type":
                if "scheduling" in full_text:
                    destination = f"{destination}/Scheduling_Orders"
                elif "protective" in full_text or "tro" in full_text:
                    destination = f"{destination}/Protective_Orders"
                else:
                    destination = f"{destination}/Other_Orders"
            elif subfolder_rule == "subpoena_type":
                if "school" in full_text:
                    destination = f"{destination}/School_Subpoenas"
                elif "medical" in full_text or "doctor" in full_text:
                    destination = f"{destination}/Medical_Subpoenas"
                else:
                    destination = f"{destination}/Other_Subpoenas"
            
            new_name = generate_smart_filename(filename, description)
            return destination, new_name
    
    return "10_ARCHIVE/10c_Unclassified", filename

def generate_smart_filename(original: str, description: str = "") -> str:
    """Generate descriptive filename: [YYYYMMDD]_[DocType]_[Dkt###]_[ShortDesc].[ext]"""
    date_str = "UNDATED"
    date_patterns = [
        r"(\d{4})[-._](\d{2})[-._](\d{2})",
        r"(\d{2})[-._](\d{2})[-._](\d{4})",
        r"Filed[:\s]+(\d{1,2})[-._/](\d{1,2})[-._/](\d{2,4})"
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, f"{original} {description}")
        if match:
            groups = match.groups()
            if len(groups[0]) == 4:
                date_str = f"{groups[0]}{groups[1].zfill(2)}{groups[2].zfill(2)}"
            else:
                year = groups[2] if len(groups[2]) == 4 else f"20{groups[2]}"
                date_str = f"{year}{groups[0].zfill(2)}{groups[1].zfill(2)}"
            break
    
    doc_type = "DOC"
    type_mapping = {
        r"Motion": "MOTION",
        r"Order|ORDER": "ORDER",
        r"Exhibit": "EXHIBIT",
        r"Subpoena": "SUBPOENA",
        r"Notice": "NOTICE",
        r"Asset.*Debt": "ASSET_DEBT",
        r"Report": "REPORT",
        r"Strategy": "STRATEGY"
    }
    
    for pattern, dtype in type_mapping.items():
        if re.search(pattern, original, re.IGNORECASE):
            doc_type = dtype
            break
    
    docket = ""
    docket_match = re.search(r"[Dd]kt[\.#]?\s*(\d+)", f"{original} {description}")
    if docket_match:
        docket = f"_Dkt{docket_match.group(1)}"
    
    desc = description if description else original
    desc = re.sub(r'[^\w\s-]', '', desc)
    desc = re.sub(r'\s+', '_', desc)[:50]
    
    ext = Path(original).suffix or ".pdf"
    return f"{date_str}_{doc_type}{docket}_{desc}{ext}"

# ═══════════════════════════════════════════════════════════════
# 🗄️ SQLITE TRACKING DATABASE
# ═══════════════════════════════════════════════════════════════

def init_tracking_db(db_path: str):
    """Initialize SQLite database for tracking"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_path TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            new_path TEXT NOT NULL,
            new_filename TEXT NOT NULL,
            file_hash TEXT,
            file_size INTEGER,
            classification TEXT,
            operation_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            success BOOLEAN,
            error_message TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✓ Tracking database initialized\n")

def log_file_operation(db_path: str, original_path: str, new_path: str, 
                       classification: str, success: bool, error: str = None):
    """Log file operation to database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        with open(original_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()
        file_size = os.path.getsize(original_path)
    except:
        file_hash = None
        file_size = None
    
    cursor.execute("""
        INSERT INTO file_operations 
        (original_path, original_filename, new_path, new_filename, 
         file_hash, file_size, classification, success, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        original_path,
        os.path.basename(original_path),
        new_path,
        os.path.basename(new_path),
        file_hash,
        file_size,
        classification,
        success,
        error
    ))
    
    conn.commit()
    conn.close()

# ═══════════════════════════════════════════════════════════════
# 🚀 MAIN ORGANIZATION ENGINE
# ═══════════════════════════════════════════════════════════════

def create_folder_structure(root: str):
    """Recursively create entire folder structure"""
    def create_recursive(base_path: str, structure: Dict):
        for folder, subfolders in structure.items():
            folder_path = os.path.join(base_path, folder)
            os.makedirs(folder_path, exist_ok=True)
            if subfolders:
                create_recursive(folder_path, subfolders)
    
    create_recursive(root, MASTER_STRUCTURE)
    print(f"✓ Created folder structure\n")

def organize_dropbox(source_dir: str, target_root: str, 
                    db_path: str, dry_run: bool = False):
    """Main organization function"""
    print(f"""
╔════════════════════════════════════════════════════════════════╗
║  🔥 DROPBOX ORGANIZER - CASE 1FDV-23-0001009 🔥              ║
║  Files: 2,703+ documents                                       ║
║  Mode: {'DRY RUN' if dry_run else 'LIVE EXECUTION'}                                          ║
╚════════════════════════════════════════════════════════════════╝
    """)
    
    if not dry_run:
        create_folder_structure(target_root)
        init_tracking_db(db_path)
    
    stats = {
        "total_scanned": 0,
        "successfully_moved": 0,
        "renamed": 0,
        "skipped": 0,
        "errors": [],
        "by_category": defaultdict(int)
    }
    
    print("🔍 Scanning files...\n")
    
    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            stats["total_scanned"] += 1
            source_path = os.path.join(root, filename)
            
            if filename.startswith('.') or filename.endswith('.tmp'):
                stats["skipped"] += 1
                continue
            
            try:
                destination, new_filename = classify_file(filename, "")
                category = destination.split('/')[0]
                stats["by_category"][category] += 1
                
                dest_path = os.path.join(target_root, destination, new_filename)
                
                if os.path.exists(dest_path):
                    base, ext = os.path.splitext(new_filename)
                    counter = 1
                    while os.path.exists(dest_path):
                        new_filename = f"{base}_copy{counter}{ext}"
                        dest_path = os.path.join(target_root, destination, new_filename)
                        counter += 1
                
                if dry_run:
                    print(f"[DRY RUN] {filename} → {destination}/{new_filename}")
                else:
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy2(source_path, dest_path)
                    log_file_operation(db_path, source_path, dest_path, destination, True)
                    stats["successfully_moved"] += 1
                    if new_filename != filename:
                        stats["renamed"] += 1
                    print(f"✓ {filename} → {destination}/{new_filename}")
            
            except Exception as e:
                error_msg = f"Error: {filename}: {str(e)}"
                stats["errors"].append(error_msg)
                print(f"✗ {error_msg}")
                if not dry_run:
                    log_file_operation(db_path, source_path, "", destination, False, str(e))
    
    print("\n" + "="*70)
    print("🎯 ORGANIZATION COMPLETE!")
    print("="*70)
    print(f"Total Scanned:      {stats['total_scanned']}")
    print(f"Successfully Moved: {stats['successfully_moved']}")
    print(f"Files Renamed:      {stats['renamed']}")
    print(f"Skipped:            {stats['skipped']}")
    print(f"Errors:             {len(stats['errors'])}")
    print("\n📊 Distribution:")
    for cat, count in sorted(stats['by_category'].items()):
        print(f"  {cat}: {count}")
    print("="*70 + "\n")
    
    return stats

# ═══════════════════════════════════════════════════════════════
# 🎯 EXECUTION
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    
    SOURCE_DIR = "/Users/casey/Dropbox/Case_1FDV-23-0001009"
    TARGET_DIR = "/Users/casey/Dropbox/Case_1FDV-23-0001009_ORGANIZED"
    DB_PATH = "/Users/casey/Dropbox/organization_tracking.db"
    
    DRY_RUN = "--dry-run" in sys.argv or "-d" in sys.argv
    
    if DRY_RUN:
        print("⚠️  DRY RUN MODE\n")
    else:
        print("🔥 LIVE MODE\n")
        response = input("Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Aborted")
            sys.exit(0)
    
    results = organize_dropbox(SOURCE_DIR, TARGET_DIR, DB_PATH, DRY_RUN)
    
    print("🎉 COMPLETE!")
    print(f"\n📂 Organized: {TARGET_DIR}")
    print(f"📊 Database: {DB_PATH}")
    print(f"🔗 GitHub: {CASE_CONFIG['github_repo']}\n")
