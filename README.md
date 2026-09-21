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
- MongoDB (e.g. `docker run -d -p 27017:27017 mongo:7`)

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

## URL API

| Method | Path                   | Purpose                                             |
| ------ | ---------------------- | --------------------------------------------------- |
| POST   | `/api/urls`            | Store a movie page URL (`{"url": "..."}`), 409 if dup |
| GET    | `/api/urls`            | List stored URLs, newest first                      |
| GET    | `/api/urls/{id}`       | Get one URL with its crawl result                   |
| PUT    | `/api/urls/{id}`       | Change the URL (clears the previous crawl result)   |
| DELETE | `/api/urls/{id}`       | Delete the URL                                      |
| POST   | `/api/urls/{id}/crawl` | Fetch the page now; store title, description, images, stream and embed URLs (502 + `status: failed` on error) |

## Configuration

- API: env vars prefixed `API_` (see `apps/api/.env.example`); `API_MONGO_URI` and
  `API_MONGO_DB` select the MongoDB database.
- Web: `VITE_API_BASE_URL` (see `apps/web/.env.example`); leave empty in dev.
