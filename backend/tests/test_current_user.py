from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.base import Base
from app.models import User


def test_configured_development_user_resolves() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add(User(email="dev@example.com"))
        session.commit()
        user = get_current_user(session, SimpleNamespace(dev_user_email="dev@example.com"))
        assert user.email == "dev@example.com"


def test_missing_development_user_fails_safely() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session, pytest.raises(HTTPException) as exc_info:
        get_current_user(session, SimpleNamespace(dev_user_email="missing@example.com"))
    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "Development user is not initialized"
