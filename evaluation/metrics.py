import os
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
)
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.core.config import settings
from langchain_community.embeddings import HuggingFaceEmbeddings


def get_ragas_evaluator_models():
    """Initializes evaluator LLM and Embeddings using NVIDIA NIM endpoints."""
    evaluator_llm = ChatOpenAI(
        model=settings.NVIDIA_MODEL,
        openai_api_key=settings.NVIDIA_API_KEY,
        openai_api_base="https://integrate.api.nvidia.com/v1",
        temperature=0.0,
    )

    evaluator_embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-base-en-v1.5",
        model_kwargs={"device": "cuda"},
    )

    return evaluator_llm, evaluator_embeddings


EVALUATION_METRICS = [
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
]
