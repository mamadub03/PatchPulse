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
- A temporary, configured local development-user identity.
- Backend-only GitHub repository synchronization and `requirements.txt` retrieval.
- Ownership-scoped repository and scan APIs with persisted scan history.

Production authentication, Docker, cloud infrastructure, queues, workers, and CI/CD are intentionally not included yet.

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
- `PATCHPULSE_DEV_USER_EMAIL`
- `GITHUB_TOKEN`
- `PATCHPULSE_REQUIREMENTS_MAX_BYTES`
- `PATCHPULSE_OSV_API_URL`
- `PATCHPULSE_OSV_CONNECT_TIMEOUT_SECONDS`
- `PATCHPULSE_OSV_READ_TIMEOUT_SECONDS`

Use this local PostgreSQL URL format:

```text
postgresql+psycopg://USERNAME:PASSWORD@localhost:5432/patchpulse
```

Example:

```env
DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/patchpulse
```

Do not commit real credentials.

Create a fine-grained GitHub personal access token with read-only access to repository metadata
and contents for only the repositories you want to inspect. Put it in `backend/.env`; it is used
only by the backend and is never returned to the browser or stored in PostgreSQL:

```env
PATCHPULSE_DEV_USER_EMAIL=dev@patchpulse.local
GITHUB_TOKEN=github_pat_your_local_token
PATCHPULSE_REQUIREMENTS_MAX_BYTES=1000000
```

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
python -m uv run python -m app.scripts.seed_dev_user
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

## Local GitHub Workflow

Real authentication is intentionally deferred. `get_current_user` resolves the user whose email is
configured by `PATCHPULSE_DEV_USER_EMAIL`; the frontend cannot select or override a user ID. Seed the
user explicitly after migrations:

```bash
cd backend
uv run python -m app.scripts.seed_dev_user
```

The command is idempotent. Requests return a safe 503 response until this configured user exists.

Available application endpoints:

- `POST /api/v1/repositories/sync`: reads accessible GitHub repositories and upserts metadata for
  the current user without deleting missing historical rows.
- `GET /api/v1/repositories`: lists only the current user's repositories.
- `POST /api/v1/repositories/{repository_id}/scans`: creates and commits a running scan, retrieves
  `requirements.txt` from the default branch, and commits a completed or failed final state.
- `GET /api/v1/scans`: returns the current user's scan history, newest first.
- `GET /api/v1/scans/{scan_id}`: returns a scan only when its repository belongs to the current user.

Repository and scan ownership is enforced in SQL. Unknown resources and resources belonging to a
different user both return 404 to avoid leaking their existence.

The scan service deliberately commits the running scan before calling GitHub. Successful non-empty
content within the configured size limit completes the scan. Missing, empty, or oversized files and
GitHub authentication, authorization, rate-limit, network, malformed-response, or service failures
produce a persisted failed scan with safe error fields. Raw GitHub bodies, headers, tokens, and file
contents are not returned.

The frontend provides repository synchronization, repository cards with Start Scan actions, and
persisted scan history. Configure credentials only in `backend/.env`, seed the user, then start both
applications and select **Sync GitHub Repositories**.

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
Scan 1 -> many ScanDependency
ScanDependency 1 -> many Finding
Vulnerability 1 -> many Finding
```

Historical scan records are preserved. Cascade-delete behavior is intentionally not broad.

## Vulnerability Scanning

After GitHub retrieval, PatchPulse parses root-level `requirements.txt`. Only exact standard pins
such as `Django==4.2.2` are checked. Names are normalized using Python packaging conventions.
Ranges, unpinned packages, directives, URLs, extras, markers, hashes, local paths, and malformed
lines are preserved as unsupported dependencies rather than guessed or discarded.

Supported pins are sent together to OSV's PyPI batch endpoint. OSV records are normalized and
upserted by OSV ID, while raw JSON remains internal in PostgreSQL JSONB. PatchPulse uses a textual
severity only when OSV supplies a recognized categorical value; otherwise severity is unknown.
The first explicit fixed event is shown as the fixed version; absent evidence remains unknown.

Scan status rules:

- `completed`: every eligible dependency was checked successfully, including zero findings.
- `completed_with_warnings`: OSV checks succeeded, but one or more requirements were unsupported.
- `failed`: GitHub, OSV, file validation, or critical processing prevented a reliable result.

The running scan is committed before external calls. Dependencies, vulnerabilities, findings, and
the successful final state are committed together. OSV failure is persisted as a failed scan and is
never presented as a successful zero-vulnerability result. Scan detail returns stored counts,
findings, unsupported dependencies, and warnings without exposing raw OSV data.

## Architecture and Trust Boundaries

```text
Browser -> FastAPI routes -> current-user/authorization dependencies -> services
        -> GitHub client -> requirements parser -> OSV client -> SQLAlchemy/PostgreSQL
        <- Pydantic-filtered API responses <- stored scan results
```

The browser is untrusted and never chooses a user ID or receives GitHub/database credentials.
Repository and scan ownership is enforced in SQL, not by frontend filtering. GitHub, requirements
files, and OSV responses are untrusted external input. Raw OSV JSON is retained internally for
future normalization improvements but excluded from response schemas. Historical dependencies and
findings belong to immutable scan contexts; later scans create new rows. Synchronous scans keep the
MVP explainable, while the initial running state is committed before external work begins.

## Common Errors and Database Inspection

- `GitHub access is not configured`: put a replacement fine-grained token only in `backend/.env`
  and restart the backend.
- `GitHub credentials are invalid or revoked`: generate a new read-only token and restart.
- `Development user is not initialized`: run `uv run python -m app.scripts.seed_dev_user`.
- `Database unavailable`: start PostgreSQL, verify `DATABASE_URL`, and run migrations.
- `A scan is already running`: wait for the synchronous request to finish. A crashed process can
  leave a stale running row; automatic recovery is intentionally deferred.

Inspect local data with `psql` without selecting secret or raw payload columns:

```sql
SELECT id, email FROM users;
SELECT id, full_name FROM repositories ORDER BY full_name;
SELECT id, repository_id, status, completed_at FROM scans ORDER BY created_at DESC;
SELECT scan_id, package_name, version, is_supported, checked FROM scan_dependencies;
SELECT id, osv_id, severity FROM vulnerabilities;
SELECT scan_id, scan_dependency_id, vulnerability_id FROM findings;
```

Running the same repository twice creates separate `scans` and `scan_dependencies`; vulnerability
identity may be reused by OSV ID, but old dependency versions and findings are not overwritten.

## Dockerization Handoff

No Docker files are included yet. The containerization phase will need:

- Backend command: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- Frontend production build: `npm run build`; serve `frontend/dist` with an HTTP server.
- Ports: frontend `5173` for Vite development (production port is a deployment choice), backend
  `8000`, and PostgreSQL `5432` on its internal network.
- Runtime variables: `DATABASE_URL`, `GITHUB_TOKEN`, `PATCHPULSE_DEV_USER_EMAIL`, API/CORS settings,
  GitHub/OSV URLs and timeouts, size limits, and `VITE_API_BASE_URL` at frontend build time.
- Run `uv run alembic upgrade head` as an explicit deployment step; never create tables at startup.
- Persist PostgreSQL data in a database volume. Application containers require no durable volume.
- Use service DNS names rather than `localhost` for database/backend inter-service connections.
- Keep `/api/v1/health` as liveness and `/api/v1/readiness` as database readiness.

Before a multi-user deployment, replace the development identity and shared PAT with authentication
and a GitHub App. Store secrets in the deployment secret mechanism, not images or frontend assets.

## Known Missing Functionality

- GitHub OAuth and production authentication
- Dependency-file discovery beyond root-level `requirements.txt`
- Lockfiles and dependency formats beyond root-level `requirements.txt`
- Transitive dependency resolution
- Rich CVSS severity calculation and affected-range interpretation
- Production authentication and per-user GitHub OAuth credentials
- Production deployment and infrastructure
