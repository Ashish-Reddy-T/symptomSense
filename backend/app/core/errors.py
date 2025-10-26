"""Centralised FastAPI exception handlers."""

from typing import Any

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = structlog.get_logger(__name__)


def _format_error(message: str, *, detail: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"error": message}
    if detail is not None:
        payload["detail"] = detail
    return payload


async def handle_validation_error(_: Request, exc: ValidationError) -> JSONResponse:
    logger.warning("validation_error", errors=exc.errors())
    return JSONResponse(
        status_code=422,
        content=_format_error("Validation error", detail=exc.errors()),
    )


async def handle_http_exception(_: Request, exc: HTTPException) -> JSONResponse:
    logger.warning("http_exception", status_code=exc.status_code, detail=exc.detail)
    return JSONResponse(status_code=exc.status_code, content=_format_error(str(exc.detail)))


async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("unexpected_error", error=str(exc))
    return JSONResponse(status_code=500, content=_format_error("Internal server error"))


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, handle_http_exception)
    app.add_exception_handler(ValidationError, handle_validation_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
