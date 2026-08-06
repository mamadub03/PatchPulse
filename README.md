# PatchPulse

PatchPulse is a dependency-vulnerability tracking web application. The product will eventually connect to GitHub, scan Python `requirements.txt` dependencies through OSV, store scan history, and present findings in a frontend.

## Current Scope

This repository currently contains the first two local full-stack vertical slices:

- A FastAPI backend with `GET /api/v1/health`.
- Pydantic-validated health response data.
- Environment-based backend settings through `pydantic-settings`.
- Explicit local CORS configuration for the frontend origin.
- A React, TypeScript, and Vite frontend that checks backend health on page load.
- PostgreSQL configuration loaded from `DATABASE_URL`.
- SQLAlchemy 2.0 typed ORM models for users, repositories, and scans.
- Alembic migrations that control schema creation.
- A database readiness endpoint at `GET /api/v1/readiness`.

Authentication, GitHub integration, OSV integration, dependency parsing, Docker, cloud infrastructure, queues, workers, and CI/CD are intentionally not included yet.

## Repository Structure

```text
patchpulse/
|-- AGENTS.md
|-- README.md
|-- .env.example
|-- .gitignore
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |-- clients/
|   |   |-- core/
|   |   |-- db/
|   |   |-- models/
|   |   |-- schemas/
|   |   |-- services/
|   |   `-- main.py
|   |-- migrations/
|   |-- tests/
|   |-- alembic.ini
|   |-- .env.example
|   |-- pyproject.toml
|   `-- uv.lock
`-- frontend/
    |-- src/
    |-- .env.example
    |-- package.json
    `-- vite.config.ts
```

## Prerequisites

- Python 3.12 or newer.
- `uv` for backend dependency management.
- Node.js and npm for the frontend.
- PostgreSQL running locally.

This project does not include Docker yet. The commands below are for a direct local setup on Windows, macOS, or Linux.

## Install Prerequisites

### Python and uv

Install Python from your OS package manager, `pyenv`, `asdf`, the Microsoft Store, or `python.org`.

Install `uv`:

```bash
python -m pip install --user uv
```

If your system uses `python3` instead of `python`:

```bash
python3 -m pip install --user uv
```

### Node.js and npm

Install Node.js from `nodejs.org`, `nvm`, `fnm`, Homebrew, Chocolatey, or your Linux package manager. Confirm it is available:

```bash
node --version
npm --version
```

On Windows PowerShell, if `npm` is blocked by execution policy, use:

```powershell
npm.cmd --version
```

### PostgreSQL

Install PostgreSQL using the path that fits your machine:

- Windows: use the official PostgreSQL installer, then open SQL Shell (`psql`) from the Start Menu.
- macOS with Homebrew: install PostgreSQL with Homebrew.
- Ubuntu/Debian: install PostgreSQL through `apt`.
- Fedora: install PostgreSQL through `dnf`.
- Arch: install PostgreSQL through `pacman`.

After install, make sure PostgreSQL is running and that you know which database user and password you will use locally.

## Environment Variables

Copy the example values before running locally.

macOS/Linux/Git Bash:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Windows PowerShell:

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
- `DATABASE_URL`

Use this local PostgreSQL URL format:

```text
postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/patchpulse
```

Example:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/patchpulse
```

Do not commit real credentials.

Frontend variables:

- `VITE_API_BASE_URL`

## Local PostgreSQL Setup

Create a database named `patchpulse`. The exact command depends on how PostgreSQL is installed.

### Option 1: createdb Available

If `createdb` is on your PATH:

```bash
createdb patchpulse
```

### Option 2: psql SQL Command

If `createdb` is not available but you can open `psql`:

```sql
CREATE DATABASE patchpulse;
```

On Windows, the PostgreSQL installer usually adds **SQL Shell (psql)** to the Start Menu. Open it, connect as the `postgres` user, enter the password you chose during installation, then run the SQL above.

### Option 3: Admin GUI

If you use pgAdmin or another GUI, create a database named `patchpulse` there.

After the database exists, set `DATABASE_URL` in `backend/.env`.

## Fresh Device Setup

Use this flow when setting up PatchPulse on a different computer from a fresh Git clone.

1. Clone the repository:

```bash
git clone REPOSITORY_URL
cd PatchPulse
```

If your clone creates the same nested folder layout used during local development, enter the inner project directory:

```bash
cd PatchPulse
```

2. Install the prerequisites:

- Python 3.12 or newer.
- `uv`.
- Node.js and npm.
- PostgreSQL.

3. Create local environment files:

macOS/Linux/Git Bash:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
```

4. Create a local PostgreSQL database named `patchpulse`.

With `createdb`:

```bash
createdb patchpulse
```

Or from `psql`:

```sql
CREATE DATABASE patchpulse;
```

5. Update `backend/.env` with your real local database credentials:

```env
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/patchpulse
```

6. Install backend dependencies and apply migrations:

```bash
cd backend
python -m uv sync --dev
python -m uv run alembic upgrade head
```

7. Install frontend dependencies:

```bash
cd ../frontend
npm install
```

On Windows PowerShell, use `npm.cmd install` if `npm` is blocked.

8. Run verification:

```bash
cd ../backend
python -m uv run pytest
python -m uv run ruff check .
python -m uv run ruff format --check .
```

```bash
cd ../frontend
npm run lint
npm run build
```

On Windows PowerShell, use `npm.cmd run lint` and `npm.cmd run build` if needed.

9. Start the apps:

Backend terminal:

```bash
cd backend
python -m uv run uvicorn app.main:app --reload
```

Frontend terminal:

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`.

Expected local state:

- Backend health should show healthy when the FastAPI server is running.
- Database readiness should show connected after PostgreSQL is running, `DATABASE_URL` is correct, and `python -m uv run alembic upgrade head` has completed.
- If PostgreSQL is not running yet, the app can still load, but database readiness will show unavailable.

## Backend Setup

macOS/Linux/Git Bash:

```bash
cd backend
python -m uv sync --dev
python -m uv run alembic upgrade head
python -m uv run uvicorn app.main:app --reload
```

Windows PowerShell:

```powershell
Set-Location backend
python -m uv sync --dev
python -m uv run alembic upgrade head
python -m uv run uvicorn app.main:app --reload
```

Useful Alembic commands:

```bash
python -m uv run alembic current
python -m uv run alembic history
python -m uv run alembic downgrade -1
python -m uv run alembic upgrade head
```

## Health and Readiness

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

The readiness endpoint checks PostgreSQL connectivity:

```text
GET http://localhost:8000/api/v1/readiness
```

Successful response:

```json
{
  "status": "ready",
  "database": "connected"
}
```

Unavailable response:

```json
{
  "status": "not_ready",
  "database": "unavailable"
}
```

`/health` is a liveness check and does not query PostgreSQL. `/readiness` is a readiness check and executes a lightweight database query.

## Frontend Setup

macOS/Linux/Git Bash:

```bash
cd frontend
npm install
npm run dev
```

Windows PowerShell:

```powershell
Set-Location frontend
npm.cmd install
npm.cmd run dev
```

The Vite development server defaults to:

```text
http://localhost:5173
```

## Tests and Checks

Backend:

```bash
cd backend
python -m uv run pytest
python -m uv run ruff check .
python -m uv run ruff format --check .
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

On Windows PowerShell, use `npm.cmd run lint` and `npm.cmd run build` if `npm` itself is blocked.

## Running Locally

Start the backend in one terminal:

```bash
cd backend
python -m uv run uvicorn app.main:app --reload
```

Start the frontend in another terminal:

```bash
cd frontend
npm run dev
```

On Windows PowerShell, use `Set-Location` instead of `cd` if preferred, and use `npm.cmd run dev` if needed.

Open `http://localhost:5173` and confirm that the backend connection status is healthy.

The frontend displays two separate indicators: backend API health and PostgreSQL readiness. Both calls use `VITE_API_BASE_URL`.

## Persistence Model

PatchPulse uses SQLAlchemy 2.0 typed declarative mappings with synchronous sessions for the MVP. Alembic owns schema creation and changes; the application does not call `Base.metadata.create_all()` at startup.

Current models:

- `User`: stores a unique indexed email and timestamps.
- `Repository`: belongs to one user and stores GitHub repository identity and display fields.
- `Scan`: belongs to one repository and stores scan status, nullable failure details, and timing fields.

Relationships:

```text
User 1 -> many Repository
Repository 1 -> many Scan
```

Historical scan records are preserved. Cascade-delete behavior is intentionally not broad.

## Known Missing Functionality

- GitHub authentication and repository selection
- Dependency file discovery
- OSV vulnerability scanning
- Real scan lifecycle orchestration
- Dependency, vulnerability, and finding persistence
- Historical scan views
- Repository authorization controls
- Production deployment and infrastructure
