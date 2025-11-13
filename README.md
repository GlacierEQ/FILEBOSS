# Connections Diagnostics

Non-destructive health checks for external connectors (GitHub, Slack, OpenRouter, Hugging Face, Pinecone, Supabase, Notion, etc.)

Usage
- Populate environment variables (examples in .env.example).
- Run locally: `python3 checker.py`
- CI: included GitHub Actions workflow to run on push or schedule.

Outputs
- JSON report saved to ./reports/connections-YYYYMMDDTHHMMSS.json
- Exit code 0 if all checks pass; non-zero if any check fails.

Security
- This script only performs read-only/auth checks. Do not commit secrets to the repo. Use GitHub Actions secrets or your CI secret store.
