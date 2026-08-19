"""
Query Executor — runs a validated SQL query and returns results as a list of dicts.
Only SELECT queries are allowed; the validator upstream should already enforce this.
"""

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError


class QueryExecutionError(Exception):
    pass


def execute_query(engine, sql: str) -> pd.DataFrame:
    """
    Execute a SELECT query and return results as a Pandas DataFrame.
    Raises QueryExecutionError on database errors.
    """
    sql = sql.strip().rstrip(";")  # remove trailing semicolon for safety

    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql))
            columns = list(result.keys())
            rows    = result.fetchall()

        if not rows:
            return pd.DataFrame(columns=columns)

        return pd.DataFrame(rows, columns=columns)

    except SQLAlchemyError as e:
        # Extract a clean error message
        msg = str(e.orig) if hasattr(e, "orig") and e.orig else str(e)
        raise QueryExecutionError(msg) from e
