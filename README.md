# plugo

GhostLock Backend built with FastAPI.

## Getting started
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```
3. Visit `http://localhost:8000` to verify the health endpoint or use the interactive docs at `/docs`.

## Environment configuration
- `APP_SECRET_KEY` (optional): secret used to sign JWT access tokens. Defaults to a development key.
- `APP_ALLOW_ORIGINS` (optional): comma-separated list of origins allowed by CORS (e.g., `http://localhost:3000,https://app.example.com`). Defaults to `*`.

## Authentication flow
1. Register a user via `POST /auth/register` with a JSON body:
   ```json
   { "username": "alice", "password": "supersecret" }
   ```
2. Obtain a token via `POST /auth/login` using the same credentials. The response contains `access_token`.
3. Send the bearer token in the `Authorization` header (`Bearer <token>`) to access protected routes.

## Available endpoints
- `GET /` – Health check returning the backend status message.
- `POST /auth/register` – Create a user with hashed password storage.
- `POST /auth/login` – Authenticate and receive a signed JWT token.
- `GET /auth/me` – Retrieve the authenticated user's profile.
- `GET /apikeys/` – List API keys for the authenticated user.
- `POST /apikeys/` – Create a new API key.
- `GET /apikeys/{key_id}` – Retrieve a specific API key owned by the user.
- `PATCH /apikeys/{key_id}` – Update an API key's name, description, or active status.
- `DELETE /apikeys/{key_id}` – Delete an existing API key.

## Notes
- This backend uses in-memory storage for demonstration. Replace `app.storage` with a persistent database for production use.
- Tokens are signed with HS256; set a strong `APP_SECRET_KEY` before deployment.
