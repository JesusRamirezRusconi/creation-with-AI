"""Unit tests for PresentationDomainService."""

import pytest

from domain.presentation.services import PresentationDomainService
from models.presentation_layout import PresentationLayoutModel, SlideLayoutModel
from models.presentation_outline_model import PresentationOutlineModel, SlideOutlineModel
from models.presentation_structure_model import PresentationStructureModel


class TestPresentationDomainService:
    """Test suite for PresentationDomainService."""

    @pytest.fixture
    def service(self):
        """Create domain service instance."""
        return PresentationDomainService()

    def test_calculate_toc_slides_count_with_title(self, service):
        """Test TOC calculation with title slide."""
        result = service.calculate_toc_slides_count(total_slides=25, include_title_slide=True)
        assert result == 3

    def test_calculate_toc_slides_count_without_title(self, service):
        """Test TOC calculation without title slide."""
        result = service.calculate_toc_slides_count(total_slides=20, include_title_slide=False)
        assert result == 2

    def test_calculate_content_slides_count_without_toc(self, service):
        """Test content slides calculation without TOC."""
        result = service.calculate_content_slides_count(
            total_slides=10,
            include_table_of_contents=False,
            include_title_slide=True,
        )
        assert result == 10

    def test_calculate_content_slides_count_with_toc(self, service):
        """Test content slides calculation with TOC."""
        result = service.calculate_content_slides_count(
            total_slides=10,
            include_table_of_contents=True,
            include_title_slide=True,
        )
        assert result < 10

    def test_find_toc_layout_index_found(self, service):
        """Test finding TOC layout when it exists."""
        layout = PresentationLayoutModel(
            name="test",
            ordered=False,
            slides=[
                SlideLayoutModel(id="title", name="title", json_schema={}),
                SlideLayoutModel(id="toc", name="table_of_contents", json_schema={}),
                SlideLayoutModel(id="content", name="content", json_schema={}),
            ],
        )
        
        result = service._find_toc_layout_index(layout)
        assert result == 1

    def test_find_toc_layout_index_not_found(self, service):
        """Test finding TOC layout when it doesn't exist."""
        layout = PresentationLayoutModel(
            name="test",
            ordered=False,
            slides=[
                SlideLayoutModel(id="title", name="title", json_schema={}),
                SlideLayoutModel(id="content", name="content", json_schema={}),
            ],
        )
        
        result = service._find_toc_layout_index(layout)
        assert result == -1

    def test_generate_toc_content(self, service):
        """Test TOC content generation."""
        slides = [
            SlideOutlineModel(content="Introduction to AI and Machine Learning"),
            SlideOutlineModel(content="Applications of AI in Modern Technology"),
        ]
        
        result = service._generate_toc_content(
            slides=slides,
            start_index=1,
            toc_index=0,
            total_toc_slides=1,
            include_title_slide=True,
        )
        
        assert "Table of Contents" in result
        assert "Slide page number" in result
        assert "Introduction to AI" in result

    def test_validate_presentation_structure_valid(self, service):
        """Test validation of valid presentation structure."""
        structure = PresentationStructureModel(slides=[0, 1, 0])
        outlines = PresentationOutlineModel(
            slides=[
                SlideOutlineModel(content="Slide 1"),
                SlideOutlineModel(content="Slide 2"),
                SlideOutlineModel(content="Slide 3"),
            ]
        )
        layout = PresentationLayoutModel(
            name="test",
            ordered=False,
            slides=[
                SlideLayoutModel(id="layout1", name="layout1", json_schema={}),
                SlideLayoutModel(id="layout2", name="layout2", json_schema={}),
            ],
        )
        
        result = service.validate_presentation_structure(structure, outlines, layout)
        assert result is True

    def test_validate_presentation_structure_mismatched_count(self, service):
        """Test validation fails when structure/outlines count mismatch."""
        structure = PresentationStructureModel(slides=[0, 1])
        outlines = PresentationOutlineModel(
            slides=[SlideOutlineModel(content="Slide 1")]
        )
        layout = PresentationLayoutModel(
            name="test",
            ordered=False,
            slides=[SlideLayoutModel(id="layout1", name="layout1", json_schema={})],
        )
        
        with pytest.raises(ValueError):
            service.validate_presentation_structure(structure, outlines, layout)

    def test_validate_presentation_structure_invalid_layout_index(self, service):
        """Test validation fails when layout index is out of bounds."""
        structure = PresentationStructureModel(slides=[0, 5])
        outlines = PresentationOutlineModel(
            slides=[
                SlideOutlineModel(content="Slide 1"),
                SlideOutlineModel(content="Slide 2"),
            ]
        )
        layout = PresentationLayoutModel(
            name="test",
            ordered=False,
            slides=[SlideLayoutModel(id="layout1", name="layout1", json_schema={})],
        )
        
        with pytest.raises(ValueError):
            service.validate_presentation_structure(structure, outlines, layout)
