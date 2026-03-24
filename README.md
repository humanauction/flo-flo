# Florida Man or Fiction

A true/false game where players guess if a headline is a real "Florida Man" story or AI-generated fiction.

## Introduction

This project combines web scraping, multi-agent AI systems, and a frontend to create a game based on the internet meme: Florida Man.

**Concept:**

- **Frontend:** Simple true/false game interface
- **Backend:** Multi-agent system that scrapes real Florida Man headlines and generates convincing fakes
- **Gameplay:** Players decide if each headline is real or AI-generated

## Tech Stack

### Frontend

- **Next.js 15** (React, TypeScript, App Router)
- **Tailwind CSS** for styling
- **Turbopack** for fast dev builds

### Backend

- **Python 3.13+**
- **FastAPI** for REST API
- **SQLite** for headline storage (dev) / PostgreSQL (prod)
- **Docker Compose** for local development (optional)

### AI Agents

- **AutoGen 0.4+** (Microsoft) for multi-agent orchestration
- **OpenAI GPT-4o-mini** for fake headline generation
- **Vector DB (future):** Chroma or PGVector for RAG

### Scraping

- **Requests + BeautifulSoup4** for headline scraping
- **Playwright** (optional) for JS-heavy sites
- Target: <https://floridaman.com> and news outlets

## Project Structure

```text
flo-flo/
├── frontend/                    # Next.js app
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx       # Root layout
│   │   │   ├── page.tsx         # Main game page
│   │   │   └── globals.css
│   │   ├── components/
│   │   │   ├── Game.tsx         # Main game component
│   │   │   ├── GameCard.tsx     # Headline display + buttons
│   │   │   ├── ScoreBoard.tsx   # Stats display
│   │   │   ├── Header.tsx       # Title/branding
│   │   │   └── ResultModal.tsx  # Feedback after guess
│   │   ├── lib/
│   │   │   └── api.ts           # Backend API client
│   │   └── types/
│   │       └── index.ts         # TypeScript types
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.ts
│   └── tailwind.config.ts
│
├── backend/                     # Python FastAPI
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Environment config
│   │   ├── models/
│   │   │   └── headline.py      # SQLAlchemy model
│   │   ├── routers/
│   │   │   ├── game.py          # Game endpoints
│   │   │   └── admin.py         # Admin/stats endpoints
│   │   ├── services/
│   │   │   └── headline_service.py
│   │   └── db/
│   │       ├── database.py      # DB connection
│   │       └── headline_repository.py  # DB queries
│   ├── seed_data.py             # Test data seeder
│   ├── requirements.txt
│   └── .env
│
├── agents/                      # AutoGen multi-agent system
│   ├── config.py                # Agent configuration
│   ├── scraper_agent.py         # Agent 1: Web scraping
│   ├── generator_agent.py       # Agent 2: Fake headline gen
│   ├── orchestrator.py          # Agent coordination
│   └── tools/
│       ├── scraper.py           # BeautifulSoup scraping logic
│       └── database.py          # DB save/retrieve tools
│
├── .gitignore
└── README.md
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
- [x] Scraper agent (Agent 1: Collect real Florida Man headlines)
- [x] Generator agent (Agent 2: Create fake headlines)
- [x] Database integration tools
- [x] Orchestrator for agent coordination

### Phase 3: Agent Enhancement 🚧 (Current)

**Goal:** Make agents actually work and improve headline quality

#### 3.1 Fix Agent Execution

- [ ] Debug why agents terminate without running tools
- [ ] Add proper tool schemas for AutoGen
- [ ] Test scraper agent fetches real headlines
- [ ] Test generator agent creates convincing fakes
- [ ] Verify database writes work from agents

#### 3.2 Improve Scraping

- [ ] Add multiple news sources (not just floridaman.com)
- [ ] Implement retry logic for failed scrapes
- [ ] Add headline validation (length, format, keywords)
- [ ] Filter duplicate headlines
- [ ] Log scraping metrics

#### 3.3 Enhance Generation

- [ ] Connect generator to OpenAI API (currently using templates)
- [ ] Implement RAG: feed real headlines as context
- [ ] Add temperature/creativity controls
- [ ] Validate fake headlines don't duplicate real ones
- [ ] Generate batch headlines for efficiency

#### 3.4 Admin Interface

- [ ] Add backend endpoint to trigger scrape (`POST /api/admin/scrape`)
- [ ] Add backend endpoint to trigger generation (`POST /api/admin/generate`)
- [ ] Create simple admin page in frontend
- [ ] Display agent run logs/status
- [ ] Show headline distribution stats (real vs fake)

### Phase 4: Polish & Production

- [ ] Add user accounts (optional: track personal stats)
- [ ] Leaderboard system
- [ ] Share results to social media
- [ ] Error handling & loading states
- [ ] Mobile responsiveness improvements
- [ ] Deploy frontend (Vercel)
- [ ] Deploy backend (Railway/Fly.io)
- [ ] Set up PostgreSQL in production
- [ ] Environment variable management
- [ ] CI/CD pipeline

### Phase 5: Advanced Features (Future)

- [ ] Vector DB for RAG (Chroma/PGVector)
- [ ] Multi-model support (Claude, Gemini)
- [ ] Difficulty levels (easy/hard headlines)
- [ ] Daily challenge mode
- [ ] API rate limiting
- [ ] Caching layer (Redis)

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- OpenAI API key (for AutoGen generator)

### Installation

**1. Clone the repo:**

```bash
git clone https://github.com/humanauction/flo-flo.git
cd flo-flo
```

**2. Set up backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**3. Configure environment:**

Create `backend/.env`:

```env
DATABASE_URL=sqlite:///./headlines.db
OPENAI_API_KEY=your_key_here
```

Create `agents/.env`:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

**4. Seed database:**

```bash
cd backend
python seed_data.py
```

**5. Start backend:**

```bash
uvicorn app.main:app --reload --port 8000
```

**6. Set up frontend (new terminal):**

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**7. Start frontend:**

```bash
npm run dev
```

**8. Play the game:**

Visit <http://localhost:3000>

**9. Run agents (optional):**

```bash
# From project root
python -m agents.orchestrator
```

## Environment Variables

### Backend (`backend/.env`)

```env
DATABASE_URL=sqlite:///./headlines.db
OPENAI_API_KEY=sk-...
```

### Agents (`agents/.env` or use backend)

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
MAX_HEADLINES_PER_SCRAPE=10
TARGET_URL=https://floridaman.com/
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API Endpoints

### Game Endpoints

- `GET /api/game/headline` - Get random headline for guessing
- `POST /api/game/guess` - Submit guess and get result

### Admin Endpoints

- `GET /api/admin/stats` - Get database statistics
- `POST /api/admin/scrape` - Trigger headline scraping (coming soon)
- `POST /api/admin/generate` - Trigger fake headline generation (coming soon)

## Testing

```text
flo-flo/
├── frontend/
│   ├── src/
│   ├── __tests__/              # Frontend unit tests
│   │   ├── components/
│   │   │   ├── Game.test.tsx
│   │   │   └── GameCard.test.tsx
│   │   └── lib/
│   │       └── api.test.ts
│   ├── jest.config.js
│   └── package.json            # npm test
│
├── backend/
│   ├── app/
│   ├── tests/                  # Backend unit + integration tests
│   │   ├── __init__.py
│   │   ├── conftest.py         # pytest fixtures
│   │   ├── test_routers/
│   │   │   ├── test_game.py
│   │   │   └── test_admin.py
│   │   ├── test_services/
│   │   │   └── test_headline_service.py
│   │   └── test_db/
│   │       └── test_repositories.py
│   ├── pytest.ini
│   └── requirements-dev.txt    # pytest, pytest-asyncio, etc.
│
├── agents/
│   ├── tools/
│   ├── tests/                  # Agent-specific tests
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_scraper_agent.py
│   │   ├── test_generator_agent.py
│   │   ├── test_tools/
│   │   │   ├── test_scraper.py
│   │   │   └── test_database.py
│   │   └── test_orchestrator_mock.py
│   └── pytest.ini
│
├── tests/                      # End-to-end/integration tests (optional)
│   ├── __init__.py
│   ├── test_e2e_headline_flow.py    # Full pipeline: scrape → DB → API → frontend
│   └── test_api_integration.py       # Backend + Agent coordination
│
├── .github/
│   └── workflows/
│       ├── backend-tests.yml   # Backend CI
│       ├── frontend-tests.yml  # Frontend CI
│       ├── agent-tests.yml     # Agent CI
│       └── e2e-tests.yml       # Integration tests (optional)
│
└── Makefile                    # Convenience commands
```

### Frontend Tests

- `components/Game.test.tsx`
- `components/GameCard.test.tsx`
- `lib/api.test.ts`

### Backend Tests

- `tests/__init__.py`
- `tests/conftest.py`
- `test_routers/test_game.py`
- `test_routers/test_admin.py`
- `test_services/test_headline_service.py`
- `test_db/test_repositories.py`

### Agent Tests

- `tools/__init__.py`
- `tools/conftest.py`
- `test_scraper_agent.py`
- `test_generator_agent.py`
- `test_tools/test_scraper.py`
- `test_tools/test_database.py`
- `test_orchestrator_mock.py`

### End-to-end Tests

- `test_e2e_headline_flow.py`
- `test_api_integration.py`

### CI/CD

- `backend-tests.yml`
- `frontend-tests.yml`
- `agent-tests.yml`
- `e2e-tests.yml`

## Contributing

This is a learning project. Feel free to fork and experiment.

## License

MIT (because Florida Man belongs to everyone)

---

**Status:** 🚧 Phase 3 - Agent Enhancement  
**Last Updated:** Feb 5, 2026  
**Next Milestone:** Fix agent tool execution and wire admin triggers
