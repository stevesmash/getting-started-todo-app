# GhostLock Backend

## Overview
GhostLock Backend is a FastAPI-based REST API for managing cases, entities, and relationships. It includes JWT-based authentication and API key management.

## Project Structure
```
app/
├── __init__.py
├── config.py          # Application settings (env vars, CORS)
├── dependencies.py    # FastAPI dependencies
├── main.py           # FastAPI app entrypoint
├── schemas.py        # Pydantic models
├── security.py       # JWT token handling
├── storage.py        # In-memory data storage
└── routes/
    ├── apikeys.py    # API key management endpoints
    ├── auth.py       # Authentication (register/login)
    ├── cases.py      # Case management
    ├── entities.py   # Entity management
    └── relationships.py  # Relationship management
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
- `GET /` - Health check
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user profile
- `/apikeys/*` - API key CRUD operations
- `/cases/*` - Case management
- `/entities/*` - Entity management
- `/relationships/*` - Relationship management

## Database
The application uses PostgreSQL for persistent storage. The database is automatically configured via the `DATABASE_URL` environment variable.

## Notes
- Data persists across restarts via PostgreSQL
- Tokens signed with HS256 algorithm
