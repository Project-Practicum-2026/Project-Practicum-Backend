# LogiGlobal Backend

## Tech Stack
- Python 3.12 + FastAPI
- SQLAlchemy async + PostgreSQL 16
- Redis 7 + Celery
- Docker Compose
- uv

## Requirements
- Python 3.12
- Docker + Docker Compose
- uv

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/Project-Practicum-2026/Project-Practicum-Backend.git
cd Project-Practicum-Backend
git checkout develop
```

### 2. Setup Python environment
```bash
uv python pin 3.12
uv venv
source .venv/bin/activate  # Mac / Linux
.venv\Scripts\activate     # Windows
```

### 3. Install dependencies
```bash
uv sync
```

### 4. Setup environment variables
```bash
cp .env.example .env
```

### 5. Start all services
```bash
docker compose up --build
```
API: http://localhost:8000

Swagger UI: http://localhost:8000/docs

### 6. Run migrations (locally without Docker)
```bash
alembic upgrade head
```

### 7. Start server locally
```bash
uv run fastapi dev app/main.py
```

## Testing
```bash
uv run pytest tests/ -v
```

## Git Workflow
- `main` — production
- `develop` — integration branch
- `feature/*` — new features
- `fix/*` — bug fixes

## Versions
- `v0.1.0` — Auth, Drivers, Warehouses, Fleet