import base64

import httpx
import pytest

from app.clients.github import (
    GitHubAuthenticationError,
    GitHubAuthorizationError,
    GitHubClient,
    GitHubNotFoundError,
    GitHubRepository,
    GitHubResponseError,
)


def client_for(handler) -> GitHubClient:
    return GitHubClient("secret-token", transport=httpx.MockTransport(handler))


def test_lists_and_normalizes_repositories() -> None:
    client = client_for(
        lambda request: httpx.Response(
            200,
            json=[
                {
                    "id": 123,
                    "owner": {"login": "octo"},
                    "name": "demo",
                    "full_name": "octo/demo",
                    "default_branch": "main",
                    "private": False,
                }
            ],
        )
    )
    assert client.list_repositories() == [
        GitHubRepository(123, "octo", "demo", "octo/demo", "main", False)
    ]
    client.close()


def test_retrieves_base64_requirements() -> None:
    content = base64.b64encode(b"fastapi==1\n").decode()
    client = client_for(
        lambda request: httpx.Response(200, json={"encoding": "base64", "content": content})
    )
    repository = GitHubRepository(1, "octo", "demo", "octo/demo", "main", False)
    assert client.get_requirements_file(repository) == b"fastapi==1\n"
    client.close()


@pytest.mark.parametrize(
    ("status_code", "exception_type"),
    [
        (401, GitHubAuthenticationError),
        (403, GitHubAuthorizationError),
        (429, GitHubAuthorizationError),
        (500, GitHubResponseError),
    ],
)
def test_maps_github_failures(status_code: int, exception_type: type[Exception], caplog) -> None:
    client = client_for(lambda request: httpx.Response(status_code, text="token=secret"))
    with pytest.raises(exception_type):
        client.list_repositories()
    assert "secret-token" not in caplog.text
    assert "token=secret" not in caplog.text
    client.close()


def test_maps_timeout_and_malformed_response() -> None:
    def timeout(request):
        raise httpx.ReadTimeout("secret request details", request=request)

    timeout_client = client_for(timeout)
    with pytest.raises(GitHubResponseError):
        timeout_client.list_repositories()
    timeout_client.close()

    malformed_client = client_for(lambda request: httpx.Response(200, json={"unexpected": True}))
    with pytest.raises(GitHubResponseError):
        malformed_client.list_repositories()
    malformed_client.close()


def test_maps_missing_requirements_file() -> None:
    client = client_for(lambda request: httpx.Response(404, text="not found"))
    repository = GitHubRepository(1, "octo", "demo", "octo/demo", "main", False)
    with pytest.raises(GitHubNotFoundError):
        client.get_requirements_file(repository)
    client.close()
