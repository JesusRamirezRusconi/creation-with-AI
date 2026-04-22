"""Presentation API endpoints - Refactored version.

This module contains HTTP endpoints for presentation operations,
delegating business logic to services following Clean Architecture principles.
"""

from typing import Annotated, List, Literal, Optional
from uuid import UUID
import uuid

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import (
    get_export_service,
    get_presentation_generation_service,
    get_presentation_service,
)
from core.exceptions import (
    InvalidPresentationRequestException,
    PresentationBaseException,
    PresentationNotFoundException,
)
from core.logging import get_logger, set_request_id
from enums.tone import Tone
from enums.verbosity import Verbosity
from infrastructure.services.export_service import ExportService
from infrastructure.services.presentation_generation_service import PresentationGenerationService
from infrastructure.services.presentation_service import PresentationService
from models.generate_presentation_request import GeneratePresentationRequest
from models.presentation_and_path import PresentationPathAndEditPath
from models.presentation_from_template import EditPresentationRequest
from models.presentation_outline_model import PresentationOutlineModel, SlideOutlineModel
from models.presentation_with_slides import PresentationWithSlides
from models.pptx_models import PptxPresentationModel
from models.sql.async_presentation_generation_status import AsyncPresentationGenerationTaskModel
from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel
from services.database import get_async_session
from models.presentation_layout import PresentationLayoutModel
from utils.dict_utils import deep_update
from utils.export_utils import export_presentation as export_util
from sqlalchemy import delete
from sqlmodel import select


logger = get_logger(__name__)
PRESENTATION_ROUTER = APIRouter(prefix="/presentation", tags=["Presentation"])


@PRESENTATION_ROUTER.get("/all", response_model=List[PresentationWithSlides])
async def get_all_presentations(
    presentation_service: PresentationService = Depends(get_presentation_service),
):
    """Get all presentations with their first slide."""
    try:
        set_request_id()
        logger.info("GET /all - Fetching all presentations")
        return await presentation_service.get_all_with_first_slide()
    except Exception as e:
        logger.exception("Failed to fetch presentations")
        raise HTTPException(status_code=500, detail="Failed to retrieve presentations")


@PRESENTATION_ROUTER.get("/{id}", response_model=PresentationWithSlides)
async def get_presentation(
    id: UUID,
    presentation_service: PresentationService = Depends(get_presentation_service),
):
    """Get a presentation by ID with all slides."""
    try:
        set_request_id()
        logger.info(f"GET /{id} - Fetching presentation")
        return await presentation_service.get_by_id(id)
    except PresentationNotFoundException as e:
        raise e.to_http_exception()
    except Exception as e:
        logger.exception(f"Failed to fetch presentation: {id}")
        raise HTTPException(status_code=500, detail="Failed to retrieve presentation")


@PRESENTATION_ROUTER.delete("/{id}", status_code=204)
async def delete_presentation(
    id: UUID,
    presentation_service: PresentationService = Depends(get_presentation_service),
):
    """Delete a presentation by ID."""
    try:
        set_request_id()
        logger.info(f"DELETE /{id} - Deleting presentation")
        await presentation_service.delete(id)
    except PresentationNotFoundException as e:
        raise e.to_http_exception()
    except Exception as e:
        logger.exception(f"Failed to delete presentation: {id}")
        raise HTTPException(status_code=500, detail="Failed to delete presentation")


@PRESENTATION_ROUTER.post("/create", response_model=PresentationModel)
async def create_presentation(
    content: Annotated[str, Body()],
    n_slides: Annotated[int, Body()],
    language: Annotated[str, Body()],
    file_paths: Annotated[Optional[List[str]], Body()] = None,
    tone: Annotated[Tone, Body()] = Tone.DEFAULT,
    verbosity: Annotated[Verbosity, Body()] = Verbosity.STANDARD,
    instructions: Annotated[Optional[str], Body()] = None,
    include_table_of_contents: Annotated[bool, Body()] = False,
    include_title_slide: Annotated[bool, Body()] = True,
    web_search: Annotated[bool, Body()] = False,
    presentation_service: PresentationService = Depends(get_presentation_service),
):
    """Create a new presentation (without generating content)."""
    try:
        set_request_id()
        logger.info("POST /create - Creating presentation")
        
        if include_table_of_contents and n_slides < 3:
            raise HTTPException(
                status_code=400,
                detail="Number of slides cannot be less than 3 if table of contents is included",
            )
        
        presentation = PresentationModel(
            id=uuid.uuid4(),
            content=content,
            n_slides=n_slides,
            language=language,
            file_paths=file_paths,
            tone=tone.value,
            verbosity=verbosity.value,
            instructions=instructions,
            include_table_of_contents=include_table_of_contents,
            include_title_slide=include_title_slide,
            web_search=web_search,
        )
        
        return await presentation_service.create(presentation)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create presentation")
        raise HTTPException(status_code=500, detail="Failed to create presentation")


@PRESENTATION_ROUTER.post("/generate", response_model=PresentationPathAndEditPath)
async def generate_presentation_sync(
    request: GeneratePresentationRequest,
    generation_service: PresentationGenerationService = Depends(get_presentation_generation_service),
):
    """Generate a presentation synchronously."""
    try:
        set_request_id()
        logger.info("POST /generate - Generating presentation synchronously")
        return await generation_service.generate_presentation(request)
    except PresentationBaseException as e:
        raise e.to_http_exception()
    except Exception as e:
        logger.exception("Failed to generate presentation")
        raise HTTPException(status_code=500, detail="Presentation generation failed")


@PRESENTATION_ROUTER.post(
    "/generate/async", response_model=AsyncPresentationGenerationTaskModel
)
async def generate_presentation_async(
    request: GeneratePresentationRequest,
    background_tasks: BackgroundTasks,
    generation_service: PresentationGenerationService = Depends(get_presentation_generation_service),
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Generate a presentation asynchronously using background tasks."""
    try:
        set_request_id()
        logger.info("POST /generate/async - Queueing async presentation generation")
        
        async_status = AsyncPresentationGenerationTaskModel(
            status="pending",
            message="Queued for generation",
            data=None,
        )
        sql_session.add(async_status)
        await sql_session.commit()
        
        background_tasks.add_task(
            generation_service.generate_presentation,
            request,
            async_status,
        )
        
        return async_status
    except Exception as e:
        logger.exception("Failed to queue async presentation generation")
        raise HTTPException(status_code=500, detail="Failed to queue presentation generation")


@PRESENTATION_ROUTER.get(
    "/status/{id}", response_model=AsyncPresentationGenerationTaskModel
)
async def check_async_presentation_generation_status(
    id: str,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Check status of async presentation generation."""
    try:
        set_request_id()
        logger.info(f"GET /status/{id} - Checking generation status")
        
        status = await sql_session.get(AsyncPresentationGenerationTaskModel, id)
        if not status:
            raise HTTPException(
                status_code=404,
                detail="No presentation generation task found",
            )
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch generation status: {id}")
        raise HTTPException(status_code=500, detail="Failed to retrieve status")


@PRESENTATION_ROUTER.post("/export/pptx", response_model=str)
async def export_presentation_as_pptx(
    pptx_model: Annotated[PptxPresentationModel, Body()],
    export_service: ExportService = Depends(get_export_service),
):
    """Export a presentation model as PPTX."""
    try:
        set_request_id()
        logger.info("POST /export/pptx - Exporting as PPTX")
        return await export_service.export_pptx_from_model(pptx_model)
    except Exception as e:
        logger.exception("Failed to export PPTX")
        raise HTTPException(status_code=500, detail="Failed to export presentation")


@PRESENTATION_ROUTER.post("/export", response_model=PresentationPathAndEditPath)
async def export_presentation_as_pptx_or_pdf(
    id: Annotated[UUID, Body(description="Presentation ID to export")],
    export_as: Annotated[
        Literal["pptx", "pdf"],
        Body(description="Format to export the presentation as"),
    ] = "pptx",
    export_service: ExportService = Depends(get_export_service),
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Export a presentation as PPTX or PDF."""
    try:
        set_request_id()
        logger.info(f"POST /export - Exporting presentation {id} as {export_as}")
        
        presentation = await sql_session.get(PresentationModel, id)
        if not presentation:
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        presentation_and_path = await export_service.export_presentation(
            id,
            presentation.title or str(uuid.uuid4()),
            export_as,
        )
        
        return PresentationPathAndEditPath(
            **presentation_and_path.model_dump(),
            edit_path=f"/presentation?id={id}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to export presentation: {id}")
        raise HTTPException(status_code=500, detail="Failed to export presentation")


@PRESENTATION_ROUTER.patch("/update", response_model=PresentationWithSlides)
async def update_presentation(
    id: Annotated[UUID, Body()],
    n_slides: Annotated[Optional[int], Body()] = None,
    title: Annotated[Optional[str], Body()] = None,
    slides: Annotated[Optional[List[SlideModel]], Body()] = None,
    presentation_service: PresentationService = Depends(get_presentation_service),
):
    """Update presentation metadata or slides."""
    try:
        set_request_id()
        logger.info(f"PATCH /update - Updating presentation {id}")
        
        if slides:
            return await presentation_service.update_slides(id, slides)
        else:
            return await presentation_service.update(id, n_slides, title)
    except PresentationNotFoundException as e:
        raise e.to_http_exception()
    except Exception as e:
        logger.exception(f"Failed to update presentation: {id}")
        raise HTTPException(status_code=500, detail="Failed to update presentation")


# NOTE: The following endpoints maintain backward compatibility with the original API
# They use some original logic that wasn't fully extracted to services yet


@PRESENTATION_ROUTER.post("/create-from-theme")
async def create_presentation_from_theme(
    outlines: Annotated[List[dict], Body()],
    title: Annotated[str, Body()],
    language: Annotated[str, Body()] = "en",
    n_slides: Annotated[int, Body()] = 10,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Create a presentation from saved theme outlines."""
    try:
        set_request_id()
        logger.info("POST /create-from-theme - Creating from theme")
        
        presentation = PresentationModel(
            title=title,
            language=language,
            n_slides=n_slides,
            content="Presentación creada desde tema guardado",
            tone=Tone.PROFESSIONAL,
            verbosity=Verbosity.CONCISE,
            include_title_slide=True,
            include_table_of_contents=False,
            web_search=False,
        )
        
        slide_outlines = []
        for outline in outlines:
            if isinstance(outline, dict) and 'content' in outline:
                slide_outlines.append(SlideOutlineModel(content=outline['content']))
            else:
                slide_outlines.append(SlideOutlineModel(content=str(outline)))
        
        presentation_outline_model = PresentationOutlineModel(slides=slide_outlines)
        presentation.outlines = presentation_outline_model.model_dump(mode="json")
        
        sql_session.add(presentation)
        await sql_session.commit()
        await sql_session.refresh(presentation)
        
        return {"id": str(presentation.id), "title": presentation.title}
    except Exception as e:
        await sql_session.rollback()
        logger.exception("Failed to create presentation from theme")
        raise HTTPException(status_code=500, detail=f"Error creating presentation: {str(e)}")


@PRESENTATION_ROUTER.post("/prepare", response_model=PresentationModel)
async def prepare_presentation(
    presentation_id: Annotated[UUID, Body()],
    outlines: Annotated[List[SlideOutlineModel], Body()],
    layout: Annotated[PresentationLayoutModel, Body()],
    title: Annotated[Optional[str], Body()] = None,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Prepare a presentation with outlines and layout (complex legacy endpoint)."""
    # NOTE: This endpoint contains complex logic that should be moved to a service
    # Keeping original implementation for now to maintain backward compatibility
    try:
        set_request_id()
        logger.info(f"POST /prepare - Preparing presentation {presentation_id}")
        
        if not outlines:
            raise HTTPException(status_code=400, detail="Outlines are required")
        
        presentation = await sql_session.get(PresentationModel, presentation_id)
        if not presentation:
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        # Original complex logic maintained here
        from utils.llm_calls.generate_presentation_structure import generate_presentation_structure
        import random
        
        presentation_outline_model = PresentationOutlineModel(slides=outlines)
        total_slide_layouts = len(layout.slides)
        total_outlines = len(outlines)
        
        if layout.ordered:
            presentation_structure = layout.to_presentation_structure()
        else:
            presentation_structure = await generate_presentation_structure(
                presentation_outline=presentation_outline_model,
                presentation_layout=layout,
                instructions=presentation.instructions,
            )
        
        presentation_structure.slides = presentation_structure.slides[:len(outlines)]
        for index in range(total_outlines):
            random_slide_index = random.randint(0, total_slide_layouts - 1)
            if index >= total_outlines:
                presentation_structure.slides.append(random_slide_index)
                continue
            if presentation_structure.slides[index] >= total_slide_layouts:
                presentation_structure.slides[index] = random_slide_index
        
        presentation.outlines = presentation_outline_model.model_dump(mode="json")
        presentation.title = title or presentation.title
        presentation.set_layout(layout)
        presentation.set_structure(presentation_structure)
        
        sql_session.add(presentation)
        await sql_session.commit()
        
        return presentation
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to prepare presentation")
        raise HTTPException(status_code=500, detail=str(e))


# Additional legacy endpoints kept for backward compatibility
# These should be refactored in future iterations

@PRESENTATION_ROUTER.post("/edit", response_model=PresentationPathAndEditPath)
async def edit_presentation_with_new_content(
    data: Annotated[EditPresentationRequest, Body()],
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Edit presentation with new content."""
    try:
        set_request_id()
        logger.info(f"POST /edit - Editing presentation {data.presentation_id}")
        
        presentation = await sql_session.get(PresentationModel, data.presentation_id)
        if not presentation:
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        slides = await sql_session.scalars(
            select(SlideModel).where(SlideModel.presentation == data.presentation_id)
        )
        
        new_slides = []
        slides_to_delete = []
        for each_slide in slides:
            new_slide_data = list(filter(lambda x: x.index == each_slide.index, data.slides))
            if new_slide_data:
                updated_content = deep_update(each_slide.content, new_slide_data[0].content)
                new_slides.append(each_slide.get_new_slide(presentation.id, updated_content))
                slides_to_delete.append(each_slide.id)
        
        await sql_session.execute(
            delete(SlideModel).where(SlideModel.id.in_(slides_to_delete))
        )
        sql_session.add_all(new_slides)
        await sql_session.commit()
        
        presentation_and_path = await export_util(
            presentation.id,
            presentation.title or str(uuid.uuid4()),
            data.export_as,
        )
        
        return PresentationPathAndEditPath(
            **presentation_and_path.model_dump(),
            edit_path=f"/presentation?id={presentation.id}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to edit presentation")
        raise HTTPException(status_code=500, detail=str(e))


@PRESENTATION_ROUTER.post("/derive", response_model=PresentationPathAndEditPath)
async def derive_presentation_from_existing_one(
    data: Annotated[EditPresentationRequest, Body()],
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Create a new presentation derived from an existing one."""
    try:
        set_request_id()
        logger.info(f"POST /derive - Deriving from presentation {data.presentation_id}")
        
        presentation = await sql_session.get(PresentationModel, data.presentation_id)
        if not presentation:
            raise HTTPException(status_code=404, detail="Presentation not found")
        
        slides = await sql_session.scalars(
            select(SlideModel).where(SlideModel.presentation == data.presentation_id)
        )
        
        new_presentation = presentation.get_new_presentation()
        new_slides = []
        for each_slide in slides:
            new_slide_data = list(filter(lambda x: x.index == each_slide.index, data.slides))
            if new_slide_data:
                updated_content = deep_update(each_slide.content, new_slide_data[0].content)
            else:
                updated_content = None
            new_slides.append(each_slide.get_new_slide(new_presentation.id, updated_content))
        
        sql_session.add(new_presentation)
        sql_session.add_all(new_slides)
        await sql_session.commit()
        
        presentation_and_path = await export_util(
            new_presentation.id,
            new_presentation.title or str(uuid.uuid4()),
            data.export_as,
        )
        
        return PresentationPathAndEditPath(
            **presentation_and_path.model_dump(),
            edit_path=f"/presentation?id={new_presentation.id}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to derive presentation")
        raise HTTPException(status_code=500, detail=str(e))


@PRESENTATION_ROUTER.get("/stream/{id}")
async def stream_presentation(
    id: UUID,
    sql_session: AsyncSession = Depends(get_async_session),
):
    """Stream presentation generation as Server-Sent Events."""
    try:
        set_request_id()
        logger.info(f"GET /stream/{id} - Streaming presentation generation")
        
        from infrastructure.services.streaming_service import StreamingService
        from core.dependencies import get_presentation_repository, get_slide_generation_service
        
        repository = get_presentation_repository(sql_session)
        slide_service = get_slide_generation_service()
        streaming_service = StreamingService(repository, slide_service)
        
        return StreamingResponse(
            streaming_service.stream_presentation_generation(id),
            media_type="text/event-stream",
        )
    except Exception as e:
        logger.exception(f"Failed to stream presentation: {id}")
        raise HTTPException(status_code=500, detail="Failed to stream presentation")
