PYTHON := $(shell command -v python3 2> /dev/null || echo python)

.PHONY: init run-backend run-frontend test help check-venv check-debug check-secrets pre-deploy table

# Initialize development environment
init: check-venv
	@echo "Initializing development environment..."
	$(PYTHON) -m pip install -r requirements.txt
	cd frontend && npm install
	@echo "🛠️  Dependencies installed."

# Run Django backend
back: check-venv
	cd backend && uvicorn app.main:app --reload --port 8000

# Run React frontend
front: check-venv
	cd frontend && npm run dev

# Run this to create the new table
table: check-venv
	@echo "Creating database tables..."
	cd backend && $(PYTHON) -c "from app.db.database import init_db; init_db()"
	@echo "✅ Tables created successfully!"

# Run tests
test: check-venv
	$(PYTHON) manage.py test
	cd frontend && npm run lint

# Check if we're in a virtual environment
check-venv:
	@if [ -z "$$VIRTUAL_ENV" ]; then \
	echo "❌ ERROR: Not in a virtual environment!"; \
	echo "Please activate your venv first: source venv/bin/activate"; \
	exit 1; \
	fi
	@echo "^_^ Virtual environment active"

# Check DEBUG setting
check-debug:
	@echo "Checking DEBUG setting..."
	@if grep -q "DEBUG=True" .env 2>/dev/null; then \
		echo "❌ ERROR: DEBUG=True found in .env - not safe for production!"; \
		exit 1; \
	fi
	@echo "^_^ DEBUG is False - safe for production"

# Check for sensitive files
check-secrets:
	@echo "Checking for sensitive files..."
	@if [ -f ".env" ]; then \
		echo "❌ WARNING: .env file exists - ensure it's in .gitignore"; \
	fi
	@if git ls-files | grep -q "\.env$$"; then \
		echo "❌ ERROR: .env file is tracked by git!"; \
		exit 1; \
	fi
	@if git ls-files | grep -q "db\.sqlite3$$"; then \
		echo "❌ ERROR: Database file is tracked by git!"; \
		exit 1; \
	fi
	@if grep -r "SECRET_KEY.*=" . --include="*.py" --exclude-dir=venv | grep -v "env("; then \
		echo "❌ ERROR: Hardcoded SECRET_KEY found in Python files!"; \
		exit 1; \
	fi
	@echo "^_^ No sensitive files detected in git"

# Pre-deployment checks
pre-deploy: check-venv check-debug check-secrets
	@echo "Running pre-deployment checks..."
	$(PYTHON) manage.py check --deploy
	$(PYTHON) manage.py collectstatic --noinput --dry-run
	cd frontend && npm run build
	@echo "✅ All checks passed - ready for deployment! ✅"

# Show available commands
help:
	@echo "Available commands:"
	@echo "	init         	- Initialize development environment"
	@echo "	back			- Run Django backend server"
	@echo "	front     		- Run React frontend server"
	@echo "	table        	- Create database tables"
	@echo "	test         	- Run tests for backend and frontend"
	@echo "	check-venv   	- Verify virtual environment is active"
	@echo "	check-debug  	- Ensure DEBUG=False for production"
	@echo "	check-secrets	- Check for exposed sensitive files"
	@echo "	pre-deploy   	- Run all deployment safety checks"
	@echo "	help         	- Show this help message"