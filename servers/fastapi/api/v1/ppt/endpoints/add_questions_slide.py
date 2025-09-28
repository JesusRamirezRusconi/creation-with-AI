import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel
from services.database import get_async_session
from models.presentation_with_slides import PresentationWithSlides
from utils.llm_calls.generate_questions_from_content import generate_questions_from_presentation_content

ADD_QUESTIONS_ROUTER = APIRouter()


@ADD_QUESTIONS_ROUTER.post("/add-questions-slide", response_model=PresentationWithSlides)
async def add_questions_slide_to_presentation(
    presentation_id: Annotated[uuid.UUID, Body(description="Presentation ID to add questions slide to")],
    sql_session: AsyncSession = Depends(get_async_session),
):
    """
    Add an interactive questions slide to an existing presentation.
    This endpoint creates a new slide using the QuizSlideLayout template
    with the presentation content injected for generating relevant questions.
    """
    
    # Verify presentation exists
    presentation = await sql_session.get(PresentationModel, presentation_id)
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    # Get existing slides to extract content and determine next index
    existing_slides = await sql_session.scalars(
        select(SlideModel)
        .where(SlideModel.presentation == presentation_id)
        .order_by(SlideModel.index)
    )
    existing_slides_list = list(existing_slides)
    
    if not existing_slides_list:
        raise HTTPException(status_code=400, detail="Cannot add questions to a presentation with no slides")
    
    # Check if a questions slide already exists
    for slide in existing_slides_list:
        if slide.layout_group == "questions" or slide.layout == "questions:questions-quiz-slide":
            raise HTTPException(
                status_code=400, 
                detail="A questions slide already exists in this presentation"
            )
    
    # Extract content from all slides for context
    presentation_content_parts = []
    
    # Add presentation title if available
    if presentation.title:
        presentation_content_parts.append(f"# {presentation.title}")
    
    # Extract content from each slide
    for slide in existing_slides_list:
        if slide.content:
            # Try to extract meaningful content from slide content
            content = slide.content
            
            # Common content fields to extract
            content_fields = ['title', 'content', 'text', 'description', 'subtitle']
            slide_content = []
            
            for field in content_fields:
                if field in content and content[field]:
                    slide_content.append(str(content[field]))
            
            # If no standard fields found, try to extract any text content
            if not slide_content:
                for key, value in content.items():
                    if isinstance(value, str) and len(value.strip()) > 0:
                        slide_content.append(value)
                    elif isinstance(value, dict):
                        # Look for nested text content
                        for nested_key, nested_value in value.items():
                            if isinstance(nested_value, str) and len(nested_value.strip()) > 0:
                                slide_content.append(nested_value)
            
            if slide_content:
                presentation_content_parts.extend(slide_content)
    
    # Combine all content
    presentation_content = "\n\n".join(presentation_content_parts)
    
    # If no content found, use a default message
    if not presentation_content.strip():
        presentation_content = "Esta presentación contiene información valiosa que puede ser evaluada mediante las siguientes preguntas."
    
    # Generate specific questions based on content using AI
    try:
        print(f"🤖 Generando preguntas para presentación: {presentation.title}")
        print(f"📝 Contenido extraído (primeros 200 chars): {presentation_content[:200]}...")
        
        generated_questions = await generate_questions_from_presentation_content(
            presentation_content=presentation_content,
            num_questions=5,
            language="es"
        )
        
        print(f"✅ {len(generated_questions)} preguntas generadas exitosamente")
        print(f"🎯 Primera pregunta: {generated_questions[0]['question'][:100]}..." if generated_questions else "❌ No se generaron preguntas")
        
    except Exception as e:
        print(f"⚠️ Error generando preguntas con IA: {str(e)}")
        print("🔄 Usando preguntas de fallback")
        # Fallback to basic questions if AI generation fails
        generated_questions = [
            {
                "id": 1,
                "question": "¿Cuál es el tema principal abordado en esta presentación?",
                "options": [
                    "Desarrollo técnico",
                    "El tema principal presentado",
                    "Gestión operativa", 
                    "Análisis estratégico"
                ],
                "correctAnswer": 1,
                "explanation": "El tema principal se menciona claramente en la introducción y se desarrolla a lo largo de la presentación."
            },
            {
                "id": 2,
                "question": "¿Qué concepto clave se explica en la presentación?",
                "options": [
                    "Concepto básico",
                    "El concepto principal desarrollado",
                    "Tema secundario",
                    "Aspecto técnico"
                ],
                "correctAnswer": 1,
                "explanation": "Este concepto se desarrolla con detalle en varios slides de la presentación."
            },
            {
                "id": 3,
                "question": "¿Cuál es la conclusión principal de la presentación?",
                "options": [
                    "Resumen general",
                    "La conclusión principal presentada",
                    "Preguntas abiertas",
                    "Agradecimientos finales"
                ],
                "correctAnswer": 1,
                "explanation": "La conclusión se presenta al final y resume los puntos más importantes."
            },
            {
                "id": 4,
                "question": "¿Qué beneficio se menciona en la presentación?",
                "options": [
                    "Beneficio general",
                    "El beneficio específico mencionado",
                    "Característica técnica",
                    "Aspecto operativo"
                ],
                "correctAnswer": 1,
                "explanation": "Este beneficio se destaca como un punto clave en la presentación."
            },
            {
                "id": 5,
                "question": "¿Cuál es el siguiente paso recomendado?",
                "options": [
                    "Acción general",
                    "El siguiente paso recomendado",
                    "Contacto de soporte",
                    "Más información"
                ],
                "correctAnswer": 1,
                "explanation": "La recomendación se presenta como conclusión práctica de la presentación."
            }
        ]
    
    # Calculate next slide index
    next_index = max(slide.index for slide in existing_slides_list) + 1
    
    # Create the questions slide content
    questions_slide_content = {
        "presentationContent": presentation_content,
        "title": "🎯 Evaluación de Conocimientos",
        "description": "Responde las siguientes preguntas para evaluar tu comprensión del contenido presentado.",
        "customQuestions": generated_questions
    }
    
    print(f"📦 Contenido del slide de preguntas creado:")
    print(f"   - Título: {questions_slide_content['title']}")
    print(f"   - Preguntas personalizadas: {len(questions_slide_content['customQuestions'])} preguntas")
    print(f"   - Contenido de presentación: {len(questions_slide_content['presentationContent'])} caracteres")
    
    # Create new questions slide
    questions_slide = SlideModel(
        id=uuid.uuid4(),
        presentation=presentation_id,
        layout_group="questions",
        layout="questions:questions-quiz-slide",
        index=next_index,
        content=questions_slide_content,
        speaker_note="Esta es una evaluación interactiva basada en el contenido de la presentación. Los usuarios pueden responder las preguntas y obtener retroalimentación inmediata."
    )
    
    # Save the new slide
    sql_session.add(questions_slide)
    await sql_session.commit()
    
    # Return updated presentation with all slides
    all_slides = await sql_session.scalars(
        select(SlideModel)
        .where(SlideModel.presentation == presentation_id)
        .order_by(SlideModel.index)
    )
    
    return PresentationWithSlides(
        **presentation.model_dump(),
        slides=list(all_slides),
    )


@ADD_QUESTIONS_ROUTER.post("/check-questions-slide", response_model=dict)
async def check_if_presentation_has_questions_slide(
    presentation_id: Annotated[uuid.UUID, Body(description="Presentation ID to check")],
    sql_session: AsyncSession = Depends(get_async_session),
):
    """
    Check if a presentation already has a questions slide.
    Returns information about whether questions functionality is available.
    """
    
    # Verify presentation exists
    presentation = await sql_session.get(PresentationModel, presentation_id)
    if not presentation:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    # Check for existing questions slides
    slides = await sql_session.scalars(
        select(SlideModel)
        .where(SlideModel.presentation == presentation_id)
        .order_by(SlideModel.index)
    )
    slides_list = list(slides)
    
    has_questions_slide = any(
        slide.layout_group == "questions" or slide.layout == "questions:questions-quiz-slide" 
        for slide in slides_list
    )
    
    total_slides = len(slides_list)
    
    return {
        "presentation_id": str(presentation_id),
        "has_questions_slide": has_questions_slide,
        "total_slides": total_slides,
        "can_add_questions": total_slides > 0 and not has_questions_slide,
        "message": (
            "Presentation already has a questions slide" if has_questions_slide
            else "Questions slide can be added" if total_slides > 0
            else "Cannot add questions to empty presentation"
        )
    }
