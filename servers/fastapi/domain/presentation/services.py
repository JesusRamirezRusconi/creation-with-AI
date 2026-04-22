"""Domain services for presentation business logic.

This module contains pure business logic for presentations, independent
of infrastructure concerns like databases or external services.
"""

import math
from typing import List

from core.logging import get_logger
from models.presentation_layout import PresentationLayoutModel
from models.presentation_outline_model import PresentationOutlineModel, SlideOutlineModel
from models.presentation_structure_model import PresentationStructureModel

logger = get_logger(__name__)


class PresentationDomainService:
    """Service containing pure presentation business logic.
    
    This service implements domain rules and calculations without
    depending on external infrastructure.
    """

    @staticmethod
    def calculate_toc_slides_count(
        total_slides: int,
        include_title_slide: bool,
    ) -> int:
        """Calculate how many table of contents slides are needed.

        Args:
            total_slides: Total number of slides in presentation
            include_title_slide: Whether presentation includes a title slide

        Returns:
            Number of TOC slides needed (assuming 10 slides per TOC page)
        """
        logger.debug(f"Calculating TOC slides for {total_slides} total slides")
        
        # Adjust for title slide
        slides_to_index = total_slides - 1 if include_title_slide else total_slides
        
        # Calculate TOC slides needed (10 slides per TOC page)
        toc_slides_needed = math.ceil(slides_to_index / 10)
        
        logger.debug(f"TOC slides needed: {toc_slides_needed}")
        return toc_slides_needed

    @staticmethod
    def calculate_content_slides_count(
        total_slides: int,
        include_table_of_contents: bool,
        include_title_slide: bool,
    ) -> int:
        """Calculate how many content slides to generate.

        Args:
            total_slides: Total number of slides requested
            include_table_of_contents: Whether to include TOC
            include_title_slide: Whether to include title slide

        Returns:
            Number of content slides to generate (excluding TOC)
        """
        logger.debug(
            f"Calculating content slides: total={total_slides}, "
            f"toc={include_table_of_contents}, title={include_title_slide}"
        )
        
        content_slides = total_slides
        
        if include_table_of_contents:
            # Calculate and subtract TOC slides
            toc_count = PresentationDomainService.calculate_toc_slides_count(
                total_slides, include_title_slide
            )
            # Account for the space TOC takes
            needed_toc_count = math.ceil(
                ((total_slides - 1) if include_title_slide else total_slides) / 10
            )
            content_slides -= math.ceil((total_slides - needed_toc_count) / 10)
        
        logger.debug(f"Content slides to generate: {content_slides}")
        return content_slides

    @staticmethod
    def inject_table_of_contents(
        outlines: PresentationOutlineModel,
        structure: PresentationStructureModel,
        layout: PresentationLayoutModel,
        include_title_slide: bool,
        total_slides: int,
    ) -> tuple[PresentationOutlineModel, PresentationStructureModel]:
        """Inject table of contents into presentation outlines and structure.

        Args:
            outlines: Original presentation outlines
            structure: Original presentation structure
            layout: Presentation layout model
            include_title_slide: Whether presentation has title slide
            total_slides: Total number of slides

        Returns:
            Tuple of (updated outlines, updated structure)
        """
        logger.info("Injecting table of contents into presentation")
        
        total_outlines = len(outlines.slides)
        n_toc_slides = total_slides - total_outlines
        
        # Find TOC slide layout index
        toc_slide_layout_index = PresentationDomainService._find_toc_layout_index(layout)
        
        if toc_slide_layout_index == -1:
            logger.warning("No TOC layout found, skipping TOC injection")
            return outlines, structure
        
        outline_index = 1 if include_title_slide else 0
        
        for i in range(n_toc_slides):
            # Calculate range for this TOC page
            outlines_to = outline_index + 10
            if total_outlines == outlines_to:
                outlines_to -= 1
            
            # Insert TOC into structure
            insert_position = i + 1 if include_title_slide else i
            structure.slides.insert(insert_position, toc_slide_layout_index)
            
            # Generate TOC content
            toc_content = PresentationDomainService._generate_toc_content(
                outlines.slides[outline_index:outlines_to],
                outline_index,
                i,
                n_toc_slides,
                include_title_slide,
            )
            
            # Insert TOC outline
            outlines.slides.insert(
                insert_position,
                SlideOutlineModel(content=toc_content),
            )
            
            outline_index = outlines_to + 1
        
        logger.info(f"Injected {n_toc_slides} TOC slides")
        return outlines, structure

    @staticmethod
    def _find_toc_layout_index(layout: PresentationLayoutModel) -> int:
        """Find index of TOC/list layout in presentation layout.

        Args:
            layout: Presentation layout model

        Returns:
            Index of TOC layout, or -1 if not found
        """
        for idx, slide_layout in enumerate(layout.slides):
            if slide_layout.name in ["list", "table_of_contents", "toc"]:
                logger.debug(f"Found TOC layout at index {idx}: {slide_layout.name}")
                return idx
        
        logger.warning("No TOC layout found")
        return -1

    @staticmethod
    def _generate_toc_content(
        slides: List[SlideOutlineModel],
        start_index: int,
        toc_index: int,
        total_toc_slides: int,
        include_title_slide: bool,
    ) -> str:
        """Generate content for a table of contents slide.

        Args:
            slides: Slide outlines to include in TOC
            start_index: Starting slide index
            toc_index: Index of this TOC slide
            total_toc_slides: Total number of TOC slides
            include_title_slide: Whether presentation has title slide

        Returns:
            Formatted TOC content string
        """
        toc_lines = ["Table of Contents\n\n"]
        
        for offset, outline in enumerate(slides):
            page_number = (
                start_index - toc_index + total_toc_slides + 1 + offset
                if include_title_slide
                else start_index - toc_index + total_toc_slides + offset
            )
            
            # Truncate content to 100 chars for readability
            content_preview = outline.content[:100]
            toc_lines.append(
                f"Slide page number: {page_number}\n Slide Content: {content_preview}\n\n"
            )
        
        return "".join(toc_lines)

    @staticmethod
    def validate_presentation_structure(
        structure: PresentationStructureModel,
        outlines: PresentationOutlineModel,
        layout: PresentationLayoutModel,
    ) -> bool:
        """Validate that presentation structure is consistent.

        Args:
            structure: Presentation structure to validate
            outlines: Presentation outlines
            layout: Presentation layout

        Returns:
            True if structure is valid

        Raises:
            ValueError: If structure is invalid
        """
        logger.debug("Validating presentation structure")
        
        # Check that structure has same number of slides as outlines
        if len(structure.slides) != len(outlines.slides):
            error_msg = (
                f"Structure has {len(structure.slides)} slides but "
                f"outlines has {len(outlines.slides)} slides"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Check that all layout indices are valid
        max_layout_index = len(layout.slides) - 1
        for idx, layout_index in enumerate(structure.slides):
            if layout_index > max_layout_index:
                error_msg = (
                    f"Slide {idx} references layout index {layout_index} "
                    f"but max is {max_layout_index}"
                )
                logger.error(error_msg)
                raise ValueError(error_msg)
        
        logger.info("Presentation structure validation successful")
        return True
