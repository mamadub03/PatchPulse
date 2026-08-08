import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.github import GitHubClient
from app.models import Repository, User


@dataclass(frozen=True)
class SyncResult:
    repositories_discovered: int
    repositories_created: int
    repositories_updated: int


def list_user_repositories(session: Session, user: User) -> list[Repository]:
    return list(
        session.scalars(
            select(Repository).where(Repository.user_id == user.id).order_by(Repository.full_name)
        )
    )


def get_user_repository(
    session: Session, user: User, repository_id: uuid.UUID
) -> Repository | None:
    return session.scalar(
        select(Repository).where(
            Repository.id == repository_id,
            Repository.user_id == user.id,
        )
    )


def synchronize_repositories(session: Session, user: User, github: GitHubClient) -> SyncResult:
    discovered = github.list_repositories()
    existing = {
        repository.github_repository_id: repository
        for repository in session.scalars(select(Repository).where(Repository.user_id == user.id))
    }
    created = 0
    updated = 0
    for github_repository in discovered:
        repository = existing.get(github_repository.github_repository_id)
        if repository is None:
            session.add(
                Repository(
                    user_id=user.id,
                    github_repository_id=github_repository.github_repository_id,
                    owner=github_repository.owner,
                    name=github_repository.name,
                    full_name=github_repository.full_name,
                    default_branch=github_repository.default_branch,
                    is_private=github_repository.is_private,
                )
            )
            created += 1
            continue
        mutable_values = (
            github_repository.owner,
            github_repository.name,
            github_repository.full_name,
            github_repository.default_branch,
            github_repository.is_private,
        )
        current_values = (
            repository.owner,
            repository.name,
            repository.full_name,
            repository.default_branch,
            repository.is_private,
        )
        if mutable_values != current_values:
            (
                repository.owner,
                repository.name,
                repository.full_name,
                repository.default_branch,
                repository.is_private,
            ) = mutable_values
            updated += 1
    session.commit()
    return SyncResult(len(discovered), created, updated)
