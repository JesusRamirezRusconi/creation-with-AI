"""Slide generation service.

This service handles slide-specific generation logic including
regular slides and special slide types like questions.
"""

import asyncio
from typing import List, Optional

from core.logging import get_logger
from models.presentation_outline_model import PresentationOutlineModel
from models.sql.slide import SlideModel
from services.image_generation_service import ImageGenerationService
from utils.llm_calls.generate_questions_from_content import (
    generate_questions_from_presentation_content,
    generate_fallback_questions,
)
from utils.llm_calls.generate_slide_content import get_slide_content_from_type_and_outline
from utils.process_slides import (
    process_slide_add_placeholder_assets,
    process_slide_and_fetch_assets,
)

logger = get_logger(__name__)


class SlideGenerationService:
    """Service for generating and processing slides.
    
    This service handles the generation of individual slides including
    special types like questions slides.
    """

    def __init__(self, image_service: ImageGenerationService):
        """Initialize service.

        Args:
            image_service: Image generation service for assets
        """
        self.image_service = image_service

    async def generate_slides_batch(
        self,
        slide_layouts: List[any],
        outlines: PresentationOutlineModel,
        language: str,
        tone: str,
        verbosity: str,
        instructions: Optional[str],
        presentation_id: any,
        layout_group_name: str,
        start_index: int = 0,
    ) -> List[SlideModel]:
        """Generate a batch of slides concurrently.

        Args:
            slide_layouts: List of slide layouts
            outlines: Presentation outlines
            language: Presentation language
            tone: Content tone
            verbosity: Content verbosity
            instructions: Optional custom instructions
            presentation_id: Presentation ID
            layout_group_name: Layout group name
            start_index: Starting index for slides

        Returns:
            List of generated slides
        """
        logger.debug(f"Generating batch of {len(slide_layouts)} slides from index {start_index}")
        
        # Generate contents concurrently
        content_tasks = [
            get_slide_content_from_type_and_outline(
                slide_layouts[i],
                outlines.slides[start_index + i],
                language,
                tone,
                verbosity,
                instructions,
            )
            for i in range(len(slide_layouts))
        ]
        
        batch_contents = await asyncio.gather(*content_tasks)
        
        # Build slide models
        slides = []
        for i, slide_content in enumerate(batch_contents):
            slide = SlideModel(
                presentation=presentation_id,
                layout_group=layout_group_name,
                layout=slide_layouts[i].id,
                index=start_index + i,
                speaker_note=slide_content.get("__speaker_note__"),
                content=slide_content,
            )
            slides.append(slide)
        
        logger.debug(f"Successfully generated {len(slides)} slides")
        return slides

    async def generate_questions_slide(
        self,
        previous_slides: List[SlideModel],
        language: str,
        num_questions: int = 5,
    ) -> dict:
        """Generate a questions/quiz slide based on presentation content.

        Args:
            previous_slides: All previous slides for context
            language: Presentation language
            num_questions: Number of questions to generate

        Returns:
            Slide content dictionary with questions
        """
        logger.info("Generating questions slide from presentation content")
        
        # Extract content from previous slides
        presentation_content = self._extract_presentation_content(previous_slides)
        outlines = [{"content": slide.content} for slide in previous_slides if slide.content]
        
        if not presentation_content.strip():
            presentation_content = "Esta presentación contiene información valiosa."
        
        logger.debug(f"Extracted {len(presentation_content)} characters of content")
        
        # Generate questions with AI
        try:
            questions = await generate_questions_from_presentation_content(
                presentation_content=presentation_content,
                num_questions=num_questions,
                language=language,
                outlines=outlines,
            )
            logger.info(f"Successfully generated {len(questions)} questions with AI")
        except Exception as e:
            logger.warning(f"AI question generation failed: {e}, using fallback")
            questions = generate_fallback_questions(
                presentation_content,
                num_questions,
                language,
                outlines,
            )
        
        # Create slide content
        return {
            "presentationContent": presentation_content,
            "title": "🎯 Evaluación de Conocimientos",
            "description": "Responde las siguientes preguntas para evaluar tu comprensión del contenido presentado.",
            "customQuestions": questions,
            "__speaker_note__": "Esta es una evaluación interactiva basada en el contenido de la presentación.",
        }

    def _extract_presentation_content(self, slides: List[SlideModel]) -> str:
        """Extract meaningful content from slides.

        Args:
            slides: List of slides to extract from

        Returns:
            Combined content string
        """
        content_parts = []
        content_fields = ['title', 'content', 'text', 'description', 'subtitle', 'body', 'mainContent']
        
        for slide in slides:
            if not slide.content:
                continue
            
            slide_content = []
            
            # Extract specific fields
            for field in content_fields:
                if field in slide.content and slide.content[field]:
                    value = slide.content[field]
                    if isinstance(value, str) and len(value.strip()) > 0:
                        slide_content.append(str(value))
                    elif isinstance(value, list) and value:
                        slide_content.append(' '.join(str(v) for v in value if v))
            
            # If no specific fields, extract any text
            if not slide_content:
                for key, value in slide.content.items():
                    if key.startswith('__'):
                        continue
                    if isinstance(value, str) and len(value.strip()) > 50:
                        slide_content.append(value)
                    elif isinstance(value, list) and value:
                        for item in value:
                            if isinstance(item, str) and len(item.strip()) > 20:
                                slide_content.append(item)
            
            if slide_content:
                content_parts.extend(slide_content)
        
        return "\n\n".join(content_parts)

    async def process_slide_assets(
        self,
        slide: SlideModel,
        add_placeholders: bool = True,
    ) -> List[any]:
        """Process assets for a slide.

        Args:
            slide: Slide to process
            add_placeholders: Whether to add placeholder assets

        Returns:
            List of generated assets
        """
        if add_placeholders:
            process_slide_add_placeholder_assets(slide)
        
        assets = await process_slide_and_fetch_assets(self.image_service, slide)
        return assets
