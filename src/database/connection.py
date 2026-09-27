"""DuckDB connection management for the unrot brain training app."""

from __future__ import annotations

from pathlib import Path

import duckdb

from src.database.schema import get_all_schema_sql, get_default_user_sql

DB_DIR = Path.home() / ".unrot"
DB_PATH = DB_DIR / "unrot.duckdb"

_connection: duckdb.DuckDBPyConnection | None = None


def get_connection(db_path: Path | str | None = None) -> duckdb.DuckDBPyConnection:
    """Get or create a DuckDB connection.

    Args:
        db_path: Optional custom database path. Defaults to ~/.unrot/unrot.duckdb.

    Returns:
        A DuckDB connection.
    """
    global _connection

    if _connection is not None and db_path is None:
        return _connection

    path = Path(db_path) if db_path is not None else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    _connection = duckdb.connect(str(path))
    _connection.execute("SET timezone='UTC'")
    return _connection


def initialize_database(conn: duckdb.DuckDBPyConnection | None = None) -> None:
    """Create all tables if they don't exist and insert default user.

    Args:
        conn: Optional connection. Uses get_connection() if not provided.
    """
    if conn is None:
        conn = get_connection()

    for statement in get_all_schema_sql():
        conn.execute(statement)

    conn.execute(get_default_user_sql())


def close_connection(conn: duckdb.DuckDBPyConnection | None = None) -> None:
    """Close the DuckDB connection.

    Args:
        conn: Optional connection. Uses the module-level connection if not provided.
    """
    global _connection

    if conn is not None:
        conn.close()
    elif _connection is not None:
        _connection.close()
        _connection = None


def reset_connection() -> None:
    """Reset the module-level connection (for testing)."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
