# 🚀 HYBRID DEPLOYMENT GUIDE - Case 1FDV-23-0001009

## 🎯 Mission Objective

Organize **2,703 legal documents** across your Dropbox using a hybrid approach:
1. **Local execution** for immediate results
2. **GitHub MCP orchestration** for automation
3. **Cloud backup** for redundancy

**Critical Deadline:** February 19, 2025 @ 1:30 PM HST - Pre-Trial Hearing (**62 days!**)

---

## 🔥 PHASE 1: Local Execution (Immediate)

### Step 1: Download the organizer script

```bash
# Clone your FILEBOSS repo
cd ~/Documents
git clone https://github.com/GlacierEQ/FILEBOSS.git
cd FILEBOSS

# Or just download the script directly
curl -O https://raw.githubusercontent.com/GlacierEQ/FILEBOSS/main/dropbox_organizer_case_1009.py
```

### Step 2: Test with dry run

```bash
# This won't move any files - just shows what would happen
python dropbox_organizer_case_1009.py --dry-run
```

**Review the output to ensure classification looks correct!**

### Step 3: Execute live organization

```bash
# This WILL move and rename files
python dropbox_organizer_case_1009.py
```

You'll be prompted to confirm. Type `yes` to proceed.

### Step 4: Review results

**Organized structure will be at:**
`/Users/casey/Dropbox/Case_1FDV-23-0001009_ORGANIZED/`

**Critical folders to check:**
- `07_TRIAL_NOTEBOOKS/07a_February_19_2025_Hearing/` - Your Feb 19 materials
- `02_EVIDENCE/02a_Teresa_Exhibits/` - Teresa's exhibits T, U, V
- `01_COURT_FILINGS/01b_Casey_Motions/` - Your motions
- `06_AI_ANALYSIS/` - ChatGPT exports, strategy JSONs

**Tracking database:**
`/Users/casey/Dropbox/organization_tracking.db`

Query it with:
```bash
sqlite3 /Users/casey/Dropbox/organization_tracking.db "SELECT COUNT(*) FROM file_operations;"
```

---

## ⚡ PHASE 2: GitHub MCP Orchestration (Automation)

### Enable GitHub Actions automation

The workflow is already committed: [`.github/workflows/dropbox-organizer.yml`](https://github.com/GlacierEQ/FILEBOSS/blob/main/.github/workflows/dropbox-organizer.yml)

**It provides:**
- 💬 Manual trigger via GitHub UI
- 📅 Weekly automatic runs (Sundays 2 AM HST)
- ✅ Dry-run or live mode selection
- 📊 Auto-generated organization reports
- 🐛 Issue creation for manual review

### Setup secrets (one-time)

1. Go to: https://github.com/GlacierEQ/FILEBOSS/settings/secrets/actions

2. Add secret:
   - Name: `DROPBOX_ACCESS_TOKEN`
   - Value: Your Dropbox API token

### Run the automation

**Manual trigger:**
1. Visit: https://github.com/GlacierEQ/FILEBOSS/actions/workflows/dropbox-organizer.yml
2. Click "Run workflow"
3. Select mode: `dry-run` or `live`
4. Click green "Run workflow" button

**Results:**
- Check the Actions tab for execution logs
- Auto-generated `ORGANIZATION_REPORT.md` gets committed
- GitHub Issue created for your manual review

---

## 📊 PHASE 3: Analysis & Optimization

### Generate exhibit index

```python
# Run after organization complete
python -c "
import os
import json
from pathlib import Path

evidence_dir = '/Users/casey/Dropbox/Case_1FDV-23-0001009_ORGANIZED/02_EVIDENCE'
exhibit_index = []

for root, dirs, files in os.walk(evidence_dir):
    for file in files:
        if 'Exhibit' in file:
            exhibit_index.append({
                'file': file,
                'path': os.path.join(root, file),
                'category': Path(root).name
            })

with open('exhibit_index.json', 'w') as f:
    json.dump(exhibit_index, f, indent=2)

print(f'Generated exhibit index: {len(exhibit_index)} exhibits')
"
```

### Query tracking database

```sql
-- Total files organized
SELECT COUNT(*) FROM file_operations WHERE success = 1;

-- Files by category
SELECT classification, COUNT(*) as count 
FROM file_operations 
WHERE success = 1 
GROUP BY classification 
ORDER BY count DESC;

-- Files renamed
SELECT original_filename, new_filename 
FROM file_operations 
WHERE original_filename != new_filename 
LIMIT 20;

-- Feb 19 hearing materials
SELECT * FROM file_operations 
WHERE classification LIKE '%February_19%';
```

---

## 📱 PHASE 4: Mobile Access Setup

### Dropbox mobile app

1. Open Dropbox app on your phone
2. Navigate to: `Case_1FDV-23-0001009_ORGANIZED/`
3. Star/favorite these folders:
   - `07_TRIAL_NOTEBOOKS/07a_February_19_2025_Hearing/`
   - `02_EVIDENCE/02a_Teresa_Exhibits/`
   - `09_REFERENCE/`

4. Enable offline access for Feb 19 folder (tap ⋮ → Make available offline)

### Quick access from Notion

Add to your Notion case tracker:

```markdown
## 📂 Organized Files

[View in Dropbox](https://www.dropbox.com/home/Case_1FDV-23-0001009_ORGANIZED)

### Key Folders
- [Feb 19 Hearing](https://www.dropbox.com/home/Case_1FDV-23-0001009_ORGANIZED/07_TRIAL_NOTEBOOKS/07a_February_19_2025_Hearing)
- [Evidence](https://www.dropbox.com/home/Case_1FDV-23-0001009_ORGANIZED/02_EVIDENCE)
- [Court Filings](https://www.dropbox.com/home/Case_1FDV-23-0001009_ORGANIZED/01_COURT_FILINGS)
```

---

## 🔧 Troubleshooting

### Script fails with "Permission denied"

```bash
chmod +x dropbox_organizer_case_1009.py
```

### SQLite database locked

```bash
# Close any SQLite browser windows
rm /Users/casey/Dropbox/organization_tracking.db-journal
```

### Undo organization (rollback)

```python
import sqlite3
import shutil

conn = sqlite3.connect('/Users/casey/Dropbox/organization_tracking.db')
cursor = conn.cursor()

# Get all successful operations
cursor.execute("SELECT original_path, new_path FROM file_operations WHERE success = 1")
operations = cursor.fetchall()

# Reverse each operation
for original, new in operations:
    if os.path.exists(new):
        os.makedirs(os.path.dirname(original), exist_ok=True)
        shutil.move(new, original)
        print(f"Restored: {os.path.basename(original)}")

print(f"Rollback complete: {len(operations)} files restored")
```

---

## 🎯 Next Steps

### Immediate (Today)
- [ ] Run dry-run to preview organization
- [ ] Review classification of sample files
- [ ] Execute live organization
- [ ] Verify Feb 19 hearing folder is complete

### This Week
- [ ] Generate exhibit index
- [ ] Create Feb 19 trial notebook outline
- [ ] Setup GitHub Actions secrets
- [ ] Test automation with dry-run mode

### Before Feb 19 Hearing
- [ ] Weekly automated re-organization (catches new files)
- [ ] Print exhibit index for court
- [ ] Prepare USB backup of critical folders
- [ ] Share organized Dropbox folders with attorney (if applicable)

---

## 🔗 Resources

- **GitHub Repo:** https://github.com/GlacierEQ/FILEBOSS
- **Script:** [dropbox_organizer_case_1009.py](https://github.com/GlacierEQ/FILEBOSS/blob/main/dropbox_organizer_case_1009.py)
- **Actions:** [View workflows](https://github.com/GlacierEQ/FILEBOSS/actions)
- **Issues:** [Track progress](https://github.com/GlacierEQ/FILEBOSS/issues)

---

**Questions? Create an issue:** https://github.com/GlacierEQ/FILEBOSS/issues/new

🔥 **Built with Juggernaut Jack energy** 🔥
