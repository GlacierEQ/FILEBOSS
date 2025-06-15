import time
import json
from pathlib import Path
from datetime import datetime

LOG_FILE = Path("logs/mem0_pushes.json")
CODEX_FILE = Path("logs/CodexWeaver_visual_links.json")
CHRONA_FILE = Path("logs/Chrona_visual_timeline.json")

seen_uids = set()

def load_json(path):
    try:
        return json.loads(path.read_text())
    except:
        return []

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2))

def process_entry(entry):
    uid = entry.get("filename", "") + entry.get("timestamp", "")
    if uid in seen_uids:
        return None, None
    seen_uids.add(uid)

    codex = {
        "type": "symbolic_thread",
        "source": "Photoprism/Watchdog",
        "linked_file": entry["filename"],
        "tags": entry["symbol_tags"],
        "motion_link": entry["linked_motion"],
        "timestamp": entry["timestamp"]
    }

    chrona = {
        "event_type": "Visual_Ingest",
        "source": "Photoprism",
        "file": entry["filename"],
        "anchor_time": entry["timestamp"],
        "symbol_tags": entry["symbol_tags"]
    }

    return codex, chrona

def sync():
    if not LOG_FILE.exists():
        return

    codex_data = load_json(CODEX_FILE)
    chrona_data = load_json(CHRONA_FILE)

    with open(LOG_FILE, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                codex, chrona = process_entry(entry)
                if codex and chrona:
                    codex_data.append(codex)
                    chrona_data.append(chrona)
            except json.JSONDecodeError:
                continue

    save_json(CODEX_FILE, codex_data)
    save_json(CHRONA_FILE, chrona_data)

if __name__ == "__main__":
    print("📡 Mem0 Sync Daemon is now active and watching for new ingest...")
    while True:
        sync()
        time.sleep(10)
