"""Export service for presentation export operations.

This service handles exporting presentations to various formats
like PPTX and PDF.
"""

import os
from typing import Literal, Optional
from uuid import UUID, uuid4

from core.exceptions import PresentationExportException, PresentationNotFoundException
from core.logging import get_logger
from models.presentation_and_path import PresentationAndPath
from models.pptx_models import PptxPresentationModel
from services.pptx_presentation_creator import PptxPresentationCreator
from services.temp_file_service import TEMP_FILE_SERVICE
from utils.asset_directory_utils import get_exports_directory
from utils.export_utils import export_presentation as export_presentation_util

logger = get_logger(__name__)


class ExportService:
    """Service for exporting presentations to different formats.
    
    This service wraps and orchestrates export functionality for
    presentations.
    """

    async def export_presentation(
        self,
        presentation_id: UUID,
        title: str,
        export_format: Literal["pptx", "pdf"] = "pptx",
    ) -> PresentationAndPath:
        """Export a presentation to specified format.

        Args:
            presentation_id: ID of presentation to export
            title: Presentation title for filename
            export_format: Format to export ("pptx" or "pdf")

        Returns:
            Presentation with export path

        Raises:
            PresentationNotFoundException: If presentation not found
            PresentationExportException: If export fails
        """
        logger.info(
            f"Exporting presentation {presentation_id} as {export_format}"
        )
        
        try:
            result = await export_presentation_util(
                presentation_id,
                title,
                export_format,
            )
            
            logger.info(
                f"Successfully exported presentation: {result.path}"
            )
            return result
            
        except Exception as e:
            logger.exception(
                f"Failed to export presentation {presentation_id}"
            )
            raise PresentationExportException(
                f"Failed to export presentation as {export_format}",
                export_format=export_format,
                details={"presentation_id": str(presentation_id), "error": str(e)},
            )

    async def export_pptx_from_model(
        self,
        pptx_model: PptxPresentationModel,
        filename: Optional[str] = None,
    ) -> str:
        """Export a presentation from PPTX model.

        Args:
            pptx_model: PPTX presentation model
            filename: Optional custom filename

        Returns:
            Path to exported file

        Raises:
            PresentationExportException: If export fails
        """
        logger.info("Exporting presentation from PPTX model")
        
        try:
            temp_dir = TEMP_FILE_SERVICE.create_temp_dir()
            
            pptx_creator = PptxPresentationCreator(pptx_model, temp_dir)
            await pptx_creator.create_ppt()
            
            export_directory = get_exports_directory()
            filename = filename or pptx_model.name or str(uuid4())
            pptx_path = os.path.join(export_directory, f"{filename}.pptx")
            
            pptx_creator.save(pptx_path)
            
            logger.info(f"Successfully exported PPTX to: {pptx_path}")
            return pptx_path
            
        except Exception as e:
            logger.exception("Failed to export PPTX from model")
            raise PresentationExportException(
                "Failed to export presentation from PPTX model",
                export_format="pptx",
                details={"error": str(e)},
            )
