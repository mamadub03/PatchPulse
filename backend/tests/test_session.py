from sqlalchemy.exc import SQLAlchemyError

from app.db import session as db_session


class FakeSession:
    def __init__(self) -> None:
        self.rollback_called = False
        self.close_called = False

    def rollback(self) -> None:
        self.rollback_called = True

    def close(self) -> None:
        self.close_called = True


def test_session_dependency_provides_and_closes_session(monkeypatch) -> None:
    fake_session = FakeSession()
    monkeypatch.setattr(db_session, "get_session_factory", lambda: lambda: fake_session)

    session_generator = db_session.get_db_session()
    provided_session = next(session_generator)

    assert provided_session is fake_session

    try:
        next(session_generator)
    except StopIteration:
        pass

    assert fake_session.close_called is True
    assert fake_session.rollback_called is False


def test_session_dependency_rolls_back_database_errors(monkeypatch) -> None:
    fake_session = FakeSession()
    monkeypatch.setattr(db_session, "get_session_factory", lambda: lambda: fake_session)

    session_generator = db_session.get_db_session()
    next(session_generator)

    try:
        session_generator.throw(SQLAlchemyError("database work failed"))
    except SQLAlchemyError:
        pass

    assert fake_session.rollback_called is True
    assert fake_session.close_called is True
