"""
SQL Validator — cleans and validates the SQL returned by the LLM.
"""

import re
import sqlparse


# Dangerous keywords that should never appear in generated SQL
FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
    "TRUNCATE", "CREATE", "REPLACE", "MERGE", "EXEC",
    "EXECUTE", "GRANT", "REVOKE",
]


class SQLValidationError(Exception):
    pass


def clean_sql(raw: str) -> str:
    """
    Strip markdown code fences and extra whitespace from the LLM output.
    Models sometimes wrap the SQL in ```sql ... ``` even when told not to.
    """
    # Remove ```sql ... ``` or ``` ... ```
    cleaned = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "")

    # Remove leading/trailing whitespace and collapse internal newlines
    cleaned = cleaned.strip()

    # If there are multiple statements, take only the first SELECT
    statements = sqlparse.split(cleaned)
    if statements:
        cleaned = statements[0].strip()

    return cleaned


def validate_sql(sql: str) -> str:
    """
    Validate that the SQL is safe and syntactically plausible.
    Returns the cleaned SQL or raises SQLValidationError.
    """
    if not sql:
        raise SQLValidationError("The model returned an empty response.")

    cleaned = clean_sql(sql)

    if not cleaned:
        raise SQLValidationError("Could not extract a SQL query from the model response.")

    # Check for forbidden keywords (case-insensitive, word boundary)
    upper = cleaned.upper()
    for kw in FORBIDDEN_KEYWORDS:
        pattern = r"\b" + kw + r"\b"
        if re.search(pattern, upper):
            raise SQLValidationError(
                f"The generated query contains a forbidden keyword: {kw}. "
                "Only SELECT queries are allowed."
            )

    # Must start with SELECT or WITH (CTEs)
    first_word = upper.lstrip().split()[0] if upper.strip() else ""
    if first_word not in ("SELECT", "WITH"):
        raise SQLValidationError(
            f"Expected a SELECT query, but got: '{first_word}'. "
            "Please rephrase your question."
        )

    return cleaned


def format_sql(sql: str) -> str:
    """Pretty-print SQL for display."""
    return sqlparse.format(
        sql,
        reindent=True,
        keyword_case="upper",
        identifier_case="lower",
        strip_comments=True,
    )
