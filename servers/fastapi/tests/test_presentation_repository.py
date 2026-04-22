"""Unit tests for infrastructure repositories."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from core.exceptions import PresentationNotFoundException
from infrastructure.repositories.presentation_repository import PresentationRepository
from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel


class TestPresentationRepository:
    """Test suite for PresentationRepository."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        session = AsyncMock()
        session.get = AsyncMock()
        session.execute = AsyncMock()
        session.scalars = AsyncMock()
        session.add = MagicMock()
        session.add_all = MagicMock()
        session.delete = AsyncMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        return session

    @pytest.fixture
    def repository(self, mock_session):
        """Create repository with mock session."""
        return PresentationRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_id_found(self, repository, mock_session):
        """Test getting presentation by ID when it exists."""
        presentation_id = uuid4()
        mock_presentation = MagicMock()
        mock_session.get.return_value = mock_presentation
        
        result = await repository.get_by_id(presentation_id)
        
        assert result == mock_presentation
        mock_session.get.assert_called_once_with(PresentationModel, presentation_id)

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, repository, mock_session):
        """Test getting presentation by ID when it doesn't exist."""
        presentation_id = uuid4()
        mock_session.get.return_value = None
        
        result = await repository.get_by_id(presentation_id)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_create_presentation(self, repository, mock_session):
        """Test creating a new presentation."""
        presentation = PresentationModel(
            id=uuid4(),
            content="Test",
            n_slides=5,
            language="en",
        )
        
        result = await repository.create(presentation)
        
        mock_session.add.assert_called_once_with(presentation)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(presentation)
        assert result == presentation

    @pytest.mark.asyncio
    async def test_delete_presentation_success(self, repository, mock_session):
        """Test deleting an existing presentation."""
        presentation_id = uuid4()
        mock_presentation = MagicMock()
        mock_session.get.return_value = mock_presentation
        
        await repository.delete(presentation_id)
        
        mock_session.delete.assert_called_once_with(mock_presentation)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_presentation_not_found(self, repository, mock_session):
        """Test deleting non-existent presentation raises exception."""
        presentation_id = uuid4()
        mock_session.get.return_value = None
        
        with pytest.raises(PresentationNotFoundException):
            await repository.delete(presentation_id)

    @pytest.mark.asyncio
    async def test_save_slides(self, repository, mock_session):
        """Test saving multiple slides."""
        slides = [
            SlideModel(
                presentation=uuid4(),
                layout_group="test",
                layout="test-layout",
                index=i,
                content={},
            )
            for i in range(3)
        ]
        
        await repository.save_slides(slides)
        
        mock_session.add_all.assert_called_once_with(slides)
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_slides(self, repository, mock_session):
        """Test deleting all slides for a presentation."""
        presentation_id = uuid4()
        
        await repository.delete_slides(presentation_id)
        
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()
