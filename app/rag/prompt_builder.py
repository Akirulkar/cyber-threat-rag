from pathlib import Path
from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)


class PromptBuilder:
    """Manages system and user prompt templates."""

    def __init__(
        self,
        system_prompt_path: str = "app/prompts/system_prompt.txt",
        answer_prompt_path: str = "app/prompts/answer_prompt.txt",
    ):
        self.system_prompt_raw = Path(system_prompt_path).read_text(encoding="utf-8")
        self.answer_prompt_raw = Path(answer_prompt_path).read_text(encoding="utf-8")

        self.chat_prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(self.system_prompt_raw),
                HumanMessagePromptTemplate.from_template(self.answer_prompt_raw),
            ]
        )

    def format(self, context: str, question: str) -> str:
        """Formats context and question into prompt messages."""
        return self.chat_prompt.format_prompt(
            context=context, question=question
        ).to_messages()
