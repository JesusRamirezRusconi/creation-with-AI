"""Presentation service for CRUD operations.

This service handles basic CRUD operations for presentations,
delegating to the repository and adding business logic where needed.
"""

from typing import Dict, List, Optional
from uuid import UUID

from core.exceptions import PresentationNotFoundException
from core.logging import get_logger
from domain.presentation.repositories import PresentationRepositoryProtocol
from domain.presentation.validators import validate_presentation_id
from models.presentation_with_slides import PresentationWithSlides
from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel

logger = get_logger(__name__)


class PresentationService:
    """Service for presentation CRUD operations.
    
    This service orchestrates repository calls and applies business
    rules for presentation management.
    """

    def __init__(self, repository: PresentationRepositoryProtocol):
        """Initialize service with repository.

        Args:
            repository: Presentation repository implementation
        """
        self.repository = repository

    async def get_all_with_first_slide(self) -> List[PresentationWithSlides]:
        """Get all presentations with their first slide.

        Returns:
            List of presentations with first slide
        """
        logger.info("Fetching all presentations")
        return await self.repository.get_all_with_first_slide()

    async def get_by_id(self, presentation_id: UUID) -> PresentationWithSlides:
        """Get a presentation by ID with all slides.

        Args:
            presentation_id: Unique identifier of the presentation

        Returns:
            Presentation with all slides

        Raises:
            PresentationNotFoundException: If presentation not found
        """
        logger.info(f"Fetching presentation: {presentation_id}")
        validate_presentation_id(presentation_id)
        
        presentation = await self.repository.get_with_slides(presentation_id)
        
        if not presentation:
            raise PresentationNotFoundException(str(presentation_id))
        
        return presentation

    async def create(self, presentation: PresentationModel) -> PresentationModel:
        """Create a new presentation.

        Args:
            presentation: Presentation model to create

        Returns:
            Created presentation
        """
        logger.info(f"Creating presentation: {presentation.id}")
        return await self.repository.create(presentation)

    async def update(
        self,
        presentation_id: UUID,
        n_slides: Optional[int] = None,
        title: Optional[str] = None,
    ) -> PresentationWithSlides:
        """Update presentation metadata.

        Args:
            presentation_id: ID of presentation to update
            n_slides: New number of slides (optional)
            title: New title (optional)

        Returns:
            Updated presentation with slides

        Raises:
            PresentationNotFoundException: If presentation not found
        """
        logger.info(f"Updating presentation: {presentation_id}")
        validate_presentation_id(presentation_id)
        
        presentation = await self.repository.get_by_id(presentation_id)
        if not presentation:
            raise PresentationNotFoundException(str(presentation_id))
        
        # Build update dictionary
        update_dict: Dict[str, any] = {}
        if n_slides is not None:
            update_dict["n_slides"] = n_slides
        if title is not None:
            update_dict["title"] = title
        
        if update_dict:
            presentation.sqlmodel_update(update_dict)
            await self.repository.update(presentation)
        
        return await self.get_by_id(presentation_id)

    async def update_slides(
        self,
        presentation_id: UUID,
        slides: List[SlideModel],
    ) -> PresentationWithSlides:
        """Update slides for a presentation.

        Args:
            presentation_id: ID of presentation
            slides: New slides to save

        Returns:
            Updated presentation with new slides

        Raises:
            PresentationNotFoundException: If presentation not found
        """
        logger.info(f"Updating {len(slides)} slides for presentation: {presentation_id}")
        validate_presentation_id(presentation_id)
        
        # Verify presentation exists
        presentation = await self.repository.get_by_id(presentation_id)
        if not presentation:
            raise PresentationNotFoundException(str(presentation_id))
        
        # Ensure slide IDs are UUIDs
        for slide in slides:
            slide.presentation = presentation_id
            if isinstance(slide.id, str):
                slide.id = UUID(slide.id)
        
        # Delete old slides and save new ones
        await self.repository.delete_slides(presentation_id)
        await self.repository.save_slides(slides)
        
        return await self.get_by_id(presentation_id)

    async def delete(self, presentation_id: UUID) -> None:
        """Delete a presentation.

        Args:
            presentation_id: ID of presentation to delete

        Raises:
            PresentationNotFoundException: If presentation not found
        """
        logger.info(f"Deleting presentation: {presentation_id}")
        validate_presentation_id(presentation_id)
        
        await self.repository.delete(presentation_id)
        
        logger.info(f"Successfully deleted presentation: {presentation_id}")
