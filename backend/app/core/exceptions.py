"""Application-level exceptions with error codes for the response envelope."""
from __future__ import annotations


class AppError(Exception):
    """Base application error mapped to the error response envelope."""

    status_code: int = 400
    code: str = "APP_ERROR"

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None):
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"


class AuthenticationError(AppError):
    status_code = 401
    code = "UNAUTHENTICATED"


class PermissionDeniedError(AppError):
    status_code = 403
    code = "PERMISSION_DENIED"


class ValidationError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"
