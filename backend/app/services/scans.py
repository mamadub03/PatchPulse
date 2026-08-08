import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.clients.github import GitHubClient, GitHubError, GitHubRepository
from app.clients.osv import OsvClient, OsvError
from app.models import Finding, Repository, Scan, ScanDependency, ScanStatus, User, Vulnerability
from app.services.requirements import parse_requirements

logger = logging.getLogger(__name__)


class RepositoryNotFoundError(Exception):
    pass


class ScanAlreadyRunningError(Exception):
    pass


class RequirementsFileError(Exception):
    def __init__(self, error_code: str, safe_message: str) -> None:
        self.error_code = error_code
        self.safe_message = safe_message


def start_scan(
    session: Session,
    user: User,
    repository_id: uuid.UUID,
    github: GitHubClient,
    requirements_max_bytes: int,
    osv: OsvClient | None = None,
) -> Scan:
    repository = session.scalar(
        select(Repository).where(
            Repository.id == repository_id,
            Repository.user_id == user.id,
        )
    )
    if repository is None:
        raise RepositoryNotFoundError()
    running_scan = session.scalar(
        select(Scan.id).where(
            Scan.repository_id == repository.id,
            Scan.status == ScanStatus.RUNNING,
        )
    )
    if running_scan is not None:
        raise ScanAlreadyRunningError()

    scan = Scan(
        repository_id=repository.id,
        status=ScanStatus.RUNNING,
        started_at=datetime.now(UTC),
    )
    session.add(scan)
    session.commit()
    session.refresh(scan)
    logger.info("Scan started scan_id=%s repository_id=%s", scan.id, repository.id)

    try:
        content = github.get_requirements_file(
            GitHubRepository(
                repository.github_repository_id,
                repository.owner,
                repository.name,
                repository.full_name,
                repository.default_branch,
                repository.is_private,
            )
        )
        if not content:
            raise RequirementsFileError(
                "requirements_file_empty",
                "requirements.txt is empty.",
            )
        if len(content) > requirements_max_bytes:
            raise RequirementsFileError(
                "requirements_file_too_large",
                "requirements.txt exceeds the configured size limit.",
            )
        parsed = parse_requirements(content)
        supported = [item for item in parsed if item.is_supported]
        osv_results = (
            osv.query_batch([(item.package_name, item.version) for item in supported])
            if osv
            else [[] for item in supported]
        )
        dependencies: list[ScanDependency] = []
        supported_index = 0
        for item in parsed:
            dependency = ScanDependency(
                scan_id=scan.id,
                package_name=item.package_name,
                version=item.version,
                original_requirement=item.original,
                is_supported=item.is_supported,
                checked=item.is_supported,
                unsupported_reason=item.unsupported_reason,
            )
            session.add(dependency)
            dependencies.append(dependency)
        session.flush()
        for dependency in dependencies:
            if not dependency.is_supported:
                continue
            for normalized in osv_results[supported_index]:
                vulnerability = session.scalar(
                    select(Vulnerability).where(Vulnerability.osv_id == normalized.osv_id)
                )
                if vulnerability is None:
                    vulnerability = Vulnerability(
                        osv_id=normalized.osv_id,
                        summary=normalized.summary,
                        details=normalized.details,
                        severity=normalized.severity,
                        advisory_url=normalized.advisory_url,
                        raw_osv_data=normalized.raw_data,
                    )
                    session.add(vulnerability)
                    session.flush()
                else:
                    vulnerability.summary, vulnerability.details = (
                        normalized.summary,
                        normalized.details,
                    )
                    vulnerability.severity, vulnerability.advisory_url = (
                        normalized.severity,
                        normalized.advisory_url,
                    )
                    vulnerability.raw_osv_data = normalized.raw_data
                session.add(
                    Finding(
                        scan_id=scan.id,
                        scan_dependency_id=dependency.id,
                        vulnerability_id=vulnerability.id,
                        fixed_version=normalized.fixed_version,
                    )
                )
            supported_index += 1
    except (GitHubError, OsvError, RequirementsFileError, ValueError) as exc:
        session.rollback()
        scan = session.get(Scan, scan.id)
        scan.status = ScanStatus.FAILED
        scan.error_code = getattr(exc, "error_code", "requirements_processing_failed")
        scan.error_message = getattr(
            exc, "safe_message", "requirements.txt could not be processed safely."
        )
        logger.warning(
            "Scan failed scan_id=%s repository_id=%s error_code=%s",
            scan.id,
            repository.id,
            scan.error_code,
        )
    else:
        scan.status = (
            ScanStatus.COMPLETED_WITH_WARNINGS
            if any(not item.is_supported for item in parsed)
            else ScanStatus.COMPLETED
        )
        scan.error_code = None
        scan.error_message = None
        logger.info(
            "Scan completed scan_id=%s repository_id=%s status=%s",
            scan.id,
            repository.id,
            scan.status.value,
        )
    scan.completed_at = datetime.now(UTC)
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        logger.error(
            "Scan result persistence failed scan_id=%s repository_id=%s",
            scan.id,
            repository.id,
        )
        failed_scan = session.get(Scan, scan.id)
        if failed_scan is not None:
            failed_scan.status = ScanStatus.FAILED
            failed_scan.error_code = "persistence_failed"
            failed_scan.error_message = "Scan results could not be saved."
            failed_scan.completed_at = datetime.now(UTC)
            session.commit()
        raise
    session.refresh(scan)
    return scan


def list_user_scans(session: Session, user: User) -> list[Scan]:
    return list(
        session.scalars(
            select(Scan)
            .join(Scan.repository)
            .where(Repository.user_id == user.id)
            .options(
                joinedload(Scan.repository),
                selectinload(Scan.dependencies)
                .selectinload(ScanDependency.findings)
                .joinedload(Finding.vulnerability),
            )
            .order_by(Scan.created_at.desc(), Scan.id.desc())
        )
    )


def get_user_scan(session: Session, user: User, scan_id: uuid.UUID) -> Scan | None:
    return session.scalar(
        select(Scan)
        .join(Scan.repository)
        .where(Scan.id == scan_id, Repository.user_id == user.id)
        .options(
            joinedload(Scan.repository),
            selectinload(Scan.dependencies)
            .selectinload(ScanDependency.findings)
            .joinedload(Finding.vulnerability),
        )
    )
