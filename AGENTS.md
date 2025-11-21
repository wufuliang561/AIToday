# Repository Guidelines

## Project Structure & Module Organization
AIToday splits into `backend/` (FastAPI) and `frontend/` (Next.js). `backend/app` contains routers (`api/`), config (`core/`), data access (`db/`), models, and business services; ETL scripts plus `sources.yaml` sit at the folder root. The App Router UI lives under `frontend/src/app`, with shared components in `src/components` and helpers in `src/lib`. Root scripts (`start.sh`, `stop.sh`, `docker-compose.yaml`, `prd.md`) orchestrate dev workflows and specs.

## Build, Test, and Development Commands
`./start.sh` launches uvicorn on 8000 and Next dev mode on 3000; `./stop.sh` terminates the background jobs. Provision PostgreSQL with `docker-compose up -d postgres`. Backend loop: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload`. Frontend loop: `cd frontend && npm install && npm run dev`. Use `npm run build && npm run start` for production previews and `npm run lint` for ESLint/Core Web Vitals rules.

## Coding Style & Naming Conventions
Python uses 4-space indentation, type hints, and FastAPI dependency injection; keep routers thin, push orchestration into `services/`, and store IO schemas in `models/`. Script names should describe their data source (`collect_reddit.py`) or action. TypeScript follows Next.js defaults: PascalCase components, camelCase hooks/helpers, Tailwind utilities ordered layout→spacing→color. Do not bypass linting—`npm run lint` and `ruff check` (if installed) must pass before commits.

## Testing Guidelines
Backend tests belong in `backend/tests` and rely on `pytest` plus `httpx.AsyncClient`; run `pytest backend/tests --maxfail=1` before opening a PR. Integration suites should point at the docker Postgres and clean up via `init_db.py`. Frontend tests live in `frontend/src/__tests__`, use Jest + React Testing Library (wire `npm run test` to `next test`), and snapshot UI when helpful. Target ≥80% line coverage for new surfaces.

## Commit & Pull Request Guidelines
History shows short imperative subjects ("Add Chinese comments to backend...") so keep summaries ≤72 characters, with issue links in the body (`Refs #42`). Each PR must describe the problem, outline the solution, list verification commands (uvicorn, npm run dev, pytest/npm run test), and attach screenshots for UI changes. Reference `prd.md` items whenever you implement a roadmap bullet.

## Configuration & Operational Notes
Secrets live in `backend/.env` and should mirror the keys documented in `backend/README.md`; use `.env.local` for frontend overrides. Update `sources.yaml` when onboarding feeds and justify the choice in your PR. Schema or embedding changes should land alongside updates to `init_db.py`, `update_schema.py`, and `verify_embedding.py` so operators can re-run the pipeline deterministically.
