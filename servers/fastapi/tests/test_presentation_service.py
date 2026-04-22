"""Unit tests for PresentationService."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from core.exceptions import PresentationNotFoundException
from infrastructure.services.presentation_service import PresentationService
from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel


class TestPresentationService:
    """Test suite for PresentationService."""

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_repository):
        """Create service with mock repository."""
        return PresentationService(mock_repository)

    @pytest.mark.asyncio
    async def test_get_all_with_first_slide(self, service, mock_repository):
        """Test getting all presentations."""
        mock_presentations = [MagicMock(), MagicMock()]
        mock_repository.get_all_with_first_slide.return_value = mock_presentations
        
        result = await service.get_all_with_first_slide()
        
        assert result == mock_presentations
        mock_repository.get_all_with_first_slide.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, service, mock_repository):
        """Test getting presentation by ID successfully."""
        presentation_id = uuid4()
        mock_presentation = MagicMock()
        mock_repository.get_with_slides.return_value = mock_presentation
        
        result = await service.get_by_id(presentation_id)
        
        assert result == mock_presentation
        mock_repository.get_with_slides.assert_called_once_with(presentation_id)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, service, mock_repository):
        """Test getting non-existent presentation raises exception."""
        presentation_id = uuid4()
        mock_repository.get_with_slides.return_value = None
        
        with pytest.raises(PresentationNotFoundException):
            await service.get_by_id(presentation_id)

    @pytest.mark.asyncio
    async def test_create_presentation(self, service, mock_repository):
        """Test creating a new presentation."""
        presentation = PresentationModel(
            id=uuid4(),
            content="Test",
            n_slides=5,
            language="en",
        )
        mock_repository.create.return_value = presentation
        
        result = await service.create(presentation)
        
        assert result == presentation
        mock_repository.create.assert_called_once_with(presentation)

    @pytest.mark.asyncio
    async def test_delete_presentation_success(self, service, mock_repository):
        """Test deleting an existing presentation."""
        presentation_id = uuid4()
        
        await service.delete(presentation_id)
        
        mock_repository.delete.assert_called_once_with(presentation_id)

    @pytest.mark.asyncio
    async def test_update_presentation(self, service, mock_repository):
        """Test updating presentation metadata."""
        presentation_id = uuid4()
        mock_presentation = MagicMock()
        mock_presentation.id = presentation_id
        
        mock_repository.get_by_id.return_value = mock_presentation
        mock_repository.get_with_slides.return_value = MagicMock()
        
        await service.update(presentation_id, n_slides=10, title="New Title")
        
        mock_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_slides(self, service, mock_repository):
        """Test updating slides for a presentation."""
        presentation_id = uuid4()
        mock_presentation = MagicMock()
        mock_repository.get_by_id.return_value = mock_presentation
        mock_repository.get_with_slides.return_value = MagicMock()
        
        slides = [
            SlideModel(
                presentation=presentation_id,
                layout_group="test",
                layout="test-layout",
                index=0,
                content={},
            )
        ]
        
        await service.update_slides(presentation_id, slides)
        
        mock_repository.delete_slides.assert_called_once_with(presentation_id)
        mock_repository.save_slides.assert_called_once_with(slides)
