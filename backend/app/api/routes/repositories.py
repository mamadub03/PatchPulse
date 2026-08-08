import uuid
from collections.abc import Generator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import AppSettings, CurrentUser, DatabaseSession
from app.api.routes.scans import _response
from app.clients.github import GitHubClient, GitHubError, get_github_client
from app.clients.osv import OsvClient
from app.core.config import get_settings
from app.schemas.repository import RepositoryResponse, RepositorySyncResponse
from app.schemas.scan import ScanResponse
from app.services.repositories import list_user_repositories, synchronize_repositories
from app.services.scans import RepositoryNotFoundError, ScanAlreadyRunningError, start_scan

router = APIRouter(prefix="/repositories", tags=["repositories"])


def github_dependency() -> Generator[GitHubClient]:
    generator = get_github_client()
    try:
        client = next(generator)
    except GitHubError as exc:
        raise HTTPException(status_code=503, detail=exc.safe_message) from exc
    try:
        yield client
    finally:
        generator.close()


GitHubDependency = Annotated[GitHubClient, Depends(github_dependency)]


def osv_dependency() -> Generator[OsvClient]:
    settings = get_settings()
    client = OsvClient(
        settings.osv_api_url,
        settings.osv_connect_timeout_seconds,
        settings.osv_read_timeout_seconds,
    )
    try:
        yield client
    finally:
        client.close()


OsvDependency = Annotated[OsvClient, Depends(osv_dependency)]


@router.get("", response_model=list[RepositoryResponse])
def read_repositories(
    session: DatabaseSession, current_user: CurrentUser
) -> list[RepositoryResponse]:
    return [
        RepositoryResponse.model_validate(item)
        for item in list_user_repositories(session, current_user)
    ]


@router.post("/sync", response_model=RepositorySyncResponse)
def sync_repositories(
    session: DatabaseSession,
    current_user: CurrentUser,
    github: GitHubDependency,
) -> RepositorySyncResponse:
    try:
        result = synchronize_repositories(session, current_user, github)
    except GitHubError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.safe_message
        ) from exc
    return RepositorySyncResponse(**result.__dict__)


@router.post(
    "/{repository_id}/scans", response_model=ScanResponse, status_code=status.HTTP_201_CREATED
)
def create_scan(
    repository_id: uuid.UUID,
    session: DatabaseSession,
    current_user: CurrentUser,
    github: GitHubDependency,
    osv: OsvDependency,
    settings: AppSettings,
) -> ScanResponse:
    try:
        scan = start_scan(
            session,
            current_user,
            repository_id,
            github,
            settings.requirements_max_bytes,
            osv,
        )
    except RepositoryNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Repository not found") from exc
    except ScanAlreadyRunningError as exc:
        raise HTTPException(status_code=409, detail="A scan is already running") from exc
    return _response(scan)
