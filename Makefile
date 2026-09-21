API_DIR := apps/api
WEB_DIR := apps/web
VENV    := $(API_DIR)/.venv
PY      := $(VENV)/bin

.PHONY: install install-api install-web dev dev-api dev-web test lint build

install: install-api install-web

install-api:
	python3 -m venv $(VENV)
	$(PY)/pip install -e '$(API_DIR)[dev]'

install-web:
	cd $(WEB_DIR) && pnpm install

# Run API and web together; Ctrl-C stops both.
dev:
	$(MAKE) -j2 dev-api dev-web

dev-api:
	cd $(API_DIR) && .venv/bin/uvicorn media_proxy_api.main:app --reload --port 8000

dev-web:
	cd $(WEB_DIR) && pnpm dev

test:
	cd $(API_DIR) && .venv/bin/pytest

lint:
	cd $(API_DIR) && .venv/bin/ruff check . && .venv/bin/ruff format --check .
	cd $(WEB_DIR) && pnpm lint

build:
	cd $(WEB_DIR) && pnpm build
