from typing import List, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str = Field(..., description="Role of speaker: 'user' or 'assistant'")
    content: str = Field(..., description="Message text content")


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="The threat intelligence query or CVE search.",
        example="What is CVE-2024-3094?",
    )
    top_k: int = Field(
        default=5, ge=1, le=20, description="Number of documents to retrieve."
    )
    chat_history: Optional[List[Message]] = Field(
        default=[],
        description="Previous conversation turns to maintain multi-turn chat context.",
    )
