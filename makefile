PYTHON := $(shell command -v python3 2>/dev/null || command -v python)

.PHONY: check-venv init bk fr table test test-bk test-agents test-fr test-manual \
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

test: test-bk test-agents

test-bk: check-venv
	cd backend && $(PYTHON) -m pytest -vv -s -ra -m "not external and not openai" tests

test-agents: check-venv
	cd agents && $(PYTHON) -m pytest -vv -s -ra -m "not external and not openai" tests

test-fr:
	cd frontend && npm test -- --verbose

test-manual: check-venv
	$(PYTHON) -m pytest -vv -s -ra -m external agents/tests/test_scraper_agent.py

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