PYTHON := $(shell command -v python3 2>/dev/null || command -v python)
VENV_BIN := .venv/bin
PYTEST := $(VENV_BIN)/pytest
UVICORN := $(VENV_BIN)/uvicorn

.PHONY: init bk fr table test test-bk test-agents test-fr lint help check-venv

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
	cd backend && $(PYTHON) -m uvicorn app.main:app --reload --port 8000

fr:
	cd frontend && npm run dev

table: check-venv
	cd backend && ../$(VENV_BIN)/python -c "from app.db.database import init_db; init_db()"

test: test-bk test-agents

test-bk: check-venv
	cd backend && $(PYTHON) -m pytest -q tests

test-agents: check-venv
	cd agents && $(PYTHON) -m pytest -q tests

test-fr:
	cd frontend && npm test

test-manual:
	python -m pytest -q -m external -rs -vv agents/tests/test_scraper_agent.py

lint:
	cd frontend && npm run lint

help:
	@echo "init          Install backend/frontend dependencies"
	@echo "bk            Run FastAPI backend on :8000"
	@echo "fr            Run Next.js frontend"
	@echo "table         Initialize DB tables"
	@echo "test          Run backend + agents tests"
	@echo "test-bk       Run backend pytest suite"
	@echo "test-agents   Run agents pytest suite"
	@echo "test-fr       Run frontend tests (requires jest setup)"
	@echo "lint          Run frontend lint"