# Florida Man or Fiction

[![Integration Tests (Manual)](https://github.com/humanauction/flo-flo/actions/workflows/integration-tests.manual.yml/badge.svg)](https://github.com/humanauction/flo-flo/actions/workflows/integration-tests.manual.yml)
[![Python Tests (Offline)](https://github.com/humanauction/flo-flo/actions/workflows/python-tests.ci.yml/badge.svg)](https://github.com/humanauction/flo-flo/actions/workflows/python-tests.ci.yml)
[![Frontend Tests](https://github.com/humanauction/flo-flo/actions/workflows/frontend-tests.ci.yml/badge.svg)](https://github.com/humanauction/flo-flo/actions/workflows/frontend-tests.ci.yml)

A true/false game where players guess whether a headline is a real Florida Man story or AI-generated fiction.

## Introduction

This project combines web scraping, multi-agent AI behavior, and a Next.js frontend into a playable Florida Man or Fiction game.

Core loop:

- Frontend presents a headline card.
- Backend serves real and fake headlines.
- Player guesses real vs fake.
- Admin/agent workflows keep the headline pool fresh.

## Current Status Snapshot

- Phase 1 and Phase 2 are complete.
- Phase 3.3 has conservative source adapter/metrics support in scraper tooling.
- Phase 3.4 In Progress with OpenAI-native generation hardening.
- CI split is stable.
- Offline tests run automatically.
- External/OpenAI paths are isolated to manual/scheduled integration workflow.

## Tech Stack

### Frontend

- Next.js 16 (App Router, TypeScript)
- Tailwind CSS
- Jest

### Backend

- Python 3.13+
- FastAPI
- SQLAlchemy
- Alembic
- SQLite for dev (PostgreSQL planned for production)

### Agents

- AutoGen 0.4+
- OpenAI GPT-4o-mini
- Requests + BeautifulSoup for scraping

## Project Structure

Notes:

- This README intentionally keeps both current implemented layout and planned/continuity paths.
- Some continuity entries are intentionally listed even if not currently present to support roadmap tracking across sessions.

### Current Implemented Layout (Source Of Truth)

```text
flo-flo/
├── .github/
│ └── workflows/
│ ├── python-tests.ci.yml
│ ├── frontend-tests.ci.yml
│ └── integration-tests.manual.yml
├── backend/
│ ├── pyproject.toml
│ ├── app/
│ │ ├── main.py
│ │ ├── config.py
│ │ ├── db/
│ │ │ ├── database.py
│ │ │ └── repositories/
│ │ │ ├── headline_repository.py
│ │ │ └── token_usage_repository.py
│ │ ├── models/
│ │ │ ├── headline.py
│ │ │ └── token_usage.py
│ │ ├── routers/
│ │ │ ├── game.py
│ │ │ └── admin.py
│ │ └── services/
│ │ └── headline_service.py
│ ├── migrations/
│ │ ├── env.py
│ │ └── versions/
│ ├── tests/
│ │ ├── conftest.py
│ │ ├── test_db/
│ │ ├── test_routers/
│ │ └── test_services/
│ ├── alembic.ini
│ ├── requirements.txt
│ └── seed_data.py
├── agents/
│ ├── pyproject.toml
│ ├── pytest.ini
│ ├── src/
│ │ └── agents/
│ │ ├── __init__.py
│ │ ├── config.py
│ │ ├── scraper_agent.py
│ │ ├── generator_agent.py
│ │ ├── orchestrator.py
│ │ └── tools/
│ │ ├── __init__.py
│ │ ├── scraper.py
│ │ ├── database.py
│ │ └── generator_quality.py
│ ├── tools/ # compatibility namespace retained
│ └── tests/
│ ├── test_scraper_agent.py
│ ├── test_generator_agent.py
│ └── test_tools/
│ ├── test_tool_scraper.py
│ ├── test_tool_database.py
│ └── test_tool_generator_quality.py
├── frontend/
│ ├── src/
│ │ ├── app/
│ │ │ ├── page.tsx
│ │ │ └── admin/
│ │ │ └── page.tsx
│ │ ├── components/
│ │ ├── lib/
│ │ │ └── api.ts
│ │ └── types/
│ │ └── index.ts
│ ├── tests/
│ │ ├── components/
│ │ └── lib/
│ │ └── api.test.ts
│ └── package.json
├── tests/
│ ├── test_api_integration.py
│ └── test_e2e_headline_flow.py
├── env.py
├── makefile
├── .gitignore
└── README.md
```

### Planned/Continuity Paths (Intentionally Retained)

```text
agents/
├── config.py                    # planned compatibility shim
├── scraper_agent.py             # planned compatibility shim
├── generator_agent.py           # planned compatibility shim
├── orchestrator.py              # planned compatibility shim
└── tools/
    ├── scraper.py               # planned compatibility shim
    └── database.py              # planned compatibility shim

frontend/__tests__/components/
├── Game.test.tsx                # planned
└── GameCard.test.tsx            # planned

frontend/__tests__/lib/
└── api.test.ts                  # implemented/planned expansion
```

## Development Roadmap

### Phase 1: Foundation ✅

- [x] Project structure + Next.js install
- [x] Backend scaffold (FastAPI + SQLite)
- [x] Database models (headlines table)
- [x] Seed data with test headlines
- [x] Frontend game UI (working end-to-end)

### Phase 2: AI Agents ✅

- [x] AutoGen 0.4+ agent setup
- [x] Scraper agent (collect real headlines)
- [x] Generator agent (create fake headlines)
- [x] Database integration tools
- [x] Orchestrator for agent coordination

### Phase 3: Agent Enhancement 🚧 (Current)

Goal: robust offline-first behavior, explicit external/openai test gates, stronger quality controls.

#### 3.1 Fix Agent Execution

- [x] Debug why agents terminate without running tools
- [x] Add baseline tool-level tests for scraper/database paths
- [x] Verify database writes from agent tools (offline)
- [x] Add stronger tool schemas for AutoGen
- [x] Add richer generator assertions for real OpenAI path

#### 3.2 Testing Strategy (Implemented)

- [x] Offline tests default (`not external and not openai`)
- [x] External scraping tests marked `@pytest.mark.external`
- [x] OpenAI integration tests marked `@pytest.mark.openai`
- [x] Manual/scheduled integration workflow with secret guard

#### 3.3 Improve Scraping (In Progress)

- [ ] Add additional real news source adapters beyond current conservative setup
- [x] Retry/backoff and timeout strategy
- [x] Stronger validation and dedupe metrics (`scrape_with_metrics`)

#### 3.4 Enhance Generation (Core Implemented)

- [x] Connect generation path to OpenAI outputs (with deterministic fallback)
- [x] Baseline quality checks (length, phrase plausibility, duplicate filtering)

#### 3.5 Admin Interface (Implemented)

- [x] Add endpoints to trigger scrape/generate jobs from API
- [x] Add frontend admin page to run jobs and show status/logs
- [x] Add admin job status endpoint and polling contract

#### 3.6 Context Augmentation (Planned After 3.3, Before Phase 4)

- [ ] RAG context from real headlines
- [ ] RAG grounding metadata for generated headline provenance

### Phase 4: Polish & Production

- [ ] Accounts/Stats
- [ ] Leaderboard
- [ ] Social sharing
- [ ] UX loading/error polish
- [ ] Mobile polish
- [ ] Production deploy (frontend/backend)
- [ ] PostgreSQL production setup
- [ ] Env/config hardening

### Phase 5: Advanced Features (Future)

- [ ] Vector DB/RAG
- [ ] Multi-model support
- [ ] Difficulty levels
- [ ] Daily challenge mode
- [ ] Rate limiting
- [ ] Caching layer

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.13+

### Installation (Recommended, Repository Root)

```bash
git clone https://github.com/humanauction/flo-flo.git
cd flo-flo

python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip

# Install both packages editable
python -m pip install -e backend -e agents

# Test tooling
python -m pip install pytest pytest-asyncio pytest-cov
```

### Environment

Create `backend/.env`:

```env
DATABASE_URL=sqlite:///./floridaman.db
OPENAI_API_KEY=your_key_here
```

Optional agent knobs (if used in your local flow):

```env
OPENAI_MODEL=gpt-4o-mini
MAX_HEADLINES_PER_SCRAPE=10
TARGET_URL=https://floridaman.com/
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Database + App Boot

```bash
cd backend
python -m alembic upgrade head
python seed_data.py
uvicorn app.main:app --reload --port 8000
```

```bash
# in another terminal
cd frontend
npm install
npm run dev
```

### Run Agents

```bash
# from repo root, with editable installs active
python -m agents.orchestrator
```

## Migration-First Workflow

Use Alembic as the only schema change path.

```bash
cd backend
python -m alembic revision --autogenerate -m "describe schema change"
python -m alembic upgrade head
python seed_data.py
```

Do not use runtime `Base.metadata.create_all()` for schema management.

## API Endpoints

### Game

- `GET /api/game/headline`
- `POST /api/game/guess`

### Admin

- `GET /api/admin/stats`
- `POST /api/admin/headline` (manual insert)
- `POST /api/admin/scrape` (queues scrape job, optional count 1-50, default 10)
- `POST /api/admin/generate` (queues generate job, optional count 1-50, default 10)
- `GET /api/admin/jobs/{job_id}` (returns queued, running, completed, or failed state with summary or error)

## Testing

### Quick Local Commands

```bash
# backend offline
cd backend
python -m pytest -m "not external and not openai"

# agents offline
cd ../agents
python -m pytest -m "not external and not openai"

# focused scraper/generator tool tests
python -m pytest -q tests/test_tools/test_tool_scraper.py
python -m pytest -q tests/test_tools/test_tool_generator_quality.py
```

### Root Integration Scaffolds

- `tests/test_api_integration.py`
- `tests/test_e2e_headline_flow.py`

## CI Workflows

### Python Tests (Offline)

- File: `.github/workflows/python-tests.ci.yml`
- Trigger: backend/agents push or pull request
- Runs offline-only backend and agents suites

### Frontend Tests

- File: `.github/workflows/frontend-tests.ci.yml`
- Trigger: frontend push or pull request
- Runs npm test with coverage

### Integration Tests (Manual)

- File: `.github/workflows/integration-tests.manual.yml`
- Trigger: manual + weekly schedule
- Suites: `external`, `openai`, `all`
- OpenAI path runs only when `OPENAI_API_KEY` is present

## Contributing

Learning project, open to iteration. Keep changes small, tested, and roadmap-aligned.

## License

MIT

---

**Status:** 🚧 Phase 3 (3.3 source expansion in progress; 3.4 and 3.5 baseline implemented)
**Last Updated:** April 9, 2026
**Next Milestone:** 3.3 additional source adapters, then 3.6 Optional RAG context (April 2026)
