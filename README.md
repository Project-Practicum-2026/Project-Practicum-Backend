# Project-Practicum-Backend

## Requirements
- Python 3.12
- Docker + Docker Compose
- uv

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/<your-repo>.git
cd <repo-name>
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
Open `.env` and fill in the values.

### 5. Start database
```bash
docker compose up -d
```

### 6. Run migrations
```bash
alembic upgrade head
```

### 7. Start the server
```bash
uvicorn app.main:app --reload
```

## Git Workflow
- `main` — production
- `develop` — integration branch
- `feature/*` — new features
- `fix/*` — bug fixes

All feature branches are created from `develop` and merged back via PR.