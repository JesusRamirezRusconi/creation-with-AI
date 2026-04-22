"""Custom exceptions for the presentation application.

This module defines domain-specific exceptions with unique error codes
for better error handling and client communication.
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException


class PresentationBaseException(Exception):
    """Base exception for all presentation-related errors."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail={
                "message": self.message,
                "error_code": self.error_code,
                "details": self.details,
            },
        )


class PresentationNotFoundException(PresentationBaseException):
    """Raised when a presentation is not found."""

    def __init__(self, presentation_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Presentation with ID '{presentation_id}' not found",
            error_code="PRESENTATION_NOT_FOUND",
            status_code=404,
            details=details or {"presentation_id": presentation_id},
        )


class InvalidPresentationRequestException(PresentationBaseException):
    """Raised when presentation request validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="INVALID_PRESENTATION_REQUEST",
            status_code=400,
            details=details,
        )


class PresentationGenerationException(PresentationBaseException):
    """Raised when presentation generation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="PRESENTATION_GENERATION_FAILED",
            status_code=500,
            details=details,
        )


class TemplateNotFoundException(PresentationBaseException):
    """Raised when a template is not found."""

    def __init__(self, template_name: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Template '{template_name}' not found",
            error_code="TEMPLATE_NOT_FOUND",
            status_code=404,
            details=details or {"template_name": template_name},
        )


class SlideGenerationException(PresentationBaseException):
    """Raised when slide generation fails."""

    def __init__(self, message: str, slide_index: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if slide_index is not None:
            details["slide_index"] = slide_index
        super().__init__(
            message=message,
            error_code="SLIDE_GENERATION_FAILED",
            status_code=500,
            details=details,
        )


class PresentationExportException(PresentationBaseException):
    """Raised when presentation export fails."""

    def __init__(self, message: str, export_format: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        if export_format:
            details["export_format"] = export_format
        super().__init__(
            message=message,
            error_code="PRESENTATION_EXPORT_FAILED",
            status_code=500,
            details=details,
        )


class InvalidSlideCountException(InvalidPresentationRequestException):
    """Raised when slide count is invalid."""

    def __init__(self, count: int, min_count: int = 1, max_count: Optional[int] = None):
        details = {"count": count, "min_count": min_count}
        if max_count:
            details["max_count"] = max_count
        
        message = f"Invalid slide count: {count}. Must be at least {min_count}"
        if max_count:
            message += f" and at most {max_count}"
        
        super().__init__(message=message, details=details)


class InsufficientSlidesForTOCException(InvalidPresentationRequestException):
    """Raised when table of contents is requested with insufficient slides."""

    def __init__(self, n_slides: int, minimum_required: int = 3):
        super().__init__(
            message=f"Table of contents requires at least {minimum_required} slides, got {n_slides}",
            details={"n_slides": n_slides, "minimum_required": minimum_required},
        )
