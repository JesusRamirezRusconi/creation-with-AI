#!/usr/bin/env python3
"""
Script para agregar slides de preguntas interactivas a todas las presentaciones existentes
que no tengan ya un slide de preguntas.

Este script puede ejecutarse de forma segura ya que:
1. Verifica que la presentación no tenga ya un slide de preguntas
2. Solo agrega el slide, no modifica contenido existente  
3. Puede ejecutarse múltiples veces sin causar duplicados
4. Proporciona logging detallado de las operaciones

Uso:
    python add_questions_to_all_presentations.py [--dry-run] [--limit N]
    
    --dry-run: Solo muestra qué haría sin hacer cambios reales
    --limit N: Procesa solo las primeras N presentaciones
"""

import asyncio
import argparse
import logging
import sys
import uuid
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

# Add the parent directory to the path so we can import from the FastAPI app
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.sql.presentation import PresentationModel
from models.sql.slide import SlideModel
from services.database import get_async_session
from utils.llm_calls.generate_questions_from_content import generate_questions_from_presentation_content

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PresentationQuestionsUpdater:
    """
    Clase para manejar la adición de slides de preguntas a presentaciones existentes.
    """
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.stats = {
            'total_presentations': 0,
            'presentations_with_questions': 0,
            'presentations_without_slides': 0,
            'questions_added': 0,
            'errors': 0
        }
    
    async def get_presentations_needing_questions(
        self, 
        session: AsyncSession, 
        limit: int = None
    ) -> List[PresentationModel]:
        """
        Obtiene las presentaciones que necesitan slides de preguntas.
        """
        query = select(PresentationModel).order_by(PresentationModel.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        result = await session.execute(query)
        presentations = result.scalars().all()
        
        logger.info(f"Encontradas {len(presentations)} presentaciones para revisar")
        return list(presentations)
    
    async def check_presentation_questions_status(
        self, 
        session: AsyncSession, 
        presentation: PresentationModel
    ) -> Dict[str, Any]:
        """
        Verifica el estado de preguntas en una presentación específica.
        """
        # Obtener slides de la presentación
        slides_query = select(SlideModel).where(
            SlideModel.presentation == presentation.id
        ).order_by(SlideModel.index)
        
        result = await session.execute(slides_query)
        slides = list(result.scalars().all())
        
        # Verificar si ya tiene slide de preguntas
        has_questions = any(
            slide.layout_group == "questions" or slide.layout == "questions:questions-quiz-slide"
            for slide in slides
        )
        
        return {
            'presentation_id': presentation.id,
            'title': presentation.title or f"Presentación {presentation.id}",
            'total_slides': len(slides),
            'has_questions': has_questions,
            'can_add_questions': len(slides) > 0 and not has_questions,
            'slides': slides
        }
    
    def extract_presentation_content(self, slides: List[SlideModel]) -> str:
        """
        Extrae el contenido de una presentación para generar preguntas relevantes.
        """
        content_parts = []
        
        for slide in slides:
            if slide.content:
                content = slide.content
                
                # Campos comunes de contenido a extraer
                content_fields = ['title', 'content', 'text', 'description', 'subtitle']
                slide_content = []
                
                for field in content_fields:
                    if field in content and content[field]:
                        slide_content.append(str(content[field]))
                
                # Si no se encontraron campos estándar, buscar cualquier contenido de texto
                if not slide_content:
                    for key, value in content.items():
                        if isinstance(value, str) and len(value.strip()) > 0:
                            slide_content.append(value)
                        elif isinstance(value, dict):
                            # Buscar contenido de texto anidado
                            for nested_key, nested_value in value.items():
                                if isinstance(nested_value, str) and len(nested_value.strip()) > 0:
                                    slide_content.append(nested_value)
                
                if slide_content:
                    content_parts.extend(slide_content)
        
        # Combinar todo el contenido
        presentation_content = "\n\n".join(content_parts)
        
        # Si no se encontró contenido, usar un mensaje por defecto
        if not presentation_content.strip():
            presentation_content = "Esta presentación contiene información valiosa que puede ser evaluada mediante las siguientes preguntas."
        
        return presentation_content
    
    async def add_questions_slide(
        self, 
        session: AsyncSession, 
        presentation: PresentationModel, 
        slides: List[SlideModel]
    ) -> bool:
        """
        Agrega un slide de preguntas a la presentación.
        """
        try:
            # Extraer contenido para las preguntas
            presentation_content = self.extract_presentation_content(slides)
            
            # Generar preguntas específicas basadas en el contenido usando IA
            try:
                generated_questions = await generate_questions_from_presentation_content(
                    presentation_content=presentation_content,
                    num_questions=5,
                    language="es"
                )
                logger.info(f"✅ Generated {len(generated_questions)} AI-powered questions for {presentation.title or presentation.id}")
            except Exception as e:
                logger.warning(f"⚠️ AI generation failed for {presentation.title or presentation.id}: {str(e)}")
                # Fallback a preguntas básicas
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
            
            # Calcular el siguiente índice
            next_index = max(slide.index for slide in slides) + 1
            
            # Crear contenido del slide de preguntas
            questions_slide_content = {
                "presentationContent": presentation_content,
                "title": "🎯 Evaluación de Conocimientos",
                "description": "Responde las siguientes preguntas para evaluar tu comprensión del contenido presentado.",
                "customQuestions": generated_questions
            }
            
            # Crear nuevo slide de preguntas
            questions_slide = SlideModel(
                id=uuid.uuid4(),
                presentation=presentation.id,
                layout_group="questions",
                layout="questions:questions-quiz-slide",
                index=next_index,
                content=questions_slide_content,
                speaker_note="Esta es una evaluación interactiva basada en el contenido de la presentación. Los usuarios pueden responder las preguntas y obtener retroalimentación inmediata."
            )
            
            if not self.dry_run:
                session.add(questions_slide)
                await session.commit()
            
            logger.info(f"✅ Slide de preguntas agregado a: {presentation.title or presentation.id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error agregando preguntas a {presentation.id}: {str(e)}")
            if not self.dry_run:
                await session.rollback()
            return False
    
    async def process_presentation(
        self, 
        session: AsyncSession, 
        presentation: PresentationModel
    ) -> bool:
        """
        Procesa una presentación individual.
        """
        try:
            status = await self.check_presentation_questions_status(session, presentation)
            
            self.stats['total_presentations'] += 1
            
            if status['has_questions']:
                self.stats['presentations_with_questions'] += 1
                logger.info(f"⏭️  Saltando {status['title']} - ya tiene preguntas")
                return True
            
            if not status['can_add_questions']:
                self.stats['presentations_without_slides'] += 1
                logger.warning(f"⚠️  Saltando {status['title']} - sin slides o no válida")
                return True
            
            # Agregar slide de preguntas
            success = await self.add_questions_slide(session, presentation, status['slides'])
            
            if success:
                self.stats['questions_added'] += 1
            else:
                self.stats['errors'] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error procesando presentación {presentation.id}: {str(e)}")
            self.stats['errors'] += 1
            return False
    
    async def run(self, limit: int = None):
        """
        Ejecuta el proceso principal de actualización.
        """
        logger.info("🚀 Iniciando proceso de adición de preguntas a presentaciones")
        logger.info(f"Modo: {'DRY RUN (sin cambios)' if self.dry_run else 'EJECUCIÓN REAL'}")
        
        if limit:
            logger.info(f"Límite: {limit} presentaciones")
        
        async for session in get_async_session():
            try:
                presentations = await self.get_presentations_needing_questions(session, limit)
                
                for i, presentation in enumerate(presentations, 1):
                    logger.info(f"\n--- Procesando {i}/{len(presentations)}: {presentation.title or presentation.id} ---")
                    await self.process_presentation(session, presentation)
                
                # Mostrar estadísticas finales
                logger.info("\n" + "="*60)
                logger.info("📊 RESUMEN FINAL:")
                logger.info(f"Total presentaciones revisadas: {self.stats['total_presentations']}")
                logger.info(f"Ya tenían preguntas: {self.stats['presentations_with_questions']}")
                logger.info(f"Sin slides válidos: {self.stats['presentations_without_slides']}")
                logger.info(f"Preguntas agregadas: {self.stats['questions_added']}")
                logger.info(f"Errores: {self.stats['errors']}")
                logger.info("="*60)
                
                if self.dry_run:
                    logger.info("🔍 Esto fue un DRY RUN - no se realizaron cambios reales")
                else:
                    logger.info("✅ Proceso completado con cambios reales")
                
            except Exception as e:
                logger.error(f"❌ Error crítico: {str(e)}")
                raise
            finally:
                await session.close()


async def main():
    """
    Función principal del script.
    """
    parser = argparse.ArgumentParser(
        description="Agregar slides de preguntas a presentaciones existentes"
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true', 
        help='Solo mostrar qué haría sin hacer cambios reales'
    )
    parser.add_argument(
        '--limit', 
        type=int, 
        help='Procesar solo las primeras N presentaciones'
    )
    
    args = parser.parse_args()
    
    updater = PresentationQuestionsUpdater(dry_run=args.dry_run)
    await updater.run(limit=args.limit)


if __name__ == "__main__":
    asyncio.run(main())
