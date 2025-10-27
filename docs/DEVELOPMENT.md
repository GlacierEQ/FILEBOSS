# Development Quickstart

1. Copy `.env.example` → `.env` and set values.
2. `make bootstrap` (installs dev deps, pre-commit).
3. `docker compose up -d` to start db/redis/minio.
4. `alembic upgrade head` then run API: `uvicorn app:app --reload`.
5. (Optional) `npm run dev` in `your-next-app/`.

## Testing
`make test`

## Conventions
- ruff+black+isort, mypy.
- PRs require CI green + one review (enable in repo settings).
