import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models import ScanStatus


class FindingResponse(BaseModel):
    package: str | None
    version: str | None
    vulnerability_id: str
    summary: str | None
    severity: str | None
    fixed_version: str | None
    advisory_url: str | None


class UnsupportedDependencyResponse(BaseModel):
    original_requirement: str
    package_name: str | None
    reason: str


class ScanResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    repository_full_name: str
    status: ScanStatus
    error_code: str | None
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    created_at: datetime
    dependency_count: int = 0
    checked_count: int = 0
    unsupported_count: int = 0
    finding_count: int = 0
    findings: list[FindingResponse] = []
    unsupported_dependencies: list[UnsupportedDependencyResponse] = []
    warnings: list[str] = []


class ScanSummary(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    repository_full_name: str
    status: ScanStatus
    error_code: str | None
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None
    created_at: datetime
    dependency_count: int
    finding_count: int
