"""
Main Text-to-SQL pipeline: ties together LLM, prompt builder, and validator.
"""

from core.llm_client import LLMClient
from core.prompt_builder import build_system_prompt, build_user_prompt
from core.sql_validator import validate_sql, format_sql, SQLValidationError


class TextToSQL:
    """
    Convert a natural language question into a validated SQL query.

    Usage:
        converter = TextToSQL(api_key="gsk_...", model="openai/gpt-oss-120b")
        sql = converter.convert(question="...", schema="...", dialect="SQLite")
    """

    def __init__(self, api_key: str, model: str = "openai/gpt-oss-120b"):
        self.llm = LLMClient(api_key=api_key, model=model)

    def convert(
        self,
        question: str,
        schema: str,
        dialect: str = "SQLite",
    ) -> dict:
        """
        Convert a natural language question to SQL.

        Returns a dict with:
            - sql (str)        : cleaned & validated SQL
            - formatted (str)  : pretty-printed SQL
            - raw (str)        : raw LLM output (for debugging)
            - error (str|None) : validation error message if any
        """
        system_prompt = build_system_prompt(schema=schema, dialect=dialect)
        user_prompt   = build_user_prompt(question=question)

        raw = self.llm.generate(system_prompt=system_prompt, user_message=user_prompt)

        try:
            sql       = validate_sql(raw)
            formatted = format_sql(sql)
            return {"sql": sql, "formatted": formatted, "raw": raw, "error": None}
        except SQLValidationError as e:
            return {"sql": None, "formatted": None, "raw": raw, "error": str(e)}
