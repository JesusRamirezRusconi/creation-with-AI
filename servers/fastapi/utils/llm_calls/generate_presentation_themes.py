from datetime import datetime
from typing import Optional

from models.llm_message import LLMSystemMessage, LLMUserMessage
from models.llm_tools import SearchWebTool
from models.presentation_outline_model import ThemesResponseModel
from services.llm_client import LLMClient
from utils.llm_client_error_handler import handle_llm_client_exceptions
from utils.llm_provider import get_model


def get_themes_system_prompt(
    tone: Optional[str] = None,
    verbosity: Optional[str] = None,
    instructions: Optional[str] = None,
):
    return f"""
        You are an expert presentation creator specializing in generating diverse and creative themes for presentations.

        Your task is to generate 10 different and unique presentation themes based on the user's content.
        Each theme should be completely different from the others, exploring various angles, perspectives, and approaches to the topic.

        For each theme, provide:
        1. A creative and descriptive title
        2. A brief description explaining the theme's unique approach
        3. A complete presentation outline with slides

        Try to use available tools for better results.

        {"# User Instruction:" if instructions else ""}
        {instructions or ""}

        {"# Tone:" if tone else ""}
        {tone or ""}

        {"# Verbosity:" if verbosity else ""}
        {verbosity or ""}

        Guidelines for themes:
        - Generate exactly 10 different themes
        - Each theme should have a unique perspective or angle
        - Themes should be creative and diverse
        - Each theme must include a complete presentation structure
        - Provide content for each slide in markdown format
        - Make sure the flow of each presentation is logical and consistent
        - Place greater emphasis on numerical data where applicable
        - No images should be provided in the content
        - Content must follow language guidelines
        - User instructions should always be followed

        **Search web to get latest information about the topic**
    """


def get_themes_user_prompt(
    content: str,
    n_slides: int,
    language: str,
    additional_context: Optional[str] = None,
):
    return f"""
        **Input:**
        - User provided content: {content or "Create presentation themes"}
        - Output Language: {language}
        - Number of Slides per Theme: {n_slides}
        - Current Date and Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        - Additional Information: {additional_context or ""}

        Generate 10 completely different and creative themes for this presentation topic.
        Each theme should explore a unique angle or perspective.
    """


def get_themes_messages(
    content: str,
    n_slides: int,
    language: str,
    additional_context: Optional[str] = None,
    tone: Optional[str] = None,
    verbosity: Optional[str] = None,
    instructions: Optional[str] = None,
):
    return [
        LLMSystemMessage(
            content=get_themes_system_prompt(
                tone, verbosity, instructions
            ),
        ),
        LLMUserMessage(
            content=get_themes_user_prompt(content, n_slides, language, additional_context),
        ),
    ]


async def generate_presentation_themes(
    content: str,
    n_slides: int,
    language: Optional[str] = None,
    additional_context: Optional[str] = None,
    tone: Optional[str] = None,
    verbosity: Optional[str] = None,
    instructions: Optional[str] = None,
    web_search: bool = False,
):
    model = get_model()
    response_model = ThemesResponseModel

    client = LLMClient()

    try:
        async for chunk in client.stream_structured(
            model,
            get_themes_messages(
                content,
                n_slides,
                language,
                additional_context,
                tone,
                verbosity,
                instructions,
            ),
            response_model.model_json_schema(),
            strict=True,
            tools=(
                [SearchWebTool]
                if (client.enable_web_grounding() and web_search)
                else None
            ),
        ):
            yield chunk
    except Exception as e:
        yield handle_llm_client_exceptions(e)
