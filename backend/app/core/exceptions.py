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


class ExtractionValidationError(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    error_code = "EXTRACTION_VALIDATION_FAILED"


class StorageError(AppException):
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "STORAGE_ERROR"
