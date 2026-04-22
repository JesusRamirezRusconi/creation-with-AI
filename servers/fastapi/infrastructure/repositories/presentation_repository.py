"""SQLAlchemy implementation of PresentationRepository.

This module implements the PresentationRepositoryProtocol using SQLAlchemy
for database operations.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from core.exceptions import PresentationNotFoundException
from core.logging import get_logger
from models.presentation_with_slides import PresentationWithSlides
from models.sql.image_asset import ImageAsset
from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel

logger = get_logger(__name__)


class PresentationRepository:
    """SQLAlchemy implementation of the presentation repository.
    
    This class handles all database operations for presentations,
    following the Repository pattern for clean separation of concerns.
    """

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    async def get_by_id(self, presentation_id: UUID) -> Optional[PresentationModel]:
        """Retrieve a presentation by its ID.

        Args:
            presentation_id: Unique identifier of the presentation

        Returns:
            PresentationModel if found, None otherwise
        """
        logger.debug(f"Fetching presentation with ID: {presentation_id}")
        presentation = await self.session.get(PresentationModel, presentation_id)
        
        if presentation:
            logger.info(f"Found presentation: {presentation_id}")
        else:
            logger.warning(f"Presentation not found: {presentation_id}")
            
        return presentation

    async def get_all_with_first_slide(self) -> List[PresentationWithSlides]:
        """Retrieve all presentations with their first slide.

        Returns:
            List of presentations with slides
        """
        logger.debug("Fetching all presentations with first slide")
        
        query = (
            select(PresentationModel, SlideModel)
            .join(
                SlideModel,
                (SlideModel.presentation == PresentationModel.id) & (SlideModel.index == 0),
            )
            .order_by(PresentationModel.created_at.desc())
        )

        results = await self.session.execute(query)
        rows = results.all()
        
        presentations_with_slides = [
            PresentationWithSlides(
                **presentation.model_dump(),
                slides=[first_slide],
            )
            for presentation, first_slide in rows
        ]
        
        logger.info(f"Retrieved {len(presentations_with_slides)} presentations")
        return presentations_with_slides

    async def get_with_slides(self, presentation_id: UUID) -> Optional[PresentationWithSlides]:
        """Retrieve a presentation with all its slides.

        Args:
            presentation_id: Unique identifier of the presentation

        Returns:
            PresentationWithSlides if found, None otherwise
        """
        logger.debug(f"Fetching presentation {presentation_id} with all slides")
        
        presentation = await self.get_by_id(presentation_id)
        if not presentation:
            return None

        slides = await self.get_slides(presentation_id)
        
        return PresentationWithSlides(
            **presentation.model_dump(),
            slides=slides,
        )

    async def create(self, presentation: PresentationModel) -> PresentationModel:
        """Create a new presentation.

        Args:
            presentation: Presentation model to create

        Returns:
            Created presentation model with ID
        """
        logger.info(f"Creating new presentation: {presentation.id}")
        
        self.session.add(presentation)
        await self.session.commit()
        await self.session.refresh(presentation)
        
        logger.info(f"Successfully created presentation: {presentation.id}")
        return presentation

    async def update(self, presentation: PresentationModel) -> PresentationModel:
        """Update an existing presentation.

        Args:
            presentation: Presentation model with updated data

        Returns:
            Updated presentation model
        """
        logger.info(f"Updating presentation: {presentation.id}")
        
        self.session.add(presentation)
        await self.session.commit()
        await self.session.refresh(presentation)
        
        logger.info(f"Successfully updated presentation: {presentation.id}")
        return presentation

    async def delete(self, presentation_id: UUID) -> None:
        """Delete a presentation by its ID.

        Args:
            presentation_id: Unique identifier of the presentation to delete

        Raises:
            PresentationNotFoundException: If presentation doesn't exist
        """
        logger.info(f"Deleting presentation: {presentation_id}")
        
        presentation = await self.get_by_id(presentation_id)
        if not presentation:
            raise PresentationNotFoundException(str(presentation_id))

        await self.session.delete(presentation)
        await self.session.commit()
        
        logger.info(f"Successfully deleted presentation: {presentation_id}")

    async def save_slides(self, slides: List[SlideModel]) -> None:
        """Save multiple slides to the database.

        Args:
            slides: List of slide models to save
        """
        logger.debug(f"Saving {len(slides)} slides")
        
        self.session.add_all(slides)
        await self.session.commit()
        
        logger.info(f"Successfully saved {len(slides)} slides")

    async def delete_slides(self, presentation_id: UUID) -> None:
        """Delete all slides associated with a presentation.

        Args:
            presentation_id: Unique identifier of the presentation
        """
        logger.debug(f"Deleting all slides for presentation: {presentation_id}")
        
        await self.session.execute(
            delete(SlideModel).where(SlideModel.presentation == presentation_id)
        )
        await self.session.commit()
        
        logger.info(f"Successfully deleted slides for presentation: {presentation_id}")

    async def delete_slides_by_ids(self, slide_ids: List[UUID]) -> None:
        """Delete specific slides by their IDs.

        Args:
            slide_ids: List of slide IDs to delete
        """
        logger.debug(f"Deleting {len(slide_ids)} specific slides")
        
        await self.session.execute(
            delete(SlideModel).where(SlideModel.id.in_(slide_ids))
        )
        await self.session.commit()
        
        logger.info(f"Successfully deleted {len(slide_ids)} slides")

    async def get_slides(self, presentation_id: UUID) -> List[SlideModel]:
        """Retrieve all slides for a presentation.

        Args:
            presentation_id: Unique identifier of the presentation

        Returns:
            List of slides ordered by index
        """
        logger.debug(f"Fetching slides for presentation: {presentation_id}")
        
        slides = await self.session.scalars(
            select(SlideModel)
            .where(SlideModel.presentation == presentation_id)
            .order_by(SlideModel.index)
        )
        
        slides_list = list(slides)
        logger.debug(f"Retrieved {len(slides_list)} slides")
        return slides_list

    async def save_assets(self, assets: List[ImageAsset]) -> None:
        """Save image assets to the database.

        Args:
            assets: List of image assets to save
        """
        logger.debug(f"Saving {len(assets)} image assets")
        
        self.session.add_all(assets)
        await self.session.commit()
        
        logger.info(f"Successfully saved {len(assets)} image assets")
