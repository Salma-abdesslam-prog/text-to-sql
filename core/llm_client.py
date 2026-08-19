"""
LLM Client — supports Groq (primary) with open-source models.
Other providers (Together AI, OpenRouter) can be added easily.
"""

from groq import Groq


GROQ_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
]


class LLMClient:
    """Wrapper around Groq API for open-source LLM inference."""

    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b"):
        self.client = Groq(api_key=api_key)
        self.model = model

    def generate(self, system_prompt: str, user_message: str, temperature: float = 0.1) -> str:
        """
        Send a prompt to the LLM and return the raw text response.
        Low temperature (0.1) for deterministic SQL generation.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
            temperature=temperature,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()
