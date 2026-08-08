import uuid

from fastapi import APIRouter, HTTPException

from app.api.dependencies import CurrentUser, DatabaseSession
from app.schemas.scan import (
    FindingResponse,
    ScanResponse,
    ScanSummary,
    UnsupportedDependencyResponse,
)
from app.services.scans import get_user_scan, list_user_scans

router = APIRouter(prefix="/scans", tags=["scans"])


def _response(scan: object) -> ScanResponse:
    dependencies = scan.dependencies
    findings = [finding for dependency in dependencies for finding in dependency.findings]
    unsupported = [dependency for dependency in dependencies if not dependency.is_supported]
    return ScanResponse(
        **scan.__dict__,
        repository_full_name=scan.repository.full_name,
        dependency_count=len(dependencies),
        checked_count=sum(dependency.checked for dependency in dependencies),
        unsupported_count=len(unsupported),
        finding_count=len(findings),
        findings=[
            FindingResponse(
                package=item.scan_dependency.package_name,
                version=item.scan_dependency.version,
                vulnerability_id=item.vulnerability.osv_id,
                summary=item.vulnerability.summary,
                severity=item.vulnerability.severity,
                fixed_version=item.fixed_version,
                advisory_url=item.vulnerability.advisory_url,
            )
            for item in findings
        ],
        unsupported_dependencies=[
            UnsupportedDependencyResponse(
                original_requirement=item.original_requirement,
                package_name=item.package_name,
                reason=item.unsupported_reason or "unsupported_requirement",
            )
            for item in unsupported
        ],
        warnings=["Some dependencies could not be checked."] if unsupported else [],
    )


@router.get("", response_model=list[ScanSummary])
def read_scans(session: DatabaseSession, current_user: CurrentUser) -> list[ScanSummary]:
    return [
        ScanSummary(
            **_response(scan).model_dump(
                exclude={
                    "checked_count",
                    "unsupported_count",
                    "findings",
                    "unsupported_dependencies",
                    "warnings",
                }
            )
        )
        for scan in list_user_scans(session, current_user)
    ]


@router.get("/{scan_id}", response_model=ScanResponse)
def read_scan(
    scan_id: uuid.UUID, session: DatabaseSession, current_user: CurrentUser
) -> ScanResponse:
    scan = get_user_scan(session, current_user, scan_id)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return _response(scan)
