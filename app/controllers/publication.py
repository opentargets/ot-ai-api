"""Publication Controller Module.

This controller handles HTTP requests related to scientific publications.
It coordinates with the Europe PMC service to fetch and process publication content.

Responsibilities:
- Handle HTTP requests and responses
- Validate request parameters
- Coordinate with services
- Format responses

Author: Open Targets AI API
"""

import logging

from fastapi import HTTPException

from app.services.europe_pmc_service import extract_publication_text

# Configure module logger
logger = logging.getLogger(__name__)


# =============================================================================
# CONTROLLER FUNCTIONS
# =============================================================================


def fetch_plain_text_from_europe_pmc(pmc_id: str, include_references: bool = False) -> str:
    r"""Controller function to fetch and extract plain text from a Europe PMC publication.

    This function acts as a thin layer between the HTTP endpoint and the service,
    handling request validation and delegating the actual work to the service layer.

    Args:
        pmc_id (str): The PMC ID of the publication to fetch
        include_references (bool): Whether to include references section (default: False)

    Returns:
        str: Complete plain text content of the publication

    Raises:
        HTTPException: For various error conditions during processing

    Example:
        >>> text = fetch_plain_text_from_europe_pmc('PMC1234567')
        >>> print(text[:100])
        'TITLE: Example Research Article\n\nABSTRACT: This study examines...'
    """
    try:
        # Validate PMC ID format (basic validation)
        if not pmc_id or not pmc_id.strip():
            raise HTTPException(status_code=400, detail='PMC ID cannot be empty')

        # Remove any whitespace
        pmc_id = pmc_id.strip()

        # Log the request
        logger.info(f'Processing publication request for PMC ID: {pmc_id}')

        # Delegate to service layer
        result = extract_publication_text(pmc_id, include_references)

        # Validate result
        if not result or len(result.strip()) < 10:
            raise HTTPException(status_code=422, detail='Publication text is too short or empty')

        logger.info(f'Successfully processed publication for PMC ID: {pmc_id}')
        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f'Unexpected error in controller for PMC ID {pmc_id}: {e}')
        raise HTTPException(status_code=500, detail='Internal server error while processing publication')
