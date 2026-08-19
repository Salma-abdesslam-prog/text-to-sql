"""
Schema Extractor — reads table/column definitions from the connected database
and formats them as a human-readable string for the LLM prompt.
"""

from sqlalchemy import inspect, text


def extract_schema(engine) -> str:
    """
    Introspect the database and return a schema string in the format:

        TABLE customers
          - id         INTEGER  (primary key)
          - name       TEXT
          - email      TEXT
          ...

        TABLE orders
          ...

    Works for both SQLite and MySQL engines.
    """
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    if not table_names:
        return "No tables found in the database."

    lines = []
    for table in table_names:
        lines.append(f"TABLE {table}")
        columns = inspector.get_columns(table)
        pk_cols = {pk for pk in inspector.get_pk_constraint(table).get("constrained_columns", [])}
        fk_map  = {
            fk["constrained_columns"][0]: f"{fk['referred_table']}.{fk['referred_columns'][0]}"
            for fk in inspector.get_foreign_keys(table)
            if fk["constrained_columns"]
        }

        for col in columns:
            col_name = col["name"]
            col_type = str(col["type"])
            notes = []
            if col_name in pk_cols:
                notes.append("primary key")
            if col_name in fk_map:
                notes.append(f"FK → {fk_map[col_name]}")
            if not col.get("nullable", True):
                notes.append("NOT NULL")
            note_str = f"  ({', '.join(notes)})" if notes else ""
            lines.append(f"  - {col_name:<20} {col_type}{note_str}")

        # Add indexes as a hint
        indexes = inspector.get_indexes(table)
        for idx in indexes:
            if not idx.get("unique"):
                continue
            lines.append(f"  UNIQUE ({', '.join(idx['column_names'])})")

        lines.append("")  # blank line between tables

    return "\n".join(lines)


def get_table_names(engine) -> list[str]:
    """Return the list of table names in the connected database."""
    return inspect(engine).get_table_names()


def get_row_count(engine, table: str) -> int:
    """Return the total number of rows in a table."""
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
        return result.scalar() or 0


def get_sample_rows(engine, table: str, limit: int = 3) -> list[dict]:
    """Return a few sample rows from a table for context."""
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT * FROM {table} LIMIT {limit}"))
        keys = result.keys()
        return [dict(zip(keys, row)) for row in result.fetchall()]
