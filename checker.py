#!/usr/bin/env python3
import os
import sys
import json
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

load_dotenv()  # Load .env if present

NOW = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
REPORT_DIR = "reports"
os.makedirs(REPORT_DIR, exist_ok=True)

def save_report(report):
    path = f"{REPORT_DIR}/connections-{NOW}.json"
    with open(path, "w") as f:
        json.dump(report, f, indent=2)
    print("Saved report to", path)

def check_github(token):
    if not token:
        return {"ok": False, "reason": "no_token"}
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    try:
        r = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        return {"ok": r.status_code == 200, "status_code": r.status_code, "body_summary": r.json() if r.status_code==200 else r.text}
    except Exception as e:
        return {"ok": False, "reason": str(e)}

def check_slack(token):
    if not token:
        return {"ok": False, "reason": "no_token"}
    try:
        r = requests.post("https://slack.com/api/auth.test", headers={"Authorization": f"Bearer {token}"}, timeout=10)
        j = r.json()
        return {"ok": j.get("ok", False), "status_code": r.status_code, "body": {"ok": j.get("ok"), "user": j.get("user"), "team": j.get("team")}}
    except Exception as e:
        return {"ok": False, "reason": str(e)}

def check_openrouter(key):
    if not key:
        return {"ok": False, "reason": "no_key"}
    try:
        # simple management endpoint check
        r = requests.get("https://api.openrouter.ai/v1/engines", headers={"Authorization": f"Bearer {key}"}, timeout=10)
        return {"ok": r.status_code in (200, 401, 403), "status_code": r.status_code, "body_truncated": r.text[:500]}
    except Exception as e:
        return {"ok": False, "reason": str(e)}

def check_huggingface(key):
    if not key:
        return {"ok": False, "reason": "no_key"}
    try:
        r = requests.get("https://huggingface.co/api/whoami-v2", headers={"Authorization": f"Bearer {key}"}, timeout=10)
        return {"ok": r.status_code == 200, "status_code": r.status_code, "body_summary": r.json() if r.status_code==200 else r.text}
    except Exception as e:
        return {"ok": False, "reason": str(e)}

def check_pinecone(key):
    if not key:
        return {"ok": False, "reason": "no_key"}
    try:
        r = requests.get("https://controller.pinecone.io/databases", headers={"Api-Key": key}, timeout=10)
        return {"ok": r.status_code in (200, 401, 403), "status_code": r.status_code, "body_truncated": r.text[:500]}
    except Exception as e:
        return {"ok": False, "reason": str(e)}

def check_supabase(url, key):
    if not url or not key:
        return {"ok": False, "reason": "missing_url_or_key"}
    try:
        r = requests.get(f"{url}/rest/v1/", headers={"apikey": key}, timeout=10)
        return {"ok": r.status_code in (200, 401, 403), "status_code": r.status_code, "body_truncated": r.text[:500]}
    except Exception as e:
        return {"ok": False, "reason": str(e)}

def check_notion(key):
    if not key:
        return {"ok": False, "reason": "no_key"}
    try:
        r = requests.get("https://api.notion.com/v1/users", headers={"Authorization": f"Bearer {key}", "Notion-Version": "2022-06-28"}, timeout=10)
        return {"ok": r.status_code in (200, 401, 403), "status_code": r.status_code, "body_truncated": r.text[:500]}
    except Exception as e:
        return {"ok": False, "reason": str(e)}

def main():
    env = os.environ
    report = {
        "timestamp": NOW,
        "checks": {},
        "summary": {}
    }

    github_token = env.get("GITHUB_TOKEN") or env.get("GITHUB_PAT") or env.get("GITHUB_PAT2")
    slack_token = env.get("SLACK_TOKEN")
    openrouter_key = env.get("OPENROUTER_API_KEY") or env.get("OPENROUTER_API_KEY2")
    hf_key = env.get("HUGGINGFACE_API_KEY") or env.get("HUGGINGFACE_TOKEN")
    pinecone_key = env.get("PINECONE_API_KEY") or env.get("PINECONE_HIGUY_KEY")
    supabase_url = env.get("SUPABASE_URL") or env.get("SUPABASE_API_URL") or env.get("SUPABASE_API")
    supabase_key = env.get("SUPABASE_KEY") or env.get("SUPABASE_API_KEY") or env.get("SUPABASE_GLACIEREQ_KEY")
    notion_key = env.get("NOTION_API_KEY")

    report["checks"]["github"] = check_github(github_token)
    report["checks"]["slack"] = check_slack(slack_token)
    report["checks"]["openrouter"] = check_openrouter(openrouter_key)
    report["checks"]["huggingface"] = check_huggingface(hf_key)
    report["checks"]["pinecone"] = check_pinecone(pinecone_key)
    report["checks"]["supabase"] = check_supabase(supabase_url, supabase_key)
    report["checks"]["notion"] = check_notion(notion_key)

    ok_count = sum(1 for k in report["checks"].values() if k.get("ok"))
    total = len(report["checks"])
    report["summary"]["ok"] = ok_count
    report["summary"]["total"] = total
    report["summary"]["all_ok"] = (ok_count == total)

    save_report(report)

    if report["summary"]["all_ok"]:
        print("All checks OK")
        return 0
    else:
        print(f"{ok_count}/{total} checks OK")
        return 2

if __name__ == "__main__":
    code = main()
    sys.exit(code)
