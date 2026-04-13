BASE_URL ?= http://localhost:8000
COUNT ?= 1
POLL_INTERVAL ?= 1
MAX_WAIT ?= 60
CONFIRM_OPENAI ?= 0

PYTHON := $(shell command -v python3 2>/dev/null || command -v python)

.PHONY: check-venv init bk fr table test ts-bk ts-ag ts-fr ts-man \
	migrate migrate-new migrate-down migrate-current lint help

check-venv:
	@if [ -z "$(PYTHON)" ]; then \
		echo "ERROR: python3/python not found in PATH"; \
		exit 1; \
	fi

init: check-venv
	@echo "Installing backend dependencies..."
	$(PYTHON) -m pip install -r backend/requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install
	@echo "Done."

bk: check-venv
	cd backend && $(PYTHON) -m uvicorn app.main:app --reload --port 8000

fr:
	cd frontend && npm run dev

# Backward-compatible alias (old target name)
table: migrate

.PHONY: help test-safe test-full canary-scrape canary-generate ts-openai

test-safe: ts-bk ts-ag ts-fr
test-full: ts-bk ts-ag ts-fr ts-man
test: test-safe

canary-scrape: check-venv
	BASE_URL="$(BASE_URL)" COUNT="$(COUNT)" POLL_INTERVAL="$(POLL_INTERVAL)" MAX_WAIT="$(MAX_WAIT)" bash scripts/canary_admin_job.sh scrape

canary-generate: check-venv
	CONFIRM_OPENAI="$(CONFIRM_OPENAI)" BASE_URL="$(BASE_URL)" COUNT="$(COUNT)" POLL_INTERVAL="$(POLL_INTERVAL)" MAX_WAIT="$(MAX_WAIT)" bash scripts/canary_admin_job.sh generate

ts-bk: check-venv
	cd backend && $(PYTHON) -m pytest -vv -s -ra -m "not external and not openai" tests

ts-ag: check-venv
	cd agents && $(PYTHON) -m pytest -vv -s -ra -m "not external and not openai" tests

ts-fr:
	cd frontend && npm test -- --verbose

ts-man: check-venv
	$(PYTHON) -m pytest -vv -s -ra -m external agents/tests/test_scraper_agent.py

ts-openai: check-venv
	@if [ -z "$$OPENAI_API_KEY" ]; then echo "OPENAI_API_KEY is required"; exit 1; fi
	cd agents && $(PYTHON) -m pytest -vv -s -ra -m openai tests

lint:
	cd frontend && npm run lint

migrate: check-venv
	cd backend && $(PYTHON) -m alembic upgrade head

migrate-new: check-venv
	@if [ -z "$(m)" ]; then \
		echo 'Usage: make migrate-new m="your migration message"'; \
		exit 1; \
	fi
	cd backend && $(PYTHON) -m alembic revision --autogenerate -m "$(m)"

migrate-down: check-venv
	cd backend && $(PYTHON) -m alembic downgrade -1

migrate-current: check-venv
	cd backend && $(PYTHON) -m alembic current

help:
	@echo "test-safe        offline default"
	@echo "test-full        includes external/manual"
	@echo "canary-scrape    zero-token admin scrape canary"
	@echo "canary-generate  count=1 default, requires CONFIRM_OPENAI=1"
	@echo "ts-openai        explicit OpenAI integration tests"