# GhostLock

## Overview
GhostLock is a full-stack OSINT/threat intelligence platform for managing cases, entities, and relationships. It includes JWT-based authentication, API key management, external service transforms, interactive graph visualization, and a modern dark-themed frontend.

## Recent Changes
- Added comprehensive transform suite: IP, Domain, URL, Email, Hash, Phone transforms
- Transform selection modal when multiple transforms are available for an entity type
- Added entity detail page with comprehensive view of entity info, related entities, and comments
- Implemented comments system for adding notes to entities
- Added Dashboard section with live stats cards, entity type breakdown chart, and recent activity feed
- Implemented bulk import feature for entities via CSV/JSON file uploads
- Added export functionality for cases (JSON and CSV formats)
- Added keyboard shortcuts for navigation
- Added activity timeline with chronological logging of all actions
- Enhanced graph visualization with unique node shapes, glowing shadows, curved edges

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
│   ├── comments.py   # Comments on entities
│   ├── entities.py   # Entity management
│   ├── import_export.py  # Bulk import/export endpoints
│   ├── relationships.py  # Relationship management
│   ├── timeline.py   # Activity timeline endpoint
│   └── transforms.py # Transform execution endpoint
└── transforms/
    ├── dispatcher.py # Routes transforms by entity kind
    ├── ip.py         # AbuseIPDB IP analysis
    ├── domain.py     # URLScan domain analysis
    ├── url.py        # URLScan URL analysis
    ├── email.py      # Hunter.io email verification
    ├── hash.py       # VirusTotal hash analysis
    ├── phone.py      # NumVerify phone validation
    ├── whois.py      # WhoisXML domain registration
    ├── shodan.py     # Shodan IP scanning
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
- `/comments/*` - Comments on entities
- `GET /entities/{id}/transforms` - List available transforms for entity
- `POST /entities/{id}/transforms/run` - Run transforms on an entity
- `GET /timeline/` - Get activity timeline
- `POST /import/entities` - Bulk import entities from CSV/JSON
- `GET /export/case/{id}` - Export case data as JSON or CSV

## Features

### Dashboard
- Live statistics cards showing counts for cases, entities, relationships, and API keys
- Entity type breakdown chart with color-coded bars
- Recent activity feed showing latest actions

### Entity Detail Page
- Comprehensive view of entity information (name, kind, case, description)
- Shows all related entities via relationships with direction indicators
- Notes & comments section for adding investigation notes
- Quick actions: Run Transform, Delete Entity

### Comments System
- Add notes and comments to any entity
- View comment history with timestamps
- Delete comments when no longer needed
- Useful for tracking investigation findings

### Bulk Import
- Upload CSV or JSON files containing entities
- Required fields: name, kind (or type)
- Optional field: description
- Validates data and reports errors

### Export
- Export individual cases with all entities and relationships
- Supports JSON and CSV formats
- Triggers file download

### Keyboard Shortcuts
- `d` - Dashboard
- `c` - Cases
- `e` - Entities
- `r` - Relationships
- `g` - Graph
- `t` - Timeline
- `k` - API Keys
- `Ctrl+N` - Create new item in current section
- `Esc` - Close modal
- `Shift+?` - Show help

### Transforms
Transforms analyze entities using external APIs and create new related entities. When multiple transforms are available for an entity type, a selection modal appears.

#### IP Transforms
| Transform | API Key Required | Creates |
|-----------|-----------------|---------|
| AbuseIPDB | `ABUSEIPDB_API_KEY` | Threat entity with abuse score, country, ISP |
| Shodan | `SHODAN_API_KEY` | Open ports, hostnames, vulnerabilities, org info |

#### Domain Transforms
| Transform | API Key Required | Creates |
|-----------|-----------------|---------|
| URLScan | `URLSCAN_API_KEY` | Screenshot, resolved IPs (takes ~60s) |
| WHOIS | `WHOISXML_API_KEY` | Registrar info, registrant, nameservers, expiry dates |

#### URL Transform
| Transform | API Key Required | Creates |
|-----------|-----------------|---------|
| URLScan | `URLSCAN_API_KEY` | Domain extraction, malicious detection, screenshot, contacted IPs (takes ~60s) |

#### Email Transform
| Transform | API Key Required | Creates |
|-----------|-----------------|---------|
| Hunter.io | `HUNTER_API_KEY` | Verification status, score, domain, public sources |

#### Hash Transform (MD5, SHA1, SHA256)
| Transform | API Key Required | Creates |
|-----------|-----------------|---------|
| VirusTotal | `VIRUSTOTAL_API_KEY` | Malware detection, file type, known filenames |

#### Phone Transform
| Transform | API Key Required | Creates |
|-----------|-----------------|---------|
| NumVerify | `NUMVERIFY_API_KEY` | Validation, country, carrier, line type |

### API Key Setup
Add API keys to the API Keys vault with these exact names:
- `ABUSEIPDB_API_KEY` - Get at https://abuseipdb.com/
- `URLSCAN_API_KEY` - Get at https://urlscan.io/
- `HUNTER_API_KEY` - Get at https://hunter.io/api
- `VIRUSTOTAL_API_KEY` - Get at https://www.virustotal.com/gui/my-apikey
- `NUMVERIFY_API_KEY` - Get at https://numverify.com/
- `WHOISXML_API_KEY` - Get at https://whois.whoisxmlapi.com/
- `SHODAN_API_KEY` - Get at https://shodan.io/

### Graph Visualization
- Interactive network graph using vis-network library
- Nodes colored by entity type (IP=green, Domain=blue, Threat=red, etc.)
- Filter by case to focus on specific investigations
- Edges show relationship types between entities
- Glowing shadow effects and curved edges

### Activity Timeline
- Chronological log of all create/delete actions
- Tracks cases, entities, relationships
- Shows timestamps and action details

## Database
The application uses PostgreSQL for persistent storage. The database is automatically configured via the `DATABASE_URL` environment variable.

### Tables
- `users` - User accounts with password hashes
- `cases` - Investigation cases
- `entities` - OSINT entities (IPs, domains, threats, etc.)
- `relationships` - Links between entities
- `apikeys` - API key vault
- `activity_logs` - Timeline of user actions
- `comments` - Notes and comments on entities

## Supported Entity Types
- `ip` - IP addresses
- `domain` - Domain names
- `url` - Full URLs
- `email` - Email addresses
- `hash` - File hashes (MD5, SHA1, SHA256)
- `phone` - Phone numbers
- `threat` - Threat indicators
- `person` - People
- `organization` - Organizations
- `location` - Geographic locations
- `vulnerability` - CVEs and security vulnerabilities
- `verification` - Verification results
- `analysis` - Analysis results
- `screenshot` - Website screenshots
- `port` - Network ports
- `nameserver` - DNS nameservers
- `whois` - WHOIS records

## Notes
- Data persists across restarts via PostgreSQL
- Tokens signed with HS256 algorithm
- API keys stored in vault with description field containing actual key value
- Comments are scoped to entity owner for security
- URLScan transforms take ~60 seconds due to external API processing
