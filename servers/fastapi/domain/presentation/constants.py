"""Constants for presentation module.

Centralized constants to avoid magic numbers and improve maintainability.
"""

# Slide generation
DEFAULT_BATCH_SIZE = 10
MAX_TOC_SLIDES_PER_PAGE = 10
MIN_SLIDES_FOR_TOC = 3
OUTLINE_PREVIEW_LENGTH = 100

# Questions generation
DEFAULT_QUESTIONS_COUNT = 5
MIN_CONTENT_LENGTH_FOR_EXTRACTION = 20
MIN_TEXT_LENGTH_FOR_FIELD = 50

# Asset processing
IMAGE_GENERATION_CONCURRENCY = 10

# Status messages
STATUS_GENERATING_OUTLINES = "Generating presentation outlines"
STATUS_SELECTING_LAYOUTS = "Selecting layout for each slide"
STATUS_GENERATING_SLIDES = "Generating slides"
STATUS_FETCHING_ASSETS = "Fetching assets for slides"
STATUS_EXPORTING = "Exporting presentation"
STATUS_COMPLETED = "Presentation generation completed"
STATUS_FAILED = "Presentation generation failed"
STATUS_QUEUED = "Queued for generation"
