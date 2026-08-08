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
- Repository and scan authorization must enforce current-user ownership in SQL.
- Historical scan data must not be overwritten.
- GitHub credentials are backend-only and must never be exposed.
- External API clients belong in `clients/`; orchestration belongs in `services/`.
- Repository and scan queries must always be scoped to the current user.
- Missing `requirements.txt` is a failed scan, never a successful scan.
- GitHub failures must not be reported as successful scans.
- Parse only exact `name==version` requirements for OSV; preserve unsupported lines.
- OSV calls use the batch API and belong in `clients/`.
- Never expose raw OSV JSON through API schemas.
- Reuse vulnerabilities by OSV ID; keep dependencies and findings historical per scan.
- Unknown severity and fixed versions remain null; never guess security data.
- Scan lifecycle logs may contain safe UUIDs and error codes, never secrets or external payloads.
- Reject a second running scan for the same repository; distributed locking remains deferred.
- OSV failure must never be reported as zero vulnerabilities.
- Do not introduce Docker, AWS, queues, workers, or microservices unless the current task explicitly requests them.
- Important behavior must have tests.
- Prefer simple, explainable implementations over unnecessary abstraction.
