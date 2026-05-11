# Title: ADR RAG‑V1 Embeddings, Budget Guardrails, and Diagnostics

Status: Proposed
Date: 2026‑05‑11

## Context

The project currently injects recent real headlines as context but lacks vector retrieval.
Stage 4 intends to deliver RAG using PostgreSQL + pgvector.
Cost control is required due to limited OpenAI credits.

## Decisions

Embedding provider and model
Provider: OpenAI embeddings.
Model: text-embedding-3-small.
Dimension: 1536.

Storage and retrieval
Store embeddings on real headlines only.
Use pgvector cosine distance for similarity retrieval.
Apply diversity filtering (MMR or source‑bucket dedupe) to reduce near-duplicate context.

Budget guardrails (v1)
Track estimated embedding spend from usage records.
Warnings at approximately $1, $2, $3.
Hard cap at $4: disable embeddings and fall back to recent‑real context.

Fallback policy
If RAG is disabled, DB is not PostgreSQL, budget cap is reached, or embedding fails:
fall back to deterministic recent‑real context.
Admin retrieval diagnostics
Diagnostics are allowed only when explicitly enabled.
Default: disabled in production until admin auth is implemented.
Diagnostics show only retrieval metadata: strategy, top_k, similarity range, source domains.
Never expose raw embeddings or full query text.

Planned v2 extension:
local embeddings
(TBC) local embedding provider (dev-only) to avoid OpenAI spend.
Not part of v1.

### Consequences

Pros: RAG is production‑grade, auditable, and cost‑bounded.
Cons: Requires Postgres for full RAG and embedding calls during ingest/backfill.

### Non‑goals

Hybrid retrieval, re‑ranking beyond simple diversity.
OAuth or admin auth as part of v1.
Local embeddings in v1.

### Acceptance Criteria

Embedding model and dimension are explicitly defined.
Budget warnings and cap are enforced with fallback.
RAG fallback is deterministic.
Diagnostics are gated and do not expose sensitive data.
v2 local embedding option is documented.

### Open Question(s)

Should diagnostics be dev‑only or allow staging with a feature flag?

## Implementation checklist (with touchpoints, task links placeholders)

RAG‑V1‑01 Schema + pgvector
Files: headline.py, headline_repository.py, new migration in backend/migrations/versions
Link: <PROJECT: RAG‑V1‑01>

RAG‑V1‑02 Config + budget guardrails
Files: config.py, README.md
Link: <PROJECT: RAG‑V1‑02>

RAG‑V1‑03 Embedding pipeline + backfill
Files: headline_service.py, headline_repository.py, makefile
Link: <PROJECT: RAG‑V1‑03>

RAG‑V1‑04 Retriever + diversity
Files: headline_repository.py, headline_service.py
Link: <PROJECT: RAG‑V1‑04>

RAG‑V1‑05 Agent integration + provenance
Files: database.py, generator_agent.py, test_generator_agent.py
Link: <PROJECT: RAG‑V1‑05>

RAG‑V1‑06 Usage tracking + budget enforcement
Files: token_usage.py, token_usage_repository.py, headline_service.py
Link: <PROJECT: RAG‑V1‑06>

RAG‑V1‑07 Admin diagnostics (gated)
Files: admin.py, page.tsx, index.ts
Link: <PROJECT: RAG‑V1‑07>

RAG‑V2‑01 Local embedding provider (planned)
Files: config.py, README.md
Link: <PROJECT: RAG‑V2‑01>
