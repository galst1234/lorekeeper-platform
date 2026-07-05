# Lorekeeper Platform

This file provides guidance to AI coding agents (Claude Code, Codex, etc.) working in this repository.

`AGENTS.md` is a symlink to this file — edit only `CLAUDE.md`.

## Repo layout

Three independent projects, each with its own dependency manifest and lockfile:

- `frontend/` — React 19 + TanStack Router/Query SPA (Vite, Tailwind v4 + shadcn/ui). npm.
- `api/` — FastAPI backend: SQLAlchemy async/asyncpg + Alembic migrations, SuperTokens auth. `uv` + Python >=3.14.
- `agent/` — separate FastAPI service for agent tooling. `uv` + Python >=3.14.

Nested `CLAUDE.md` (and their linked `AGENTS.md`) files exist closer to the code they govern and take precedence for their subtree — notably `frontend/CLAUDE.md` (component/page conventions), `api/src/api/routers/CLAUDE.md` (router package structure, OpenAPI documentation requirements), `api/src/api/models/CLAUDE.md` (model registration), and `api/migrations/CLAUDE.md` (Alembic migration rules).
Each `CLAUDE.md` file has a `AGENTS.md` symlink next to it for other agents to read.

## Commands

**Frontend** (run from `frontend/`):
- `npm run dev` — dev server (runs `generate:api` first)
- `npm run build` — typecheck (`tsc -b`) + production build
- `npm run lint` / `npm run lint:fix` — Biome
- `npm run generate:api` — regenerate `src/api/generated/` (hey-api client) from `api/openapi.json`; also runs `sync:spec` first
- No test suite currently exists for `frontend/`.

**API / agent** (run from `api/` or `agent/`, via `uv run`):
- `uv run ruff check .` — lint
- `uv run ty check .` — type check
- `uv run pytest` — run tests (`api/` only; `agent/` has no test suite yet)
- `uv run pytest tests/path/to/test_file.py::test_name` — run a single test
- `api/` only: `uv run python scripts/export_openapi_schema.py` — regenerate `api/openapi.json`; **required after any route/schema change** (CI fails on drift), and the frontend's generated client depends on it being current
- `api/` only: `alembic revision --autogenerate -m "description"` — create a migration (never hand-write migration files except for data backfills or multistep NOT NULL additions; see `api/migrations/CLAUDE.md`)

CI (`.github/workflows/ci.yml`) path-filters per project and runs: Ruff + Ty + Pytest + OpenAPI-drift check for `api/`; Ruff + Ty for `agent/`; Biome for `frontend/`.

## Architecture

**Campaign-scoped resource model.** Nearly everything in the API hangs off a `Campaign` (`api/src/api/models/campaign.py`): characters, items, chronicle entries, and memberships are all children of a campaign, addressed by campaign slug in the URL (`/api/v1/campaigns/{slug}/...`). Route access control is layered through FastAPI dependencies in `api/src/api/routers/campaigns/dependencies.py` — `get_campaign_or_404` → `require_campaign_member` / `require_campaign_owner` — and sub-resource routers (`characters.py`, `items.py`, `chronicle.py`, `members.py`, `invites.py`) depend on these rather than re-implementing access checks.

**Frontend routing is file-based and generated.** Routes live in `frontend/src/routes/` following TanStack Router's flat file-naming convention (e.g. `campaigns.$slug.chronicle.$entrySlug.tsx`); `routeTree.gen.ts` is generated from these files and must not be hand-edited. Route files themselves stay routing-only (`beforeLoad`/`loader`/`validateSearch`/`component`); actual page JSX lives in `src/pages/`, read via `getRouteApi(path)` rather than importing the route's `Route` export directly (see `frontend/CLAUDE.md` for the full pattern).

**The frontend API client is generated, not handwritten.** `frontend/src/api/generated/` (hey-api, gitignored) is produced from `api/openapi.json` by `npm run generate:api`. Backend route/schema changes require regenerating `api/openapi.json` (`uv run python scripts/export_openapi_schema.py` in `api/`) before the frontend client will reflect them — CI enforces this is committed and in sync.

**Entity linking spans both stacks.** Free-text fields (character/item descriptions, chronicle entry bodies) support an inline directive syntax (e.g. `:character[label]{slug}`) parsed via `remark-directive` on the frontend (`frontend/src/components/markdown/`). `useEntityResolver` (`use-entity-resolver.ts`) fetches a campaign's characters/items/chronicle entries and resolves directive slugs to display names/links client-side — there is no backend-side entity-reference resolution or validation.

**Auth** is SuperTokens end-to-end: `api/src/api/supertokens.py` configures the backend recipe, `frontend/src/lib/auth.ts` configures the frontend SDK, and `get_current_user` (`api/src/api/auth.py`) is the FastAPI dependency gating authenticated routes.

**Observability** is Sentry + OpenTelemetry in both `api/` and `agent/` (`observability.py` in each), and Sentry only on the frontend (`main.tsx`).

## Review guidelines

- Skip reviewing lock files (`package-lock.json`, `uv.lock`) and the generated OpenAPI schema (`api/openapi.json`) — they're machine-generated; focus on handwritten source changes.
