"""
Database connector — supports SQLite (test mode) and MySQL (production).
Returns a SQLAlchemy engine.
"""

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError


def get_sqlite_engine(db_path: str):
    """Connect to a local SQLite database file."""
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    return engine


def get_mysql_engine(host: str, port: int, database: str, username: str, password: str):
    """
    Connect to a MySQL database using PyMySQL.
    Raises OperationalError if the connection fails.
    """
    url = (
        f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
        "?charset=utf8mb4"
    )
    engine = create_engine(url, echo=False, pool_pre_ping=True)

    # Test the connection immediately
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    return engine


def test_connection(engine) -> bool:
    """Return True if the engine can reach the database."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
