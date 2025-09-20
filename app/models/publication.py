from pydantic import BaseModel, Field


class PublicationPlainTextRequest(BaseModel):
    pmc_id: str = Field(..., description="PMC ID of the publication")


class PublicationSummaryRequest(BaseModel):
    pmcId: str = Field(..., description="PMC ID of the publication")
    targetSymbol: str = Field(..., description="Target gene symbol")
    diseaseName: str = Field(..., description="Name of the disease")
    includeReferences: bool = Field(
        False,
        description="Whether to include references section (may increase token usage)",
    )
