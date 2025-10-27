# PROJECT HEAD

**Mission**: Umbrella for integrated upstreams and experimental surfaces feeding FILEBOSS.

**Rules of Engagement**
- No vendored virtualenvs or build artifacts.
- No plaintext secrets. Use `.env.example` only.
- If upstreams are included, prefer submodules or subtree.

**Structure (proposed)**
- `/PROJECT HEAD/sources/<upstream>` — mirrored or submodule references.
- `/PROJECT HEAD/pipelines/` — ETL/orchestration glue.

**Next**
- Convert any vendored code into submodules and add ownership mapping.

— The Architect’s Orchestrator
