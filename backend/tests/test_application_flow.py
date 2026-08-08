from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_current_user
from app.api.routes.repositories import github_dependency, osv_dependency
from app.clients.github import GitHubNotFoundError, GitHubRepository, GitHubResponseError
from app.clients.osv import OsvError, OsvVulnerability
from app.db.base import Base
from app.db.session import get_db_session
from app.main import create_app
from app.models import Repository, Scan, ScanStatus, User
from app.services.repositories import synchronize_repositories
from app.services.scans import ScanAlreadyRunningError, start_scan


class FakeGitHub:
    def __init__(self, repositories=None, content=b"fastapi==1\n", failure=None) -> None:
        self.repositories = repositories or []
        self.content = content
        self.failure = failure

    def list_repositories(self):
        if self.failure:
            raise self.failure
        return self.repositories

    def get_requirements_file(self, repository):
        if self.failure:
            raise self.failure
        return self.content


class FakeOsv:
    def __init__(self, results=None, failure=None):
        self.results, self.failure = results, failure

    def query_batch(self, dependencies):
        if self.failure:
            raise self.failure
        return self.results if self.results is not None else [[] for item in dependencies]


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, record) -> None:
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as database_session:
        yield database_session
    Base.metadata.drop_all(engine)


def make_repository(user: User, github_id: int, name: str = "demo") -> Repository:
    return Repository(
        user=user,
        github_repository_id=github_id,
        owner="octo",
        name=name,
        full_name=f"octo/{name}",
        default_branch="main",
        is_private=False,
    )


def test_sync_creates_updates_and_is_idempotent(session: Session) -> None:
    user = User(email="a@example.com")
    session.add(user)
    session.commit()
    github = FakeGitHub([GitHubRepository(10, "octo", "demo", "octo/demo", "main", False)])

    first = synchronize_repositories(session, user, github)
    second = synchronize_repositories(session, user, github)
    github.repositories[0] = GitHubRepository(10, "octo", "renamed", "octo/renamed", "trunk", True)
    third = synchronize_repositories(session, user, github)

    assert (
        first.repositories_created,
        second.repositories_created,
        third.repositories_updated,
    ) == (1, 0, 1)
    repositories = list(session.scalars(select(Repository)))
    assert len(repositories) == 1
    assert repositories[0].full_name == "octo/renamed"
    assert repositories[0].id is not None


@pytest.mark.parametrize(
    ("github", "expected_status", "error_code"),
    [
        (FakeGitHub(), ScanStatus.COMPLETED, None),
        (FakeGitHub(failure=GitHubNotFoundError()), ScanStatus.FAILED, "requirements_file_missing"),
        (FakeGitHub(failure=GitHubResponseError()), ScanStatus.FAILED, "github_unavailable"),
    ],
)
def test_scan_lifecycle_persists_history(
    session: Session,
    github: FakeGitHub,
    expected_status: ScanStatus,
    error_code: str | None,
) -> None:
    user = User(email="a@example.com")
    repository = make_repository(user, 10)
    session.add(repository)
    session.commit()

    scan = start_scan(session, user, repository.id, github, 1_000_000)

    assert scan.status == expected_status
    assert scan.completed_at is not None
    assert scan.error_code == error_code
    assert session.scalar(select(Scan).where(Scan.id == scan.id)) is not None


def test_api_enforces_repository_and_scan_ownership(session: Session) -> None:
    user_a = User(email="a@example.com")
    user_b = User(email="b@example.com")
    repository_a = make_repository(user_a, 10, "a")
    repository_b = make_repository(user_b, 20, "b")
    scan_b = Scan(
        repository=repository_b,
        status=ScanStatus.COMPLETED,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
    session.add_all([repository_a, repository_b, scan_b])
    session.commit()

    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: user_a
    app.dependency_overrides[github_dependency] = lambda: FakeGitHub()
    app.dependency_overrides[osv_dependency] = lambda: FakeOsv()
    client = TestClient(app)

    repositories = client.get("/api/v1/repositories")
    forbidden_scan = client.post(f"/api/v1/repositories/{repository_b.id}/scans")
    forbidden_history = client.get(f"/api/v1/scans/{scan_b.id}")

    assert repositories.status_code == 200
    assert [item["full_name"] for item in repositories.json()] == ["octo/a"]
    assert forbidden_scan.status_code == 404
    assert forbidden_scan.json() == {"detail": "Repository not found"}
    assert forbidden_history.status_code == 404
    assert forbidden_history.json() == {"detail": "Scan not found"}


def test_request_data_cannot_override_current_user(session: Session) -> None:
    user_a = User(email="a@example.com")
    user_b = User(email="b@example.com")
    repository_b = make_repository(user_b, 20, "b")
    session.add_all([user_a, repository_b])
    session.commit()
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: user_a
    app.dependency_overrides[github_dependency] = lambda: FakeGitHub()
    app.dependency_overrides[osv_dependency] = lambda: FakeOsv()
    client = TestClient(app)

    response = client.post(
        f"/api/v1/repositories/{repository_b.id}/scans",
        json={"user_id": str(user_b.id)},
        headers={"X-User-Id": str(user_b.id)},
    )
    assert response.status_code == 404


def test_application_flow_endpoints_return_safe_schemas(session: Session) -> None:
    user = User(email="a@example.com")
    session.add(user)
    session.commit()
    github = FakeGitHub([GitHubRepository(10, "octo", "demo", "octo/demo", "main", False)])
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[github_dependency] = lambda: github
    app.dependency_overrides[osv_dependency] = lambda: FakeOsv()
    client = TestClient(app)

    sync_response = client.post("/api/v1/repositories/sync")
    repositories_response = client.get("/api/v1/repositories")
    repository_id = repositories_response.json()[0]["id"]
    start_response = client.post(f"/api/v1/repositories/{repository_id}/scans")
    scans_response = client.get("/api/v1/scans")
    scan_response = client.get(f"/api/v1/scans/{start_response.json()['id']}")

    assert sync_response.json() == {
        "repositories_discovered": 1,
        "repositories_created": 1,
        "repositories_updated": 0,
    }
    assert repositories_response.status_code == 200
    assert start_response.status_code == 201
    assert start_response.json()["status"] == "completed"
    assert start_response.json()["repository_full_name"] == "octo/demo"
    assert scans_response.status_code == 200
    assert scans_response.json()[0]["id"] == start_response.json()["id"]
    assert scan_response.status_code == 200
    assert scan_response.json()["id"] == scans_response.json()[0]["id"]


def test_vulnerability_results_persist_and_raw_data_is_filtered(session: Session) -> None:
    user = User(email="findings@example.com")
    repository = make_repository(user, 90, "vulnerable")
    session.add(repository)
    session.commit()
    vulnerability = OsvVulnerability(
        "OSV-1", "Issue", "internal", None, "https://example.test", "2.0", {"secret_raw": True}
    )
    scan = start_scan(
        session,
        user,
        repository.id,
        FakeGitHub(content=b"Demo_Pkg==1.0\nrange>=2\n"),
        1_000_000,
        FakeOsv([[vulnerability]]),
    )
    assert scan.status == ScanStatus.COMPLETED_WITH_WARNINGS
    app = create_app()
    app.dependency_overrides[get_db_session] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: user
    response = TestClient(app).get(f"/api/v1/scans/{scan.id}")
    assert response.json()["finding_count"] == 1
    assert response.json()["unsupported_count"] == 1
    assert "raw_osv_data" not in response.text
    assert "secret_raw" not in response.text


def test_osv_failure_never_completes_scan(session: Session) -> None:
    user = User(email="osv@example.com")
    repository = make_repository(user, 91)
    session.add(repository)
    session.commit()
    scan = start_scan(
        session,
        user,
        repository.id,
        FakeGitHub(content=b"demo==1\n"),
        1_000_000,
        FakeOsv(failure=OsvError()),
    )
    assert scan.status == ScanStatus.FAILED
    assert scan.error_code == "osv_unavailable"


def test_second_running_scan_is_rejected(session: Session) -> None:
    user = User(email="running@example.com")
    repository = make_repository(user, 92)
    session.add(repository)
    session.commit()
    session.add(
        Scan(repository_id=repository.id, status=ScanStatus.RUNNING, started_at=datetime.now(UTC))
    )
    session.commit()
    with pytest.raises(ScanAlreadyRunningError):
        start_scan(session, user, repository.id, FakeGitHub(), 1_000_000, FakeOsv())
