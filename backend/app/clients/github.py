import base64
import binascii
import logging
from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class GitHubError(Exception):
    error_code = "github_unavailable"
    safe_message = "GitHub could not complete the request."


class GitHubConfigurationError(GitHubError):
    error_code = "github_not_configured"
    safe_message = "GitHub access is not configured."


class GitHubAuthenticationError(GitHubError):
    error_code = "github_authentication_failed"
    safe_message = "GitHub credentials are invalid or revoked."


class GitHubAuthorizationError(GitHubError):
    error_code = "github_authorization_failed"
    safe_message = "GitHub denied access or the rate limit was reached."


class GitHubNotFoundError(GitHubError):
    error_code = "requirements_file_missing"
    safe_message = "requirements.txt was not found on the default branch."


class GitHubResponseError(GitHubError):
    pass


@dataclass(frozen=True)
class GitHubRepository:
    github_repository_id: int
    owner: str
    name: str
    full_name: str
    default_branch: str
    is_private: bool


class GitHubClient:
    def __init__(
        self,
        token: str,
        *,
        api_url: str = "https://api.github.com",
        connect_timeout: float = 5.0,
        read_timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        timeout = httpx.Timeout(read_timeout, connect=connect_timeout)
        self._client = httpx.Client(
            base_url=api_url,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=timeout,
            transport=transport,
        )

    def close(self) -> None:
        self._client.close()

    def list_repositories(self) -> list[GitHubRepository]:
        repositories: list[GitHubRepository] = []
        page = 1
        while True:
            payload = self._request_json(
                "GET",
                "/user/repos",
                params={"per_page": 100, "page": page, "sort": "full_name"},
            )
            if not isinstance(payload, list):
                raise GitHubResponseError()
            repositories.extend(self._parse_repository(item) for item in payload)
            if len(payload) < 100:
                return repositories
            page += 1

    def get_requirements_file(self, repository: GitHubRepository) -> bytes:
        payload = self._request_json(
            "GET",
            f"/repos/{repository.owner}/{repository.name}/contents/requirements.txt",
            params={"ref": repository.default_branch},
            missing_is_not_found=True,
        )
        if not isinstance(payload, dict):
            raise GitHubResponseError()
        content = payload.get("content")
        if payload.get("encoding") != "base64" or not isinstance(content, str):
            raise GitHubResponseError()
        try:
            return base64.b64decode("".join(content.splitlines()), validate=True)
        except (ValueError, binascii.Error) as exc:
            raise GitHubResponseError() from exc

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        missing_is_not_found: bool = False,
        **kwargs: Any,
    ) -> Any:
        try:
            response = self._client.request(method, path, **kwargs)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.warning("GitHub request failed (error_type=%s)", type(exc).__name__)
            raise GitHubResponseError() from exc
        if response.is_error:
            logger.warning("GitHub request failed (status_code=%s)", response.status_code)
        if response.status_code == 401:
            raise GitHubAuthenticationError()
        if response.status_code in {403, 429}:
            raise GitHubAuthorizationError()
        if response.status_code == 404:
            if missing_is_not_found:
                raise GitHubNotFoundError()
            raise GitHubResponseError()
        if response.status_code >= 500:
            raise GitHubResponseError()
        if response.is_error:
            raise GitHubResponseError()
        try:
            return response.json()
        except ValueError as exc:
            raise GitHubResponseError() from exc

    @staticmethod
    def _parse_repository(item: object) -> GitHubRepository:
        if not isinstance(item, dict) or not isinstance(item.get("owner"), dict):
            raise GitHubResponseError()
        try:
            repository_id = item["id"]
            owner = item["owner"]["login"]
            name = item["name"]
            full_name = item["full_name"]
            default_branch = item["default_branch"]
            is_private = item["private"]
        except KeyError as exc:
            raise GitHubResponseError() from exc
        if (
            not isinstance(repository_id, int)
            or not all(
                isinstance(value, str) and value
                for value in (owner, name, full_name, default_branch)
            )
            or not isinstance(is_private, bool)
        ):
            raise GitHubResponseError()
        return GitHubRepository(repository_id, owner, name, full_name, default_branch, is_private)


def get_github_client() -> Generator[GitHubClient]:
    settings = get_settings()
    if settings.github_token is None or not settings.github_token.get_secret_value():
        raise GitHubConfigurationError()
    client = GitHubClient(
        settings.github_token.get_secret_value(),
        api_url=settings.github_api_url,
        connect_timeout=settings.github_connect_timeout_seconds,
        read_timeout=settings.github_read_timeout_seconds,
    )
    try:
        yield client
    finally:
        client.close()
