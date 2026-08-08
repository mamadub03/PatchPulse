import uuid

from pydantic import BaseModel, ConfigDict


class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    github_repository_id: int
    owner: str
    name: str
    full_name: str
    default_branch: str
    is_private: bool


class RepositorySyncResponse(BaseModel):
    repositories_discovered: int
    repositories_created: int
    repositories_updated: int
