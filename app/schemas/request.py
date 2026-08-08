from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        description="The threat intelligence query or CVE search.",
        example="What is CVE-2024-3094?",
    )
    top_k: int = Field(
        default=5, ge=1, le=20, description="Number of documents to retrieve."
    )
