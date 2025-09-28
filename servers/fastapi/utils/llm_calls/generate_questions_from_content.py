"""
Utilidad para generar preguntas específicas basadas en el contenido de una presentación
usando IA para crear preguntas relevantes al tema específico.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from models.llm_message import LLMSystemMessage, LLMUserMessage
from services.llm_client import LLMClient
from utils.llm_client_error_handler import handle_llm_client_exceptions
from utils.llm_provider import get_model

logger = logging.getLogger(__name__)

class QuestionOption(BaseModel):
    text: str
    is_correct: bool

class GeneratedQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: int  # Índice de la respuesta correcta (0-3)
    explanation: str

class QuestionsResponse(BaseModel):
    questions: List[GeneratedQuestion]

@handle_llm_client_exceptions
async def generate_questions_from_presentation_content(
    presentation_content: str,
    num_questions: int = 5,
    language: str = "es",
    outlines: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Genera preguntas específicas basadas en el contenido de una presentación.

    Args:
        presentation_content: El contenido completo de la presentación
        num_questions: Número de preguntas a generar (por defecto 5)
        language: Idioma para las preguntas (por defecto español)
        outlines: Lista de outlines/subtemas para basar las preguntas (opcional)

    Returns:
        Lista de diccionarios con las preguntas generadas
    """

    # Usar LLMClient para generar preguntas
    client = LLMClient()
    logger.info("Using LLMClient for question generation")

    # Si tenemos outlines, usarlos como base en lugar del contenido generado
    if outlines:
        outlines_text = "\n\n".join([f"Subtema {i+1}: {outline.get('content', '')}" for i, outline in enumerate(outlines)])
        base_content = f"Basado en los siguientes subtemas de la presentación:\n\n{outlines_text}"
        logger.info(f"Using {len(outlines)} outlines as base for questions")
    else:
        base_content = presentation_content
    
    # Truncar contenido si es muy largo para evitar límites de tokens
    max_content_length = 4000
    if len(base_content) > max_content_length:
        base_content = base_content[:max_content_length] + "..."

    # Prompts específicos por idioma
    prompts = {
        "es": {
            "system": """Eres un experto en crear evaluaciones educativas. Tu tarea es generar preguntas de opción múltiple específicas y relevantes basadas en los subtemas de una presentación.

INSTRUCCIONES IMPORTANTES:
1. Las preguntas DEBEN ser específicas a los subtemas proporcionados, NO genéricas
2. Cada pregunta debe tener exactamente 4 opciones de respuesta
3. Solo UNA opción debe ser correcta
4. Las opciones incorrectas deben ser plausibles pero claramente incorrectas
5. Incluye una explicación clara de por qué la respuesta es correcta
6. Las preguntas deben cubrir diferentes aspectos de los subtemas

Responde ÚNICAMENTE con un JSON válido en este formato exacto:
{
  "questions": [
    {
      "question": "Pregunta específica sobre los subtemas",
      "options": ["Opción A", "Opción B", "Opción C", "Opción D"],
      "correct_answer": 0,
      "explanation": "Explicación clara de por qué esta respuesta es correcta"
    }
  ]
}""",
            "user": f"""Analiza los siguientes subtemas de una presentación y genera {num_questions} preguntas específicas de opción múltiple:

SUBTEMAS DE LA PRESENTACIÓN:
{base_content}

GENERA {num_questions} PREGUNTAS ESPECÍFICAS que evalúen la comprensión de estos subtemas. Las preguntas deben ser sobre:
- Conceptos clave mencionados en los subtemas
- Detalles específicos de cada subtema
- Relaciones entre diferentes subtemas
- Información importante presentada en los subtemas

IMPORTANTE: Las preguntas NO deben ser genéricas como "¿Cuál es el tema principal?". Deben ser específicas y basadas directamente en el contenido de los subtemas proporcionados."""
        },
        "en": {
            "system": """You are an expert in creating educational assessments. Your task is to generate specific and relevant multiple-choice questions based on presentation subtopics.

IMPORTANT INSTRUCTIONS:
1. Questions MUST be specific to the provided subtopics, NOT generic
2. Each question must have exactly 4 answer options
3. Only ONE option should be correct
4. Incorrect options should be plausible but clearly wrong
5. Include a clear explanation of why the answer is correct
6. Questions should cover different aspects of the subtopics

Respond ONLY with valid JSON in this exact format:
{
  "questions": [
    {
      "question": "Specific question about the subtopics",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_answer": 0,
      "explanation": "Clear explanation of why this answer is correct"
    }
  ]
}""",
            "user": f"""Analyze the following presentation subtopics and generate {num_questions} specific multiple-choice questions:

PRESENTATION SUBTOPICS:
{base_content}

GENERATE {num_questions} SPECIFIC QUESTIONS that assess understanding of these subtopics. Questions should be about:
- Key concepts mentioned in the subtopics
- Specific details of each subtopic
- Relationships between different subtopics
- Important information presented in the subtopics

IMPORTANT: Questions should NOT be generic like "What is the main topic?". They must be specific and based directly on the provided subtopics content."""
        }
    }

    selected_prompts = prompts.get(language, prompts["es"])

    try:
        # Generar preguntas usando IA
        logger.info(f"Generating {num_questions} questions from {'outlines' if outlines else 'content'} (length: {len(base_content)})")

        # Usar cliente estándar
        response = await client.generate_response(
            messages=[
                LLMSystemMessage(content=selected_prompts["system"]),
                LLMUserMessage(content=selected_prompts["user"])
            ],
            model=get_model(),
            max_tokens=2000,
            temperature=0.7
        )
        
        if not response.content:
            raise Exception("Empty response from LLM")
        
        # Parsear respuesta JSON
        try:
            response_json = json.loads(response.content)
            questions_data = QuestionsResponse(**response_json)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Raw response: {response.content}")
            raise Exception("Invalid JSON response from LLM")
        except Exception as e:
            logger.error(f"Error validating questions data: {e}")
            raise Exception("Invalid questions format from LLM")
        
        # Convertir a formato esperado por el frontend
        formatted_questions = []
        for i, q in enumerate(questions_data.questions):
            formatted_question = {
                "id": i + 1,
                "question": q.question,
                "options": q.options,
                "correctAnswer": q.correct_answer,
                "explanation": q.explanation
            }
            formatted_questions.append(formatted_question)
        
        logger.info(f"Successfully generated {len(formatted_questions)} questions")
        return formatted_questions
        
    except Exception as e:
        logger.error(f"Error generating questions: {str(e)}")
        
        # Fallback: generar preguntas básicas basadas en análisis simple del contenido
        logger.info("Falling back to basic content-based questions")
        return generate_fallback_questions(presentation_content, num_questions, language, outlines)

def generate_fallback_questions(
    content: str,
    num_questions: int,
    language: str,
    outlines: Optional[List[Dict[str, Any]]] = None
) -> List[Dict[str, Any]]:
    """
    Genera preguntas específicas analizando el contenido sin IA como fallback.
    Analiza el contenido para extraer información específica y generar preguntas relevantes.
    """

    # Usar outlines si están disponibles, sino usar el contenido
    if outlines and len(outlines) > 0:
        analysis_content = "\n\n".join([outline.get('content', '') for outline in outlines])
        logger.info(f"Using {len(outlines)} outlines for fallback question generation")
    else:
        analysis_content = content

    # Análisis más sofisticado del contenido
    content_lower = analysis_content.lower()
    
    # Extraer números, estadísticas y datos específicos
    import re
    numbers = re.findall(r'\d+[%+]?|\d+\.\d+', content)
    percentages = re.findall(r'\d+%', content)
    years = re.findall(r'\b(19|20)\d{2}\b', content)
    
    # Buscar conceptos clave (palabras capitalizadas o en negritas)
    key_concepts = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
    
    # Extraer frases importantes (que contengan palabras clave)
    important_phrases = []
    key_indicators = ['es', 'son', 'incluye', 'consiste', 'significa', 'representa', 'alcanzó', 'logró']
    sentences = content.split('.')
    for sentence in sentences:
        if any(indicator in sentence.lower() for indicator in key_indicators):
            important_phrases.append(sentence.strip())
    
    # Obtener palabras más frecuentes (temas principales)  
    words = re.findall(r'\b[a-zA-ZñÑáéíóúÁÉÍÓÚ]{4,}\b', content)
    word_freq = {}
    for word in words:
        if word.lower() not in ['para', 'con', 'que', 'por', 'como', 'una', 'del', 'las', 'los', 'este', 'esta']:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    main_topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Generar preguntas dinámicas basadas en el análisis
    generated_questions = []
    
    # Pregunta 1: Sobre el tema principal (usando palabras clave)
    main_topic = main_topics[0][0] if main_topics else "tema principal"
    question_1 = {
        "question": f"¿Cuál es el concepto clave relacionado con '{main_topic}' en esta presentación?",
        "options": [
            f"Un aspecto general de {main_topic}",
            f"El concepto específico sobre {main_topic} que se desarrolla",
            f"Una mención casual de {main_topic}",
            f"Un tema diferente a {main_topic}"
        ],
        "correctAnswer": 1,
        "explanation": f"El concepto de {main_topic} es central en esta presentación y se desarrolla específicamente."
    }
    generated_questions.append(question_1)
    
    # Pregunta 2: Sobre números/estadísticas (si existen)
    if numbers and len(numbers) > 0:
        number = numbers[0]
        question_2 = {
            "question": f"¿Qué representa la cifra '{number}' mencionada en la presentación?",
            "options": [
                f"Un dato aproximado relacionado con {main_topic}",
                f"La estadística específica presentada sobre {main_topic}",
                f"Un número sin relevancia",
                f"Una referencia a otro tema"
            ],
            "correctAnswer": 1,
            "explanation": f"La cifra {number} es un dato específico importante mencionado en la presentación."
        }
    else:
        question_2 = {
            "question": f"¿Qué aspecto específico de {main_topic} se destaca en la presentación?",
            "options": [
                f"Una característica general",
                f"El aspecto clave de {main_topic} que se presenta",
                f"Un detalle menor",
                f"Un tema no relacionado"
            ],
            "correctAnswer": 1,
            "explanation": f"Se destaca un aspecto específico importante de {main_topic}."
        }
    generated_questions.append(question_2)
    
    # Pregunta 3: Sobre conceptos secundarios
    second_topic = main_topics[1][0] if len(main_topics) > 1 else "concepto clave"
    question_3 = {
        "question": f"¿Cómo se relaciona '{second_topic}' con el tema principal?",
        "options": [
            f"No tiene relación directa",
            f"Es un elemento fundamental que complementa {main_topic}",
            f"Es un tema completamente separado",
            f"Solo se menciona brevemente"
        ],
        "correctAnswer": 1,
        "explanation": f"{second_topic} es un concepto importante que se integra con el tema principal."
    }
    generated_questions.append(question_3)
    
    # Pregunta 4: Sobre años/fechas (si existen)
    if years and len(years) > 0:
        year = years[0]
        question_4 = {
            "question": f"¿Qué importancia tiene el año {year} en el contexto de la presentación?",
            "options": [
                f"Es una fecha sin relevancia específica",
                f"Marca un momento importante relacionado con {main_topic}",
                f"Se menciona por casualidad",
                f"No tiene conexión con el tema"
            ],
            "correctAnswer": 1,
            "explanation": f"El año {year} representa un momento significativo en el desarrollo del tema."
        }
    else:
        question_4 = {
            "question": f"¿Cuál es la conclusión principal sobre {main_topic}?",
            "options": [
                f"Una observación general",
                f"La conclusión específica presentada sobre {main_topic}",
                f"No hay conclusiones claras",
                f"Se necesita más información"
            ],
            "correctAnswer": 1,
            "explanation": f"La presentación llega a conclusiones específicas sobre {main_topic}."
        }
    generated_questions.append(question_4)
    
    # Pregunta 5: Sobre el impacto o importancia
    question_5 = {
        "question": f"¿Por qué es importante el tema de {main_topic} según la presentación?",
        "options": [
            f"Por razones generales",
            f"Por el impacto específico que se describe en la presentación",
            f"No se explica su importancia",
            f"Solo es un tema de interés académico"
        ],
        "correctAnswer": 1,
        "explanation": f"La presentación explica específicamente por qué {main_topic} es relevante e importante."
    }
    generated_questions.append(question_5)
    
    # Asignar IDs únicos y retornar las preguntas generadas
    for i, question in enumerate(generated_questions):
        question["id"] = i + 1
    
    # Limitar al número solicitado
    final_questions = generated_questions[:num_questions]
    
    # Si necesitamos más preguntas, generar variaciones
    while len(final_questions) < num_questions:
        base_index = len(final_questions) % len(generated_questions)
        base_question = generated_questions[base_index].copy()
        base_question["id"] = len(final_questions) + 1
        base_question["question"] = f"Según el análisis del contenido, {base_question['question'].lower()}"
        final_questions.append(base_question)
    
    return final_questions
