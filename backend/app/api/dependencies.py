from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.models import User

DatabaseSession = Annotated[Session, Depends(get_db_session)]
AppSettings = Annotated[Settings, Depends(get_settings)]


def get_current_user(session: DatabaseSession, settings: AppSettings) -> User:
    """Resolve the temporary server-controlled identity used by the local MVP.

    Identity deliberately comes from backend configuration, never request data. Real
    authentication can replace this dependency without changing ownership-aware routes.
    """
    user = session.scalar(select(User).where(User.email == settings.dev_user_email))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Development user is not initialized",
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
