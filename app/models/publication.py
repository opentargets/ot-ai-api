import re

from pydantic import BaseModel, Field, field_validator


class PublicationPlainTextRequest(BaseModel):
    pmc_id: str = Field(..., description='PMC ID of the publication')


class PublicationSummaryPayload(BaseModel):
    pmcId: str = Field(..., description='PMC ID of the publication')
    targetSymbol: str = Field(..., max_length=20, description='Target gene symbol')
    diseaseName: str = Field(..., max_length=100, description='Name of the disease')
    includeReferences: bool = Field(
        False,
        description='Whether to include references section (may increase token usage)',
    )

    @field_validator('targetSymbol', 'diseaseName')
    @classmethod
    def sanitize_input(cls, v: str) -> str:
        v = v.strip()
        v = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', v)
        if not v:
            raise ValueError('Field cannot be empty')
        return v


class PublicationSummaryRequest(BaseModel):
    payload: PublicationSummaryPayload = Field(..., description='Envelope containing summary request parameters')
