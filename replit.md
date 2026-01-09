# GhostLock

## Overview
GhostLock is a full-stack OSINT/threat intelligence platform for managing cases, entities, and relationships. It includes JWT-based authentication, API key management, external service transforms (AbuseIPDB, URLScan), interactive graph visualization, and a modern dark-themed frontend.

## Project Structure
```
app/
├── __init__.py
├── config.py          # Application settings (env vars, CORS)
├── dependencies.py    # FastAPI dependencies
├── main.py           # FastAPI app entrypoint (serves frontend + API)
├── schemas.py        # Pydantic models
├── security.py       # Password hashing (bcrypt) & JWT handling
├── storage.py        # PostgreSQL data storage
├── routes/
│   ├── apikeys.py    # API key management endpoints
│   ├── auth.py       # Authentication (register/login)
│   ├── cases.py      # Case management
│   ├── entities.py   # Entity management
│   ├── relationships.py  # Relationship management
│   └── transforms.py # Transform execution endpoint
└── transforms/
    ├── dispatcher.py # Routes transforms by entity kind
    ├── ip.py         # AbuseIPDB IP analysis
    ├── domain.py     # URLScan domain analysis
    ├── url.py        # URL analysis (placeholder)
    └── keys.py       # API key retrieval helper

static/
├── index.html        # Frontend HTML (includes vis-network for graphs)
├── style.css         # Dark theme styling
└── app.js           # Frontend JavaScript (API integration, graph rendering)
```

## Running the Application
The server runs on port 5000 using uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

## Environment Variables
- `APP_SECRET_KEY`: Secret for signing JWT tokens (default: dev-secret-key)
- `APP_ALLOW_ORIGINS`: Comma-separated CORS origins (default: *)

## API Endpoints
- `GET /` - Serves the frontend
- `GET /health` - Health check
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user profile
- `/apikeys/*` - API key CRUD operations
- `/cases/*` - Case management
- `/entities/*` - Entity management
- `/relationships/*` - Relationship management
- `POST /entities/{id}/transforms/run` - Run transforms on an entity

## Transforms
Transforms analyze entities using external APIs and create new related entities:

### IP Transform (AbuseIPDB)
- Requires: `ABUSEIPDB_API_KEY` in API Keys vault
- Creates: Threat entity with abuse score, country, ISP

### Domain Transform (URLScan)
- Requires: `URLSCAN_API_KEY` in API Keys vault
- Creates: Screenshot entity, IP entities the domain resolves to
- Note: Takes ~60 seconds due to URLScan processing time

## Graph Visualization
- Interactive network graph using vis-network library
- Nodes colored by entity type (IP=green, Domain=blue, Threat=red, etc.)
- Filter by case to focus on specific investigations
- Edges show relationship types between entities

## Database
The application uses PostgreSQL for persistent storage. The database is automatically configured via the `DATABASE_URL` environment variable.

## Notes
- Data persists across restarts via PostgreSQL
- Tokens signed with HS256 algorithm
- API keys stored in vault with description field containing actual key value
