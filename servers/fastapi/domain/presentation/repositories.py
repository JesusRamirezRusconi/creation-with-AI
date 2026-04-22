"""Repository interfaces for presentation domain.

This module defines the protocol (interface) for presentation repositories,
following the Repository pattern and Dependency Inversion Principle.
"""

from typing import List, Optional, Protocol
from uuid import UUID

from models.presentation_with_slides import PresentationWithSlides
from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel
from models.sql.image_asset import ImageAsset


class PresentationRepositoryProtocol(Protocol):
    """Protocol defining the interface for presentation repositories.
    
    This follows the Repository pattern, providing an abstraction layer
    between the domain logic and data access logic.
    """

    async def get_by_id(self, presentation_id: UUID) -> Optional[PresentationModel]:
        """Retrieve a presentation by its ID.

        Args:
            presentation_id: Unique identifier of the presentation

        Returns:
            PresentationModel if found, None otherwise
        """
        ...

    async def get_all_with_first_slide(self) -> List[PresentationWithSlides]:
        """Retrieve all presentations with their first slide.

        Returns:
            List of presentations with slides
        """
        ...

    async def get_with_slides(self, presentation_id: UUID) -> Optional[PresentationWithSlides]:
        """Retrieve a presentation with all its slides.

        Args:
            presentation_id: Unique identifier of the presentation

        Returns:
            PresentationWithSlides if found, None otherwise
        """
        ...

    async def create(self, presentation: PresentationModel) -> PresentationModel:
        """Create a new presentation.

        Args:
            presentation: Presentation model to create

        Returns:
            Created presentation model with ID
        """
        ...

    async def update(self, presentation: PresentationModel) -> PresentationModel:
        """Update an existing presentation.

        Args:
            presentation: Presentation model with updated data

        Returns:
            Updated presentation model
        """
        ...

    async def delete(self, presentation_id: UUID) -> None:
        """Delete a presentation by its ID.

        Args:
            presentation_id: Unique identifier of the presentation to delete
        """
        ...

    async def save_slides(self, slides: List[SlideModel]) -> None:
        """Save multiple slides to the database.

        Args:
            slides: List of slide models to save
        """
        ...

    async def delete_slides(self, presentation_id: UUID) -> None:
        """Delete all slides associated with a presentation.

        Args:
            presentation_id: Unique identifier of the presentation
        """
        ...

    async def delete_slides_by_ids(self, slide_ids: List[UUID]) -> None:
        """Delete specific slides by their IDs.

        Args:
            slide_ids: List of slide IDs to delete
        """
        ...

    async def get_slides(self, presentation_id: UUID) -> List[SlideModel]:
        """Retrieve all slides for a presentation.

        Args:
            presentation_id: Unique identifier of the presentation

        Returns:
            List of slides ordered by index
        """
        ...

    async def save_assets(self, assets: List[ImageAsset]) -> None:
        """Save image assets to the database.

        Args:
            assets: List of image assets to save
        """
        ...
