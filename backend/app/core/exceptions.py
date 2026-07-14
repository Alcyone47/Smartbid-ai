from fastapi import status


class AppException(Exception):
    """Base for domain exceptions that carry an HTTP status and a stable error_code."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, error_code: str | None = None, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code


class DocumentNotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "DOCUMENT_NOT_FOUND"

    def __init__(self, message: str = "Document not found") -> None:
        super().__init__(message)


class UnsupportedDocumentTypeError(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    error_code = "UNSUPPORTED_DOCUMENT_TYPE"


class DocumentParsingError(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    error_code = "DOCUMENT_PARSING_FAILED"


class LLMProviderError(AppException):
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "LLM_PROVIDER_ERROR"


class LLMRateLimitError(AppException):
    """Transient: the LLM provider returned HTTP 429 and in-call retries were exhausted.

    Carries the server-suggested wait (retryDelay/Retry-After) so the caller — the
    Celery task — can re-queue the job after that delay instead of failing it.
    """

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "LLM_RATE_LIMITED"

    def __init__(self, message: str = "LLM provider rate limit exceeded", retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ExtractionValidationError(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    error_code = "EXTRACTION_VALIDATION_FAILED"


class StorageError(AppException):
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "STORAGE_ERROR"
