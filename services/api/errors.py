"""Readable errors shared by the Python engine and HTTP handlers."""

from packages.schema.api import ErrorInfo, ErrorType


class PlatformError(Exception):
    def __init__(
        self, error_type: ErrorType, message: str, *, status_code: int = 422,
        line: int | None = None, details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.error = ErrorInfo(
            type=error_type, line=line, message=message, details=details or {},
        )
        self.status_code = status_code
