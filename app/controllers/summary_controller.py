"""
Summary Controller Module

This controller handles HTTP requests related to publication summarization.
It coordinates with the OpenAI service to generate focused summaries about
gene-disease relationships from scientific publications.

Responsibilities:
- Handle HTTP requests and responses for summary generation
- Validate summary request parameters
- Coordinate with OpenAI service
- Format summary responses

Author: Open Targets AI API
"""

import logging
from fastapi import HTTPException
from app.services.openai_service import generate_publication_summary

# Configure module logger
logger = logging.getLogger(__name__)


# =============================================================================
# CONTROLLER FUNCTIONS
# =============================================================================


def create_publication_summary(
    text: str, target_symbol: str, disease_name: str, pmc_id: str
) -> dict:
    """
    Controller function to create a focused publication summary.

    This function acts as a thin layer between the HTTP endpoint and the service,
    handling request validation and delegating the actual work to the service layer.

    Args:
        text (str): Full text of the publication
        target_symbol (str): Gene/protein symbol of interest
        disease_name (str): Disease name to focus on
        pmc_id (str): PMC ID for logging and tracking

    Returns:
        dict: Dictionary containing the generated summary and metadata

    Raises:
        HTTPException: For various error conditions during processing

    Example:
        >>> result = create_publication_summary(
        ...     publication_text, "BRCA1", "breast cancer", "PMC1234567"
        ... )
        >>> print(result["summary"])
    """
    try:
        # Validate input parameters
        if not text or len(text.strip()) < 100:
            raise HTTPException(
                status_code=422,
                detail="Publication text is too short or empty for meaningful summary",
            )

        if not target_symbol or not target_symbol.strip():
            raise HTTPException(status_code=422, detail="Target symbol cannot be empty")

        if not disease_name or not disease_name.strip():
            raise HTTPException(status_code=422, detail="Disease name cannot be empty")

        if not pmc_id or not pmc_id.strip():
            raise HTTPException(status_code=422, detail="PMC ID cannot be empty")

        # Clean input parameters
        target_symbol = target_symbol.strip()
        disease_name = disease_name.strip()
        pmc_id = pmc_id.strip()

        # Log the request
        logger.info(
            f"Processing summary request for PMC {pmc_id}: {target_symbol} vs {disease_name}"
        )

        # Delegate to service layer
        result = generate_publication_summary(text, target_symbol, disease_name, pmc_id)

        logger.info(f"Successfully generated summary for PMC {pmc_id}")
        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        # Convert validation errors to HTTP exceptions
        logger.error(f"Validation error for PMC {pmc_id}: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in summary controller for PMC {pmc_id}: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error while generating summary"
        )
