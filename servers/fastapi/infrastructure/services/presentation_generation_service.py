"""Presentation generation service.

This service handles the complex logic of generating presentations from
various sources (content, markdown, files) using LLM services.
"""

import asyncio
import math
import random
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

import dirtyjson
from fastapi import HTTPException

from core.exceptions import PresentationGenerationException
from core.logging import get_logger
from domain.presentation.repositories import PresentationRepositoryProtocol
from domain.presentation.services import PresentationDomainService
from domain.presentation.validators import validate_presentation_request
from models.generate_presentation_request import GeneratePresentationRequest
from models.presentation_and_path import PresentationPathAndEditPath
from models.presentation_outline_model import PresentationOutlineModel, SlideOutlineModel
from models.presentation_structure_model import PresentationStructureModel
from models.sql.async_presentation_generation_status import AsyncPresentationGenerationTaskModel
from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel
from services.concurrent_service import CONCURRENT_SERVICE
from services.documents_loader import DocumentsLoader
from services.image_generation_service import ImageGenerationService
from services.webhook_service import WebhookService
from enums.webhook_event import WebhookEvent
from utils.asset_directory_utils import get_images_directory
from utils.export_utils import export_presentation
from utils.get_layout_by_name import get_layout_by_name
from utils.llm_calls.generate_presentation_outlines import generate_ppt_outline
from utils.llm_calls.generate_presentation_structure import generate_presentation_structure
from utils.llm_calls.generate_slide_content import get_slide_content_from_type_and_outline
from utils.ppt_utils import get_presentation_title_from_outlines
from utils.process_slides import process_slide_and_fetch_assets
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class PresentationGenerationService:
    """Service for generating complete presentations.
    
    This service orchestrates the complex multi-step process of generating
    presentations from various content sources.
    """

    def __init__(self, repository: PresentationRepositoryProtocol, session: AsyncSession):
        """Initialize service.

        Args:
            repository: Presentation repository
            session: Database session for validation
        """
        self.repository = repository
        self.session = session
        self.domain_service = PresentationDomainService()

    async def generate_presentation(
        self,
        request: GeneratePresentationRequest,
        async_status: Optional[AsyncPresentationGenerationTaskModel] = None,
    ) -> PresentationPathAndEditPath:
        """Generate a complete presentation from request.

        Args:
            request: Presentation generation request
            async_status: Optional async status tracker

        Returns:
            Generated presentation with path

        Raises:
            PresentationGenerationException: If generation fails
        """
        presentation_id = uuid4()
        logger.info(f"Starting presentation generation: {presentation_id}")

        try:
            # Step 1: Validate request
            await validate_presentation_request(request, self.session)

            # Step 2: Generate or parse outlines
            outlines = await self._generate_outlines(request, async_status)

            # Step 3: Update async status
            await self._update_status(async_status, "Selecting layout for each slide")

            # Step 4: Generate presentation structure
            structure, layout = await self._generate_structure(request, outlines, async_status)

            # Step 5: Inject table of contents if needed
            if request.include_table_of_contents and not request.slides_markdown:
                outlines, structure = self.domain_service.inject_table_of_contents(
                    outlines,
                    structure,
                    layout,
                    request.include_title_slide,
                    request.n_slides,
                )

            # Step 6: Create presentation model
            presentation = self._create_presentation_model(
                presentation_id, request, outlines, layout, structure
            )
            await self.repository.create(presentation)

            # Step 7: Update async status
            await self._update_status(async_status, "Generating slides")

            # Step 8: Generate slides
            slides = await self._generate_slides(
                request, outlines, structure, layout, presentation_id
            )

            # Step 9: Update async status
            await self._update_status(async_status, "Fetching assets for slides")

            # Step 10: Fetch assets
            assets = await self._fetch_slide_assets(slides)

            # Step 11: Save slides and assets
            await self.repository.save_slides(slides)
            await self.repository.save_assets(assets)

            # Step 12: Update async status
            await self._update_status(async_status, "Exporting presentation")

            # Step 13: Export presentation
            presentation_and_path = await export_presentation(
                presentation_id,
                presentation.title or str(uuid4()),
                request.export_as,
            )

            response = PresentationPathAndEditPath(
                **presentation_and_path.model_dump(),
                edit_path=f"/presentation?id={presentation_id}",
            )

            # Step 14: Update async status to completed
            await self._update_status(
                async_status,
                "Presentation generation completed",
                status="completed",
                data=response.model_dump(mode="json"),
            )

            # Trigger success webhook
            CONCURRENT_SERVICE.run_task(
                None,
                WebhookService.send_webhook,
                WebhookEvent.PRESENTATION_GENERATION_COMPLETED,
                response.model_dump(mode="json"),
            )

            logger.info(f"Successfully generated presentation: {presentation_id}")
            return response

        except Exception as e:
            logger.exception(f"Presentation generation failed: {presentation_id}")
            await self._handle_generation_error(e, async_status)
            raise

    async def _generate_outlines(
        self,
        request: GeneratePresentationRequest,
        async_status: Optional[AsyncPresentationGenerationTaskModel],
    ) -> PresentationOutlineModel:
        """Generate or parse presentation outlines.

        Args:
            request: Generation request
            async_status: Optional status tracker

        Returns:
            Presentation outlines
        """
        if request.slides_markdown:
            logger.info("Using provided slides markdown")
            return PresentationOutlineModel(
                slides=[SlideOutlineModel(content=slide) for slide in request.slides_markdown]
            )

        await self._update_status(async_status, "Generating presentation outlines")

        # Load additional context from files
        additional_context = await self._load_file_context(request.files)

        # Calculate slides to generate (accounting for TOC)
        n_slides_to_generate = self.domain_service.calculate_content_slides_count(
            request.n_slides,
            request.include_table_of_contents,
            request.include_title_slide,
        )

        # Generate outlines using LLM
        presentation_outlines_text = ""
        async for chunk in generate_ppt_outline(
            request.content,
            n_slides_to_generate,
            request.language,
            additional_context,
            request.tone.value,
            request.verbosity.value,
            request.instructions,
            request.include_title_slide,
            request.web_search,
        ):
            if isinstance(chunk, HTTPException):
                raise chunk
            presentation_outlines_text += chunk

        # Parse JSON
        try:
            presentation_outlines_json = dict(dirtyjson.loads(presentation_outlines_text))
            outlines = PresentationOutlineModel(**presentation_outlines_json)
            logger.info(f"Generated {len(outlines.slides)} outlines")
            return outlines
        except Exception as e:
            logger.error(f"Failed to parse presentation outlines: {e}")
            raise PresentationGenerationException(
                "Failed to generate presentation outlines. Please try again.",
                details={"error": str(e)},
            )

    async def _load_file_context(self, files: Optional[List[str]]) -> str:
        """Load additional context from uploaded files.

        Args:
            files: List of file paths

        Returns:
            Combined file content as string
        """
        if not files:
            return ""

        logger.info(f"Loading context from {len(files)} files")
        documents_loader = DocumentsLoader(file_paths=files)
        await documents_loader.load_documents()
        
        if documents_loader.documents:
            return "\n\n".join(documents_loader.documents)
        
        return ""

    async def _generate_structure(
        self,
        request: GeneratePresentationRequest,
        outlines: PresentationOutlineModel,
        async_status: Optional[AsyncPresentationGenerationTaskModel],
    ) -> tuple[PresentationStructureModel, any]:
        """Generate presentation structure and layout.

        Args:
            request: Generation request
            outlines: Presentation outlines
            async_status: Optional status tracker

        Returns:
            Tuple of (structure, layout)
        """
        logger.info("Generating presentation structure")
        
        # Get layout
        layout = await get_layout_by_name(request.template)
        total_slide_layouts = len(layout.slides)
        total_outlines = len(outlines.slides)

        # Generate structure
        if layout.ordered:
            structure = layout.to_presentation_structure()
        else:
            structure = await generate_presentation_structure(
                outlines,
                layout,
                request.instructions,
                bool(request.slides_markdown),
            )

        # Ensure structure matches outlines
        structure.slides = structure.slides[:total_outlines]
        
        # Fix invalid layout indices
        for index in range(total_outlines):
            if index >= len(structure.slides):
                structure.slides.append(random.randint(0, total_slide_layouts - 1))
            elif structure.slides[index] >= total_slide_layouts:
                structure.slides[index] = random.randint(0, total_slide_layouts - 1)

        logger.info("Successfully generated presentation structure")
        return structure, layout

    def _create_presentation_model(
        self,
        presentation_id: UUID,
        request: GeneratePresentationRequest,
        outlines: PresentationOutlineModel,
        layout: any,
        structure: PresentationStructureModel,
    ) -> PresentationModel:
        """Create presentation model from components.

        Args:
            presentation_id: Generated presentation ID
            request: Generation request
            outlines: Presentation outlines
            layout: Presentation layout
            structure: Presentation structure

        Returns:
            PresentationModel ready to save
        """
        return PresentationModel(
            id=presentation_id,
            content=request.content,
            n_slides=request.n_slides,
            language=request.language,
            title=get_presentation_title_from_outlines(outlines),
            outlines=outlines.model_dump(),
            layout=layout.model_dump(),
            structure=structure.model_dump(),
            tone=request.tone.value,
            verbosity=request.verbosity.value,
            instructions=request.instructions,
        )

    async def _generate_slides(
        self,
        request: GeneratePresentationRequest,
        outlines: PresentationOutlineModel,
        structure: PresentationStructureModel,
        layout: any,
        presentation_id: UUID,
    ) -> List[SlideModel]:
        """Generate all slides with content.

        Args:
            request: Generation request
            outlines: Presentation outlines
            structure: Presentation structure
            layout: Presentation layout
            presentation_id: Presentation ID

        Returns:
            List of generated slides
        """
        logger.info(f"Generating {len(structure.slides)} slides")
        
        slides: List[SlideModel] = []
        slide_layouts = [layout.slides[idx] for idx in structure.slides]

        # Generate slides in batches of 10
        batch_size = 10
        for start in range(0, len(slide_layouts), batch_size):
            end = min(start + batch_size, len(slide_layouts))
            logger.debug(f"Generating slides {start} to {end}")

            # Generate contents concurrently
            content_tasks = [
                get_slide_content_from_type_and_outline(
                    slide_layouts[i],
                    outlines.slides[i],
                    request.language,
                    request.tone.value,
                    request.verbosity.value,
                    request.instructions,
                )
                for i in range(start, end)
            ]
            batch_contents = await asyncio.gather(*content_tasks)

            # Build slides
            for offset, slide_content in enumerate(batch_contents):
                i = start + offset
                slide = SlideModel(
                    presentation=presentation_id,
                    layout_group=layout.name,
                    layout=slide_layouts[i].id,
                    index=i,
                    speaker_note=slide_content.get("__speaker_note__"),
                    content=slide_content,
                )
                slides.append(slide)

        logger.info(f"Successfully generated {len(slides)} slides")
        return slides

    async def _fetch_slide_assets(self, slides: List[SlideModel]) -> List:
        """Fetch assets for all slides.

        Args:
            slides: List of slides

        Returns:
            List of generated assets
        """
        logger.info(f"Fetching assets for {len(slides)} slides")
        
        image_service = ImageGenerationService(get_images_directory())
        
        asset_tasks = [
            process_slide_and_fetch_assets(image_service, slide)
            for slide in slides
        ]
        
        generated_assets_list = await asyncio.gather(*asset_tasks)
        assets = []
        for assets_list in generated_assets_list:
            assets.extend(assets_list)
        
        logger.info(f"Successfully fetched {len(assets)} assets")
        return assets

    async def _update_status(
        self,
        async_status: Optional[AsyncPresentationGenerationTaskModel],
        message: str,
        status: str = "pending",
        data: any = None,
    ) -> None:
        """Update async generation status.

        Args:
            async_status: Status model to update
            message: Status message
            status: Status state
            data: Optional result data
        """
        if not async_status:
            return

        async_status.message = message
        async_status.updated_at = datetime.now()
        if status != "pending":
            async_status.status = status
        if data:
            async_status.data = data
        
        self.session.add(async_status)
        await self.session.commit()

    async def _handle_generation_error(
        self,
        error: Exception,
        async_status: Optional[AsyncPresentationGenerationTaskModel],
    ) -> None:
        """Handle generation errors and update status.

        Args:
            error: Exception that occurred
            async_status: Optional status to update
        """
        if not isinstance(error, HTTPException):
            error = HTTPException(status_code=500, detail="Presentation generation failed")

        from models.api_error_model import APIErrorModel
        api_error = APIErrorModel.from_exception(error)

        # Trigger failure webhook
        CONCURRENT_SERVICE.run_task(
            None,
            WebhookService.send_webhook,
            WebhookEvent.PRESENTATION_GENERATION_FAILED,
            api_error.model_dump(mode="json"),
        )

        if async_status:
            async_status.status = "error"
            async_status.message = "Presentation generation failed"
            async_status.updated_at = datetime.now()
            async_status.error = api_error.model_dump(mode="json")
            self.session.add(async_status)
            await self.session.commit()
