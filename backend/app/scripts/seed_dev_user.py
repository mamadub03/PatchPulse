from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import get_session_factory
from app.models import User


def main() -> None:
    settings = get_settings()
    with get_session_factory()() as session:
        user = session.scalar(select(User).where(User.email == settings.dev_user_email))
        if user is None:
            session.add(User(email=settings.dev_user_email))
            session.commit()
            print("Development user created.")
        else:
            print("Development user already exists.")


if __name__ == "__main__":
    main()
