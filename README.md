# flo-flo
florida man RAG


### Project Structure
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
