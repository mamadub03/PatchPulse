import logging

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.session import check_database_connection, get_db_session
from app.schemas.readiness import ReadinessResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["readiness"])
SessionDependency = Depends(get_db_session)


@router.get(
    "/readiness",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
)
def read_readiness(session: Session = SessionDependency) -> ReadinessResponse | JSONResponse:
    try:
        check_database_connection(session)
    except SQLAlchemyError:
        logger.warning("Database readiness check failed", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ReadinessResponse(status="not_ready", database="unavailable").model_dump(),
        )

    return ReadinessResponse(status="ready", database="connected")
