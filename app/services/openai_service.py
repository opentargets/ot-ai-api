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
from langchain.chains.summarize import load_summarize_chain
from langchain_openai import ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from app.config import get_config

# Configure module logger
logger = logging.getLogger(__name__)

# Reduce LangChain logging verbosity
logging.getLogger("langchain").setLevel(logging.WARNING)
logging.getLogger("langchain.chains").setLevel(logging.WARNING)
logging.getLogger("langchain_openai").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Get configuration
config = get_config()

# =============================================================================
# MODEL CONFIGURATION
# =============================================================================

# Initialize OpenAI model with configuration
model = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key=config.OPENAI_API_KEY,
    temperature=0.5,
    max_tokens=1000,
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
        f"Can you provide a concise summary about the relationship between "
        f"{target_symbol} and {disease_name} according to this study? "
    )


# =============================================================================
# TEXT PROCESSING UTILITIES
# =============================================================================


def split_text_into_chunks(text: str, chunk_size: int = 14000) -> list:
    """
    Split large text into manageable chunks for processing.

    Args:
        text (str): The text to split
        chunk_size (int): Maximum size of each chunk

    Returns:
        list: List of document chunks ready for processing
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=200,  # Add overlap to maintain context
        separators=["\n\n", "\n", ". ", " "],
        length_function=len,
    )

    documents = text_splitter.create_documents([text])
    logger.info(f"Split text into {len(documents)} chunks (max size: {chunk_size})")

    return documents


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

        # Analyze text size and prepare chunks
        word_count = len(text.split())
        char_count = len(text)
        logger.info(f"Processing text: {word_count} words, {char_count} characters")

        # Split text into manageable chunks
        documents = split_text_into_chunks(text)

        # Create custom prompt templates for focused summarization
        map_template = f"""
        {prompt}
        
        Based on this portion of the scientific publication:
        {{text}}
        
        Provide relevant information about the relationship between the target and disease.
        """

        combine_template = f"""
        {prompt}
        
        Based on the following summaries from different sections:
        {{text}}
        
        Provide a comprehensive summary focusing on the relationship between the target and disease.
        """

        map_prompt = PromptTemplate(template=map_template, input_variables=["text"])
        combine_prompt = PromptTemplate(
            template=combine_template, input_variables=["text"]
        )

        # Initialize the summarization chain with custom prompts (modern approach)
        chain = load_summarize_chain(
            llm=model,
            chain_type="map_reduce",
            map_prompt=map_prompt,
            combine_prompt=combine_prompt,
            verbose=False,
        )

        # Generate summary using the modern LangChain approach
        logger.info(f"Processing {len(documents)} text chunks with OpenAI...")
        logger.info("Executing map-reduce summarization...")

        # Use the invoke method (modern LangChain approach)
        api_response = chain.invoke({"input_documents": documents})
        logger.info("OpenAI summarization completed successfully")

        # Extract the text from the response (handle both dict and string responses)
        if isinstance(api_response, dict):
            summary_text = api_response.get("output_text", "")
        else:
            # If response is a string directly (from run method)
            summary_text = str(api_response)

        # Validate response
        if not summary_text or not summary_text.strip():
            raise RuntimeError("OpenAI returned empty response")

        logger.info(f"Successfully generated summary ({len(summary_text)} characters)")

        return {
            "summary": summary_text.strip(),
            "pmc_id": pmc_id,
            "target_symbol": target_symbol,
            "disease_name": disease_name,
            "word_count": word_count,
            "chunks_processed": len(documents),
        }

    except Exception as e:
        logger.error(f"Error generating summary for PMC {pmc_id}: {e}")
        raise RuntimeError(f"Failed to generate publication summary: {str(e)}")


# =============================================================================
# HEALTH CHECK AND UTILITIES
# =============================================================================


def check_openai_connection() -> bool:
    """
    Check if OpenAI service is accessible and properly configured.

    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        # Simple test to verify OpenAI connection
        test_response = model.invoke("Hello")
        return bool(test_response)
    except Exception as e:
        logger.error(f"OpenAI connection check failed: {e}")
        return False


def get_model_info() -> dict:
    """
    Get information about the current OpenAI model configuration.

    Returns:
        dict: Model configuration details
    """
    return {
        "model_name": model.model_name,
        "temperature": model.temperature,
        "max_tokens": model.max_tokens,
        "api_key_configured": bool(config.OPENAI_API_KEY),
    }
