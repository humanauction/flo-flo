PYTHON := $(shell command -v python3 2> /dev/null || echo python)
VENV_BIN := .venv/bin
PYTEST := $(VENV_BIN)/pytest
UVICORN := $(VENV_BIN)/uvicorn

.PHONY: init bk fr table test test-backend test-agents test-frontend lint help check-venv

check-venv:
    @if [ ! -x "$(VENV_BIN)/python" ]; then \
        echo "ERROR: .venv not found. Create and activate it first."; \
        echo "Example: python3 -m venv .venv && source .venv/bin/activate"; \
        exit 1; \
    fi

init: check-venv
    @echo "Installing backend deps..."
    $(VENV_BIN)/pip install -r backend/requirements.txt
    @echo "Installing frontend deps..."
    cd frontend && npm install
    @echo "Done."

bk: check-venv
    cd backend && ../$(UVICORN) app.main:app --reload --port 8000

fr:
    cd frontend && npm run dev

table: check-venv
    cd backend && ../$(VENV_BIN)/python -c "from app.db.database import init_db; init_db()"

test: test-backend test-agents

test-backend: check-venv
    cd backend && ../$(PYTEST) -q tests

test-agents: check-venv
    cd agents && ../$(PYTEST) -q tests

test-frontend:
    cd frontend && npm test

lint:
    cd frontend && npm run lint

help:
    @echo "init          Install backend/frontend dependencies"
    @echo "bk            Run FastAPI backend on :8000"
    @echo "fr            Run Next.js frontend"
    @echo "table         Initialize DB tables"
    @echo "test          Run backend + agents tests"
    @echo "test-backend  Run backend pytest suite"
    @echo "test-agents   Run agents pytest suite"
    @echo "test-frontend Run frontend tests (requires jest setup)"
    @echo "lint          Run frontend lint"