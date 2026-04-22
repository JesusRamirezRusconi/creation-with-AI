"""Unit tests for domain validators."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from core.exceptions import (
    InsufficientSlidesForTOCException,
    InvalidPresentationRequestException,
    InvalidSlideCountException,
    TemplateNotFoundException,
)
from domain.presentation.validators import (
    validate_outlines,
    validate_presentation_id,
    validate_slides_count,
    validate_template_exists,
)
from constants.presentation import DEFAULT_TEMPLATES


class TestSlideCountValidation:
    """Test suite for slide count validation."""

    def test_valid_slide_count(self):
        """Test that valid slide count passes validation."""
        validate_slides_count(5)
        validate_slides_count(10, include_table_of_contents=False)

    def test_invalid_slide_count_below_minimum(self):
        """Test that slide count below minimum raises exception."""
        with pytest.raises(InvalidSlideCountException):
            validate_slides_count(0)
        
        with pytest.raises(InvalidSlideCountException):
            validate_slides_count(-1)

    def test_invalid_slide_count_above_maximum(self):
        """Test that slide count above maximum raises exception."""
        with pytest.raises(InvalidSlideCountException):
            validate_slides_count(101, max_slides=100)

    def test_insufficient_slides_for_toc(self):
        """Test that TOC with insufficient slides raises exception."""
        with pytest.raises(InsufficientSlidesForTOCException):
            validate_slides_count(2, include_table_of_contents=True)
        
        with pytest.raises(InsufficientSlidesForTOCException):
            validate_slides_count(1, include_table_of_contents=True)

    def test_valid_slides_for_toc(self):
        """Test that TOC with sufficient slides passes validation."""
        validate_slides_count(3, include_table_of_contents=True)
        validate_slides_count(10, include_table_of_contents=True)


class TestTemplateValidation:
    """Test suite for template validation."""

    @pytest.mark.asyncio
    async def test_valid_default_template(self):
        """Test that default template passes validation."""
        session = MagicMock()
        template_name = list(DEFAULT_TEMPLATES)[0] if DEFAULT_TEMPLATES else "general"
        
        await validate_template_exists(template_name, session)

    @pytest.mark.asyncio
    async def test_valid_custom_template(self):
        """Test that existing custom template passes validation."""
        session = AsyncMock()
        template_id = uuid4()
        
        mock_template = MagicMock()
        session.get = AsyncMock(return_value=mock_template)
        
        await validate_template_exists(f"custom-{template_id}", session)
        session.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalid_custom_template(self):
        """Test that non-existent custom template raises exception."""
        session = AsyncMock()
        template_id = uuid4()
        
        session.get = AsyncMock(return_value=None)
        
        with pytest.raises(TemplateNotFoundException):
            await validate_template_exists(f"custom-{template_id}", session)

    @pytest.mark.asyncio
    async def test_invalid_template_name(self):
        """Test that invalid template name raises exception."""
        session = MagicMock()
        
        with pytest.raises(TemplateNotFoundException):
            await validate_template_exists("nonexistent-template", session)


class TestPresentationIdValidation:
    """Test suite for presentation ID validation."""

    def test_valid_presentation_id(self):
        """Test that valid UUID passes validation."""
        presentation_id = uuid4()
        validate_presentation_id(presentation_id)

    def test_none_presentation_id(self):
        """Test that None raises exception."""
        with pytest.raises(InvalidPresentationRequestException):
            validate_presentation_id(None)


class TestOutlinesValidation:
    """Test suite for outlines validation."""

    def test_valid_outlines(self):
        """Test that valid outlines pass validation."""
        outlines = [{"content": "Slide 1"}, {"content": "Slide 2"}]
        validate_outlines(outlines)

    def test_empty_outlines(self):
        """Test that empty outlines raise exception."""
        with pytest.raises(InvalidPresentationRequestException):
            validate_outlines([])
