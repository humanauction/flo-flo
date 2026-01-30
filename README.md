# Florida Man or Fiction

A true/false game where players guess if a headline is a real "Florida Man" story or AI-generated fiction.

## Introduction

This project combines web scraping, multi-agent AI systems, and a slick frontend to create an entertaining game based on the internet's favorite meme: Florida Man headlines.

**Concept:**

- **Frontend:** Simple true/false game interface
- **Backend:** Multi-agent system that scrapes real Florida Man headlines and generates convincing fakes
- **Gameplay:** Players decide if each headline is real or AI-generated

## Tech Stack

### Frontend

- **Next.js 16** (React, TypeScript, App Router)
- **Tailwind CSS** for styling
- **Turbopack** for fast dev builds

### Backend

- **Python 3.11+**
- **FastAPI** for REST API
- **PostgreSQL** for headline storage
- **Docker Compose** for local development

### AI Agents

- **AutoGen** (Microsoft) for multi-agent orchestration
- **LangChain** or **LlamaIndex** for RAG
- **Vector DB:** Chroma, Weaviate, or PGVector

### Scraping

- **Requests + BeautifulSoup** or **Playwright**
- Target: <https://floridaman.com> and news outlets

## Project Structure

```text
flo-flo/
├── frontend/                    # Next.js app
│   ├── src/
│   │   ├── app/                 # App Router (Next.js 13+)
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx         # Main game page
│   │   │   └── api/             # API routes (optional proxy)
│   │   ├── components/
│   │   │   ├── GameCard.tsx     # Headline display + T/F buttons
│   │   │   ├── ScoreBoard.tsx
│   │   │   └── Header.tsx
│   │   ├── hooks/
│   │   │   └── useGame.ts       # Game logic hook
│   │   ├── lib/
│   │   │   └── api.ts           # Backend API client
│   │   └── types/
│   │       └── index.ts         # TypeScript types
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   └── tailwind.config.js
│
├── backend/                     # Python FastAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Environment config
│   │   ├── models/              # Pydantic + SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   └── headline.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── game.py          # Game endpoints
│   │   │   └── admin.py         # Scrape triggers, stats
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── headline_service.py
│   │   └── db/
│   │       ├── __init__.py
│   │       ├── database.py      # DB connection
│   │       └── repositories.py  # DB queries
│   ├── requirements.txt
│   └── .env.example
│
├── agents/                      # AutoGen multi-agent system
│   ├── __init__.py
│   ├── config.py
│   ├── scraper_agent.py         # Agent 1: Web scraping
│   ├── generator_agent.py       # Agent 2: Fake headline gen
│   ├── orchestrator.py          # Agent coordination
│   └── tools/
│       ├── __init__.py
│       ├── scraper.py           # BeautifulSoup/Playwright logic
│       └── vector_store.py      # RAG integration
│
├── docker-compose.yml           # PostgreSQL + optional services
├── .gitignore
└── README.md
```

## Development Roadmap

### Phase 1: Foundation

- [x] **Project structure + Next.js install**
- [ ] Backend scaffold (FastAPI + PostgreSQL via Docker)
- [ ] Database models (headlines table)

### Phase 2: AI Agents

- [ ] AutoGen agent setup (awaiting version confirmation)
- [ ] Scraper agent (Agent 1: Collect real Florida Man headlines)
- [ ] Generator agent (Agent 2: Create fake headlines using RAG)

### Phase 3: Integration

- [ ] Wire frontend to backend API
- [ ] Game logic & scoring system
- [ ] Admin panel for triggering scrapes

### Phase 4: Polish & Launch

- [ ] UI/UX refinements
- [ ] Error handling & edge cases
- [ ] Deploy (Vercel frontend + Railway/Fly.io backend)

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Docker Desktop (for PostgreSQL)
- OpenAI API key (for AutoGen)

### Installation

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**Backend (coming soon):**

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Database:**

```bash
docker-compose up -d
```

## Environment Variables

Create `.env` files in both `backend/` and `agents/` directories:

```env
# Backend
DATABASE_URL=postgresql://user:pass@localhost:5432/floridaman
OPENAI_API_KEY=your_key_here

# Agents
AUTOGEN_MODEL=gpt-4
VECTOR_DB_PATH=./data/chroma
```

## Contributing

This is a learning project. Feel free to fork and experiment.

## License

MIT (because Florida Man belongs to everyone)

---

**Status:** 🚧 In active development  
**Current Phase:** Backend scaffold (Step 2/8)
