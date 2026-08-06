# PatchPulse

PatchPulse is a dependency-vulnerability tracking web application. The product will eventually connect to GitHub, scan Python `requirements.txt` dependencies through OSV, store scan history, and present findings in a frontend.

## Current Scope

This repository currently contains the first local full-stack vertical slice:

- A FastAPI backend with `GET /api/v1/health`.
- Pydantic-validated health response data.
- Environment-based backend settings through `pydantic-settings`.
- Explicit local CORS configuration for the frontend origin.
- A React, TypeScript, and Vite frontend that checks backend health on page load.

PostgreSQL, SQLAlchemy models, Alembic migrations, authentication, GitHub integration, OSV integration, Docker, cloud infrastructure, queues, workers, and CI/CD are intentionally not included yet.

## Repository Structure

```text
patchpulse/
├── AGENTS.md
├── README.md
├── .env.example
├── .gitignore
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── clients/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   ├── tests/
│   ├── .env.example
│   └── pyproject.toml
└── frontend/
    ├── src/
    ├── .env.example
    ├── package.json
    └── vite.config.ts
```

## Prerequisites

- Python 3.12 or newer
- `uv`
- Node.js and npm

## Environment Variables

Copy the example values before running locally:

```powershell
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

Backend variables:

- `PATCHPULSE_APP_NAME`
- `PATCHPULSE_ENVIRONMENT`
- `PATCHPULSE_API_PREFIX`
- `PATCHPULSE_ALLOWED_FRONTEND_ORIGIN`

Frontend variables:

- `VITE_API_BASE_URL`

## Backend Setup

```powershell
Set-Location backend
uv sync --dev
```

Run the backend:

```powershell
Set-Location backend
uv run uvicorn app.main:app --reload
```

The health endpoint should respond at:

```text
GET http://localhost:8000/api/v1/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "patchpulse-api"
}
```

## Frontend Setup

```powershell
Set-Location frontend
npm install
```

Run the frontend:

```powershell
Set-Location frontend
npm run dev
```

The Vite development server defaults to:

```text
http://localhost:5173
```

## Tests and Checks

Backend:

```powershell
Set-Location backend
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Frontend:

```powershell
Set-Location frontend
npm run lint
npm run build
```

## Running Locally

Start the backend in one terminal:

```powershell
Set-Location backend
uv run uvicorn app.main:app --reload
```

Start the frontend in another terminal:

```powershell
Set-Location frontend
npm run dev
```

Open `http://localhost:5173` and confirm that the backend connection status is healthy.

## Known Missing Functionality

- GitHub authentication and repository selection
- Dependency file discovery
- OSV vulnerability scanning
- PostgreSQL persistence
- Historical scan views
- Repository authorization controls
- Production deployment and infrastructure
