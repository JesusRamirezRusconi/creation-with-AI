"""Streaming service for real-time slide generation.

This service handles Server-Sent Events (SSE) streaming for
generating presentations in real-time.
"""

import asyncio
import json
from typing import AsyncGenerator, List
from uuid import UUID

from core.exceptions import PresentationNotFoundException
from core.logging import get_logger
from domain.presentation.repositories import PresentationRepositoryProtocol
from infrastructure.services.slide_generation_service import SlideGenerationService
from models.presentation_outline_model import PresentationOutlineModel
from models.presentation_with_slides import PresentationWithSlides
from models.sql.slide import SlideModel
from models.sse_response import SSECompleteResponse, SSEErrorResponse, SSEResponse
from services.image_generation_service import ImageGenerationService
from utils.asset_directory_utils import get_images_directory
from utils.llm_calls.generate_slide_content import get_slide_content_from_type_and_outline
from utils.process_slides import process_slide_add_placeholder_assets, process_slide_and_fetch_assets

logger = get_logger(__name__)


class StreamingService:
    """Service for streaming presentation generation.
    
    This service handles SSE streaming to send slides as they're
    generated in real-time.
    """

    def __init__(
        self,
        repository: PresentationRepositoryProtocol,
        slide_service: SlideGenerationService,
    ):
        """Initialize service.

        Args:
            repository: Presentation repository
            slide_service: Slide generation service
        """
        self.repository = repository
        self.slide_service = slide_service

    async def stream_presentation_generation(
        self,
        presentation_id: UUID,
    ) -> AsyncGenerator[str, None]:
        """Stream presentation generation as SSE.

        Args:
            presentation_id: ID of presentation to generate

        Yields:
            SSE formatted strings with slide data

        Raises:
            PresentationNotFoundException: If presentation not found
        """
        logger.info(f"Starting streaming generation for: {presentation_id}")
        
        # Get presentation
        presentation = await self.repository.get_by_id(presentation_id)
        if not presentation:
            yield SSEErrorResponse(detail="Presentation not found").to_string()
            return
        
        if not presentation.structure:
            yield SSEErrorResponse(
                detail="Presentation not prepared for stream"
            ).to_string()
            return
        
        if not presentation.outlines:
            yield SSEErrorResponse(detail="Outlines can not be empty").to_string()
            return
        
        try:
            async for chunk in self._generate_and_stream_slides(presentation, presentation_id):
                yield chunk
        except Exception as e:
            logger.exception(f"Streaming generation failed: {presentation_id}")
            yield SSEErrorResponse(detail="Streaming generation failed").to_string()

    async def _generate_and_stream_slides(
        self,
        presentation: any,
        presentation_id: UUID,
    ) -> AsyncGenerator[str, None]:
        """Generate slides and stream them.

        Args:
            presentation: Presentation model
            presentation_id: Presentation ID

        Yields:
            SSE formatted slide data
        """
        structure = presentation.get_structure()
        layout = presentation.get_layout()
        outline = presentation.get_presentation_outline()
        
        image_service = ImageGenerationService(get_images_directory())
        async_assets_tasks = []
        slides: List[SlideModel] = []
        
        # Start JSON array
        yield SSEResponse(
            event="response",
            data=json.dumps({"type": "chunk", "chunk": '{ "slides": [ '}),
        ).to_string()
        
        # Generate each slide
        for i, slide_layout_index in enumerate(structure.slides):
            slide_layout = layout.slides[slide_layout_index]
            is_last_slide = i == len(structure.slides) - 1
            is_questions_slide = slide_layout.id == "questions-quiz-slide" or slide_layout.name == "questions"
            
            try:
                # Generate questions slide if it's the last slide
                if is_last_slide and is_questions_slide and slides:
                    slide_content = await self.slide_service.generate_questions_slide(
                        slides,
                        presentation.language or "es",
                        num_questions=5,
                    )
                else:
                    # Generate regular slide
                    slide_content = await get_slide_content_from_type_and_outline(
                        slide_layout,
                        outline.slides[i],
                        presentation.language,
                        presentation.tone,
                        presentation.verbosity,
                        presentation.instructions,
                    )
                
                slide = SlideModel(
                    presentation=presentation_id,
                    layout_group=layout.name,
                    layout=slide_layout.id,
                    index=i,
                    speaker_note=slide_content.get("__speaker_note__", ""),
                    content=slide_content,
                )
                slides.append(slide)
                
                # Process assets
                process_slide_add_placeholder_assets(slide)
                async_assets_tasks.append(
                    process_slide_and_fetch_assets(image_service, slide)
                )
                
                # Stream slide
                yield SSEResponse(
                    event="response",
                    data=json.dumps({"type": "chunk", "chunk": slide.model_dump_json()}),
                ).to_string()
                
            except Exception as e:
                logger.error(f"Failed to generate slide {i}: {e}")
                yield SSEErrorResponse(detail=f"Failed to generate slide {i}").to_string()
                return
        
        # Close JSON array
        yield SSEResponse(
            event="response",
            data=json.dumps({"type": "chunk", "chunk": " ] }"}),
        ).to_string()
        
        # Wait for all assets
        generated_assets_lists = await asyncio.gather(*async_assets_tasks)
        generated_assets = []
        for assets_list in generated_assets_lists:
            generated_assets.extend(assets_list)
        
        # Save to database
        await self.repository.delete_slides(presentation_id)
        await self.repository.save_slides(slides)
        await self.repository.save_assets(generated_assets)
        
        # Send completion
        response = PresentationWithSlides(
            **presentation.model_dump(),
            slides=slides,
        )
        yield SSECompleteResponse(
            key="presentation",
            value=response.model_dump(mode="json"),
        ).to_string()
        
        logger.info(f"Completed streaming generation: {presentation_id}")
