import os
from typing import List, Optional
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from app.core.config import NVIDIA_API_KEY
from app.core.logger import logger


class LLMEngine:
    """Wrapper around LangChain Chat models (NVIDIA NIM / Nemotron / Ollama)."""

    def __init__(
        self,
        provider: str = "nvidia",
        model_name: str = "nvidia/nemotron-3-nano-30b-a3b",
        temperature: float = 1.0,
        top_p: float = 1.0,
        max_tokens: int = 16384,
        reasoning_budget: int = 16384,
        api_key: Optional[str] = None,
    ):
        self.provider = provider
        self.model_name = model_name

        logger.info(f"Initializing LLMEngine [{provider}] with model '{model_name}'...")

        if provider == "nvidia":
            key = NVIDIA_API_KEY
            if not key:
                raise ValueError(
                    "NVIDIA_API_KEY is not set in environment or passed to LLMEngine."
                )

            # Pass extra_body parameters (e.g. reasoning_budget) to NVIDIA API
            extra_body = {}
            if reasoning_budget > 0:
                extra_body["reasoning_budget"] = reasoning_budget

            self.llm = ChatOpenAI(
                model=self.model_name,
                openai_api_key=key,
                openai_api_base="https://integrate.api.nvidia.com/v1",
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                extra_body=extra_body if extra_body else None,
            )

        elif provider == "ollama":
            self.llm = ChatOllama(
                model=self.model_name,
                temperature=temperature,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def generate(self, messages: List[BaseMessage]) -> str:
        """Generates text response given prompt messages."""
        response = self.llm.invoke(messages)
        return response.content
