"""
OpenAI Service Module

This service handles all interactions with OpenAI's language models for text summarization.
It provides methods to generate focused summaries of scientific publications about
gene-disease relationships.

Responsibilities:
- OpenAI model configuration and management
- Text chunking and processing
- Prompt generation and optimization
- Summary generation using LangChain

Author: Open Targets AI API
"""

import logging
from openai import OpenAI
from app.config import get_config

# Configure module logger
logger = logging.getLogger(__name__)

logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Get configuration
config = get_config()

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

# Initialize OpenAI model with configuration
client = OpenAI(
    api_key=config.OPENAI_API_KEY,
)

# =============================================================================
# PROMPT GENERATION
# =============================================================================


def create_focused_prompt(target_symbol: str, disease_name: str) -> str:
    """
    Create a focused prompt for the summarization model.

    This function generates a specific prompt that asks the AI to focus on
    the relationship between a target gene/protein and a disease based on
    the provided scientific publication.

    Args:
        target_symbol (str): The gene/protein symbol of interest
        disease_name (str): The name of the disease to investigate

    Returns:
        str: Formatted prompt for the AI model

    Example:
        >>> create_focused_prompt("BRCA1", "breast cancer")
        'Can you provide a concise summary about the relationship between BRCA1 and breast cancer according to this study?'
    """
    return (
        f"Can you provide a concise paragraph summarising the relationship between "
        f"{target_symbol} and {disease_name} according to this study?"
    )


# =============================================================================
# SUMMARY GENERATION SERVICE
# =============================================================================


def generate_publication_summary(
    text: str, target_symbol: str, disease_name: str, pmc_id: str
) -> dict:
    """
    Generate a focused summary from publication text using OpenAI.

    This function processes the full text of a scientific publication and
    generates a summary focused on the relationship between a specific
    target gene/protein and a disease.

    Args:
        text (str): Full text of the publication
        target_symbol (str): Gene/protein symbol of interest
        disease_name (str): Disease name to focus on
        pmc_id (str): PMC ID for logging and tracking

    Returns:
        dict: Dictionary containing the generated summary and metadata

    Raises:
        RuntimeError: If summary generation fails
        ValueError: If input parameters are invalid

    Example:
        >>> result = generate_publication_summary(
        ...     publication_text, "BRCA1", "breast cancer", "PMC1234567"
        ... )
        >>> print(result["summary"])
    """
    # Validate inputs
    if not text or not text.strip():
        raise ValueError("Publication text cannot be empty")
    if not target_symbol or not target_symbol.strip():
        raise ValueError("Target symbol cannot be empty")
    if not disease_name or not disease_name.strip():
        raise ValueError("Disease name cannot be empty")

    try:
        logger.info(
            f"Generating summary for PMC {pmc_id}: {target_symbol} vs {disease_name}"
        )

        # Create focused prompt
        prompt = create_focused_prompt(target_symbol, disease_name)

        response = client.responses.create(
            model="gpt-5-mini",
            input=prompt + text,
            instructions="You are an expert in drug discovery. The paragraph should be clear, scientifically accurate and no more than 100 words",
        )
        return response.output_text

    except Exception as e:
        logger.error(f"Error generating summary for PMC {pmc_id}: {e}")
        raise RuntimeError(f"Failed to generate publication summary: {str(e)}")
