from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError, StatementError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models import Repository, Scan, ScanStatus, User


@pytest.fixture
def sqlite_session() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


def test_user_email_is_unique(sqlite_session: Session) -> None:
    sqlite_session.add_all([User(email="owner@example.com"), User(email="owner@example.com")])

    with pytest.raises(IntegrityError):
        sqlite_session.commit()


def test_repository_has_user_foreign_key_and_uniqueness_constraint() -> None:
    foreign_keys = Repository.__table__.c.user_id.foreign_keys
    unique_constraints = {
        constraint.name: tuple(column.name for column in constraint.columns)
        for constraint in Repository.__table__.constraints
    }

    assert {foreign_key.target_fullname for foreign_key in foreign_keys} == {"users.id"}
    assert unique_constraints["uq_repositories_user_id_github_repository_id"] == (
        "user_id",
        "github_repository_id",
    )


def test_repository_uniqueness_is_scoped_to_user(sqlite_session: Session) -> None:
    user = User(email="owner@example.com")
    sqlite_session.add(user)
    sqlite_session.flush()

    sqlite_session.add_all(
        [
            Repository(
                user_id=user.id,
                github_repository_id=123456789012,
                owner="octo",
                name="patchpulse",
                full_name="octo/patchpulse",
                default_branch="main",
                is_private=False,
            ),
            Repository(
                user_id=user.id,
                github_repository_id=123456789012,
                owner="octo",
                name="patchpulse",
                full_name="octo/patchpulse",
                default_branch="main",
                is_private=False,
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        sqlite_session.commit()


def test_scan_metadata_and_nullable_fields(sqlite_session: Session) -> None:
    user = User(email="owner@example.com")
    repository = Repository(
        user=user,
        github_repository_id=123456789012,
        owner="octo",
        name="patchpulse",
        full_name="octo/patchpulse",
        default_branch="main",
        is_private=False,
    )
    scan = Scan(
        repository=repository,
        status=ScanStatus.RUNNING,
        started_at=datetime.now(UTC),
    )

    sqlite_session.add(scan)
    sqlite_session.commit()

    assert scan.error_code is None
    assert scan.error_message is None
    assert scan.completed_at is None
    assert scan.repository_id == repository.id
    assert scan.repository.user == user


def test_scan_has_repository_foreign_key() -> None:
    foreign_keys = Scan.__table__.c.repository_id.foreign_keys

    assert {foreign_key.target_fullname for foreign_key in foreign_keys} == {"repositories.id"}


def test_scan_status_accepts_only_defined_values(sqlite_session: Session) -> None:
    user = User(email="owner@example.com")
    repository = Repository(
        user=user,
        github_repository_id=123456789012,
        owner="octo",
        name="patchpulse",
        full_name="octo/patchpulse",
        default_branch="main",
        is_private=False,
    )
    scan = Scan(
        repository=repository,
        status="queued",
        started_at=datetime.now(UTC),
    )

    sqlite_session.add(scan)

    with pytest.raises((IntegrityError, StatementError)):
        sqlite_session.commit()
