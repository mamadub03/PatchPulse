# PatchPulse Agent Guidance

PatchPulse uses a separate React frontend and FastAPI backend.

- API routes should remain thin.
- Business workflows belong in services.
- Pydantic schemas control API input and output.
- SQLAlchemy models will represent database persistence.
- Use SQLAlchemy 2.0 directly, not SQLModel.
- Use synchronous database sessions for the MVP.
- Use Alembic for schema changes.
- Never create production tables automatically at startup.
- Do not expose database models directly as API responses.
- Do not log credentials or full database URLs.
- GitHub and OSV communication will belong in clients.
- External input must be treated as untrusted.
- GitHub tokens and other secrets must remain backend-only.
- Repository authorization must eventually prevent BOLA/IDOR.
- Historical scan data must not be overwritten.
- OSV failure must never be reported as zero vulnerabilities.
- Do not introduce Docker, AWS, queues, workers, or microservices unless the current task explicitly requests them.
- Important behavior must have tests.
- Prefer simple, explainable implementations over unnecessary abstraction.
