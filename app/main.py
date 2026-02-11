from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse
from app.config import get_config
from app.controllers.publication import fetch_plain_text_from_europe_pmc
from app.models.publication import (
    PublicationPlainTextRequest,
    PublicationSummaryRequest,
)
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


config = get_config()

app = FastAPI(debug=config.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": f"Welcome to {config.APP_NAME}"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the service is working properly.

    Returns:
        JSON response with service status and basic system information
    """
    try:
        import time
        from datetime import datetime

        # Basic health check response
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": config.APP_NAME,
            "version": "1.0.0",
            "uptime": time.time(),
            "checks": {"api": "ok", "config": "ok" if config else "error"},
        }

        # Optional: Add more detailed checks here
        # For example, you could test database connections, external APIs, etc.

        logger.info("Health check performed successfully")
        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )


@app.post("/literature/publication/plaintext/")
async def get_publication_plain_text(request: PublicationPlainTextRequest):
    try:
        logger.info(f"Fetching publication text for PMC ID: {request.pmc_id}")
        plain_text = fetch_plain_text_from_europe_pmc(request.pmc_id)
        return {"pmc_id": request.pmc_id, "plain_text": plain_text}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred")


def handle_publication_summary_request(request: PublicationSummaryRequest) -> dict:
    """
    Logic for creating publication summaries.

    This function coordinates the process of:
    1. Fetching the publication text from Europe PMC
    2. Generating a focused summary using OpenAI

    Args:
        request: PublicationSummaryRequest containing PMC ID, target symbol, and disease name

    Returns:
        dict: Summary response with metadata

    Raises:
        HTTPException: For various error conditions during processing
    """
    try:
        payload = request.payload
        logger.info(f"Processing summary request for PMC {payload.pmcId}")

        # Step 1: Fetch publication text
        logger.info(f"Fetching publication text for PMC {payload.pmcId}")
        publication_text = fetch_plain_text_from_europe_pmc(
            payload.pmcId, include_references=payload.includeReferences
        )

        if not publication_text or len(publication_text.strip()) < 100:
            raise HTTPException(
                status_code=422,
                detail="Publication text is too short or empty for meaningful summary",
            )

        # Step 2: Generate summary
        logger.info(
            f"Generating summary for {payload.targetSymbol} vs {payload.diseaseName}"
        )
        from app.controllers.summary_controller import create_publication_summary

        summary_result = create_publication_summary(
            text=publication_text,
            target_symbol=payload.targetSymbol,
            disease_name=payload.diseaseName,
            pmc_id=payload.pmcId,
        )

        logger.info(f"Successfully generated summary for PMC {payload.pmcId}")
        return summary_result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing PMC {payload.pmcId}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process publication summary: {str(e)}"
        )


@app.post("/literature/publication/summary/")
async def create_publication_summary(request: PublicationSummaryRequest):
    """
    Create a focused summary of a publication regarding a specific gene-disease relationship.

    This endpoint fetches a scientific publication from Europe PMC and generates
    an AI-powered summary focused on the relationship between a target gene/protein
    and a specific disease.

    Args:
        request: JSON body containing:
            - pmcId: PMC ID of the publication
            - targetSymbol: Gene/protein symbol of interest
            - diseaseName: Disease name to focus on
            - includeReferences: Whether to include references (optional, default: false)

    Returns:
        JSON response with the generated summary and metadata

    Example:
        POST /literature/publication/summary/
        {
            "pmcId": "PMC1234567",
            "targetSymbol": "BRCA1",
            "diseaseName": "breast cancer",
            "includeReferences": false
        }
    """
    return handle_publication_summary_request(request)


# Error habdler
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={
                "error": "Endpoint not found",
                "detail": f"The requested URL {request.url.path} was not found on the server",
            },
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )
