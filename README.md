# MTG Builder

A web application for building, managing, and playtesting Magic: The Gathering decks. Features a full card database powered by Scryfall, deck construction tools, and real-time multiplayer gameplay via WebSockets.

## Architecture

```
mtg-builder/
├── frontend/          Svelte 5 + Vite SPA
├── backend/           FastAPI (Python 3.13) REST + WebSocket API
├── scripts/           Rust CLI for bulk Scryfall card import
└── docker-compose.yml PostgreSQL + all services
```

### Frontend

Svelte 5 single-page application built with Vite and TypeScript. Client-side routing with a resizable sidebar layout.

**Pages:** Home, Deck List, Deck Builder, Card Explorer, Training (solo playtesting), Play (multiplayer lobbies), Login/Register

### Backend

FastAPI application using an MVC pattern:

- **Models** — SQLAlchemy async ORM (asyncpg driver)
- **Views** — Pydantic request/response schemas
- **Controllers** — Business logic
- **Routers** — Thin route handlers

**API endpoints** (all under `/api/v1`):

| Group | Endpoints |
|-------|-----------|
| Auth | `POST /auth/register`, `POST /auth/login`, `GET /auth/me` |
| Decks | `GET /decks`, `POST /decks`, `GET /decks/{id}`, `PUT /decks/{id}`, `DELETE /decks/{id}` |
| Cards | `GET /search`, `GET /cards/{id}/printings`, `GET /name` |
| Game | `GET /games`, `WS /ws/game?token=<jwt>` |

Authentication uses JWT bearer tokens. Multiplayer games use WebSocket connections for real-time state sync.

### Scripts (Scryfall Importer)

Rust binary that downloads the full Scryfall bulk data (~80k+ cards) and upserts them into PostgreSQL. Handles double-faced cards, split cards, and adventure cards by falling back to `card_faces[0]` data. Stores complete Scryfall JSON in a `raw_json` column alongside 63+ dedicated columns.

### Database

PostgreSQL with four tables:

- **cards** — Full Scryfall card catalog (managed by the Rust importer)
- **users** — Accounts with bcrypt password hashes
- **decks** — User decks with format and description
- **deck_cards** — Junction table with quantity, zone (mainboard/sideboard/etc.), commander flag, and cached card data as JSONB

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose

### Run with Docker

```bash
# Start PostgreSQL, backend, and frontend
docker compose up --build

# Import the Scryfall card database (run once, takes a few minutes)
docker compose run --rm scripts
```

The app will be available at:

- **Frontend:** http://localhost:1420
- **API:** http://localhost:8000/api/v1
- **API docs:** http://localhost:8000/docs

### Environment Variables

Set these in a `.env` file at the project root or export them before running:

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_PASSWORD` | `123` | PostgreSQL password |
| `JWT_SECRET_KEY` | `change-me-in-production` | Secret for signing JWT tokens |

### Local Development (without Docker)

**Requirements:** Python 3.13+, Node.js 22+, Rust 1.85+, PostgreSQL 17

```bash
# Backend
cd backend
cp .env.example .env          # edit DATABASE_URL and JWT_SECRET_KEY
uv sync
uv run python migrations/run_migrations.py
uv run uvicorn main:app --host 127.0.0.1 --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev                   # http://localhost:1420

# Import cards (separate terminal)
cd scripts
cp ../backend/.env .env       # reuse the same DATABASE_URL
cargo run --release
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Svelte 5, TypeScript, Vite 7 |
| Backend | FastAPI, SQLAlchemy, asyncpg, Pydantic |
| Database | PostgreSQL 17 |
| Data Import | Rust, sqlx, reqwest |
| Auth | JWT (python-jose), bcrypt |
| Deployment | Docker Compose |
