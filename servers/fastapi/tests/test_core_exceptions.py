"""Unit tests for core exceptions."""

import pytest
from uuid import uuid4

from core.exceptions import (
    InsufficientSlidesForTOCException,
    InvalidPresentationRequestException,
    InvalidSlideCountException,
    PresentationExportException,
    PresentationGenerationException,
    PresentationNotFoundException,
    SlideGenerationException,
    TemplateNotFoundException,
)


class TestPresentationExceptions:
    """Test suite for presentation exceptions."""

    def test_presentation_not_found_exception(self):
        """Test PresentationNotFoundException creation and properties."""
        presentation_id = str(uuid4())
        exception = PresentationNotFoundException(presentation_id)
        
        assert exception.status_code == 404
        assert exception.error_code == "PRESENTATION_NOT_FOUND"
        assert presentation_id in exception.message
        assert exception.details["presentation_id"] == presentation_id

    def test_invalid_presentation_request_exception(self):
        """Test InvalidPresentationRequestException with custom details."""
        details = {"field": "content", "reason": "empty"}
        exception = InvalidPresentationRequestException(
            "Content is required",
            details=details,
        )
        
        assert exception.status_code == 400
        assert exception.error_code == "INVALID_PRESENTATION_REQUEST"
        assert exception.details == details

    def test_presentation_generation_exception(self):
        """Test PresentationGenerationException."""
        exception = PresentationGenerationException(
            "LLM service unavailable",
            details={"provider": "openai"},
        )
        
        assert exception.status_code == 500
        assert exception.error_code == "PRESENTATION_GENERATION_FAILED"
        assert exception.details["provider"] == "openai"

    def test_template_not_found_exception(self):
        """Test TemplateNotFoundException."""
        template_name = "custom-123"
        exception = TemplateNotFoundException(template_name)
        
        assert exception.status_code == 404
        assert exception.error_code == "TEMPLATE_NOT_FOUND"
        assert template_name in exception.message

    def test_invalid_slide_count_exception(self):
        """Test InvalidSlideCountException with min/max."""
        exception = InvalidSlideCountException(0, min_count=1, max_count=100)
        
        assert exception.status_code == 400
        assert exception.details["count"] == 0
        assert exception.details["min_count"] == 1
        assert exception.details["max_count"] == 100

    def test_insufficient_slides_for_toc_exception(self):
        """Test InsufficientSlidesForTOCException."""
        exception = InsufficientSlidesForTOCException(n_slides=2, minimum_required=3)
        
        assert exception.status_code == 400
        assert exception.details["n_slides"] == 2
        assert exception.details["minimum_required"] == 3

    def test_to_http_exception_conversion(self):
        """Test conversion to FastAPI HTTPException."""
        exception = PresentationNotFoundException(str(uuid4()))
        http_exception = exception.to_http_exception()
        
        assert http_exception.status_code == 404
        assert "error_code" in http_exception.detail
        assert http_exception.detail["error_code"] == "PRESENTATION_NOT_FOUND"
