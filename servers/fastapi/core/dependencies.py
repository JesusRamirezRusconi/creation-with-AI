"""Dependency injection configuration.

This module provides factory functions for creating service instances
with proper dependencies, following the Dependency Injection pattern.
"""

from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from domain.presentation.repositories import PresentationRepositoryProtocol
from infrastructure.repositories.presentation_repository import PresentationRepository
from infrastructure.services.export_service import ExportService
from infrastructure.services.presentation_generation_service import PresentationGenerationService
from infrastructure.services.presentation_service import PresentationService
from infrastructure.services.slide_generation_service import SlideGenerationService
from services.database import get_async_session
from services.image_generation_service import ImageGenerationService
from utils.asset_directory_utils import get_images_directory


# Repository factories
def get_presentation_repository(
    session: AsyncSession = Depends(get_async_session),
) -> PresentationRepositoryProtocol:
    """Get presentation repository instance.

    Args:
        session: Database session

    Returns:
        PresentationRepository instance
    """
    return PresentationRepository(session)


# Service factories
def get_presentation_service(
    repository: PresentationRepositoryProtocol = Depends(get_presentation_repository),
) -> PresentationService:
    """Get presentation service instance.

    Args:
        repository: Presentation repository

    Returns:
        PresentationService instance
    """
    return PresentationService(repository)


def get_presentation_generation_service(
    repository: PresentationRepositoryProtocol = Depends(get_presentation_repository),
    session: AsyncSession = Depends(get_async_session),
) -> PresentationGenerationService:
    """Get presentation generation service instance.

    Args:
        repository: Presentation repository
        session: Database session

    Returns:
        PresentationGenerationService instance
    """
    return PresentationGenerationService(repository, session)


def get_slide_generation_service() -> SlideGenerationService:
    """Get slide generation service instance.

    Returns:
        SlideGenerationService instance
    """
    image_service = ImageGenerationService(get_images_directory())
    return SlideGenerationService(image_service)


def get_export_service() -> ExportService:
    """Get export service instance.

    Returns:
        ExportService instance
    """
    return ExportService()
