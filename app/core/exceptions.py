"""
Global exception handlers for standardized error responses.

All API errors return a consistent JSON structure:
{
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable message",
        "details": {}  // optional
    }
}
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError

from app.core.logging import get_logger

logger = get_logger(__name__)


def _error_response(status_code: int, code: str, message: str, details: dict | None = None) -> JSONResponse:
    """Build a standardized error response."""
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Catches Pydantic validation errors and returns a clean 422."""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": " → ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            })
        logger.warning("Validation error on %s: %s", request.url.path, errors)
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="The request data is invalid.",
            details={"errors": errors},
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
        """Catches DB constraint violations (duplicate entries, etc.)."""
        logger.error("Database integrity error: %s", str(exc.orig))
        return _error_response(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message="A resource with this data already exists.",
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unhandled exceptions. Logs the full traceback."""
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_ERROR",
            message="An unexpected error occurred. Please try again later.",
        )
