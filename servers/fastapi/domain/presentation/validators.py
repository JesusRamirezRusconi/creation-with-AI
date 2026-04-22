"""Domain validators for presentation business rules.

This module contains validation logic for presentation-related operations,
ensuring business rules are enforced before data reaches the repository layer.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from constants.presentation import DEFAULT_TEMPLATES
from core.exceptions import (
    InsufficientSlidesForTOCException,
    InvalidPresentationRequestException,
    InvalidSlideCountException,
    TemplateNotFoundException,
)
from core.logging import get_logger
from models.generate_presentation_request import GeneratePresentationRequest
from models.sql.template import TemplateModel

logger = get_logger(__name__)


async def validate_presentation_request(
    request: GeneratePresentationRequest,
    session: AsyncSession,
) -> None:
    """Validate a presentation generation request.

    Args:
        request: Presentation generation request to validate
        session: Database session for template validation

    Raises:
        InvalidPresentationRequestException: If request validation fails
        TemplateNotFoundException: If template is not found
    """
    logger.debug("Validating presentation request")

    # Validate that at least one content source is provided
    if not (request.content or request.slides_markdown or request.files):
        logger.error("No content source provided in request")
        raise InvalidPresentationRequestException(
            "Either content, slides_markdown, or files must be provided",
            details={
                "has_content": bool(request.content),
                "has_slides_markdown": bool(request.slides_markdown),
                "has_files": bool(request.files),
            },
        )

    # Validate slide count
    validate_slides_count(request.n_slides, request.include_table_of_contents)

    # Validate template
    await validate_template_exists(request.template, session)

    logger.info("Presentation request validation successful")


def validate_slides_count(
    n_slides: int,
    include_table_of_contents: bool = False,
    min_slides: int = 1,
    max_slides: Optional[int] = None,
) -> None:
    """Validate the number of slides in a presentation.

    Args:
        n_slides: Number of slides requested
        include_table_of_contents: Whether table of contents is included
        min_slides: Minimum number of slides allowed
        max_slides: Maximum number of slides allowed (None for unlimited)

    Raises:
        InvalidSlideCountException: If slide count is invalid
        InsufficientSlidesForTOCException: If TOC requires more slides
    """
    logger.debug(f"Validating slide count: {n_slides}")

    # Check minimum
    if n_slides < min_slides:
        logger.error(f"Slide count {n_slides} below minimum {min_slides}")
        raise InvalidSlideCountException(n_slides, min_slides, max_slides)

    # Check maximum if specified
    if max_slides and n_slides > max_slides:
        logger.error(f"Slide count {n_slides} exceeds maximum {max_slides}")
        raise InvalidSlideCountException(n_slides, min_slides, max_slides)

    # Check table of contents requirements
    if include_table_of_contents and n_slides < 3:
        logger.error("Table of contents requires at least 3 slides")
        raise InsufficientSlidesForTOCException(n_slides, minimum_required=3)

    logger.debug("Slide count validation successful")


async def validate_template_exists(template_name: str, session: AsyncSession) -> None:
    """Validate that a template exists.

    Args:
        template_name: Name of the template to validate
        session: Database session for custom template lookup

    Raises:
        TemplateNotFoundException: If template doesn't exist
    """
    logger.debug(f"Validating template: {template_name}")

    # Check default templates
    if template_name in DEFAULT_TEMPLATES:
        logger.debug(f"Template '{template_name}' found in default templates")
        return

    # Check custom templates
    template_name_lower = template_name.lower()
    if template_name_lower.startswith("custom-"):
        template_id_str = template_name_lower.replace("custom-", "")
        
        try:
            template_id = UUID(template_id_str)
            template = await session.get(TemplateModel, template_id)
            
            if template:
                logger.debug(f"Custom template found: {template_id}")
                return
            else:
                logger.error(f"Custom template not found: {template_id}")
                raise TemplateNotFoundException(
                    template_name,
                    details={"template_id": template_id_str},
                )
        except ValueError:
            logger.error(f"Invalid template ID format: {template_id_str}")
            raise TemplateNotFoundException(
                template_name,
                details={"template_id": template_id_str, "error": "Invalid UUID format"},
            )

    # Template not found
    logger.error(f"Template not found: {template_name}")
    raise TemplateNotFoundException(
        template_name,
        details={"available_defaults": list(DEFAULT_TEMPLATES)},
    )


def validate_presentation_id(presentation_id: Optional[UUID]) -> None:
    """Validate a presentation ID.

    Args:
        presentation_id: Presentation ID to validate

    Raises:
        InvalidPresentationRequestException: If ID is invalid
    """
    if not presentation_id:
        logger.error("Presentation ID is None")
        raise InvalidPresentationRequestException(
            "Presentation ID is required",
            details={"presentation_id": str(presentation_id)},
        )

    logger.debug(f"Presentation ID validation successful: {presentation_id}")


def validate_outlines(outlines: List[dict]) -> None:
    """Validate presentation outlines.

    Args:
        outlines: List of outline dictionaries

    Raises:
        InvalidPresentationRequestException: If outlines are invalid
    """
    if not outlines:
        logger.error("Outlines list is empty")
        raise InvalidPresentationRequestException(
            "At least one outline is required",
            details={"outlines_count": 0},
        )

    logger.debug(f"Outlines validation successful: {len(outlines)} outlines")
