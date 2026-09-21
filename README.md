# media-proxy-ui

Monorepo with a Python REST API and a React UI.

```
apps/
  api/   FastAPI service (Python ≥3.12)   → http://localhost:8000/api
  web/   React + Vite + TypeScript         → http://localhost:5173
```

In development, Vite proxies `/api/*` to the API, so the UI calls relative paths.

## Prerequisites

- Python 3.12+
- Node 22+ and pnpm

## Commands

| Command        | What it does                                  |
| -------------- | --------------------------------------------- |
| `make install` | Create `apps/api/.venv`, install API + web deps |
| `make dev`     | Run API (port 8000) and UI (port 5173) together |
| `make test`    | Run API tests (pytest)                        |
| `make lint`    | Ruff for the API, oxlint for the UI           |
| `make build`   | Production build of the UI to `apps/web/dist` |

API docs (Swagger UI): http://localhost:8000/api/docs

## Adding an endpoint

1. Add a router module in `apps/api/src/media_proxy_api/routers/`.
2. Register it in `main.py` with `app.include_router(..., prefix="/api")`.
3. Add a typed call in `apps/web/src/api/client.ts`.

## Configuration

- API: env vars prefixed `API_` (see `apps/api/.env.example`).
- Web: `VITE_API_BASE_URL` (see `apps/web/.env.example`); leave empty in dev.
