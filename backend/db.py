"""
Database connection and initialization module for SQLite.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "backtesting.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "..", "schema_sqlite.sql")


def get_db():
    """Get a database connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # Enable FK enforcement
    return conn


def init_db():
    """Initialize the database by executing the SQLite schema.
    Drops the trigger and view first so the script is fully idempotent.
    """
    conn = get_db()
    try:
        with open(SCHEMA_PATH, "r") as f:
            schema_script = f.read()
        # Prepend DROP statements so CREATE TRIGGER / CREATE VIEW don't fail on re-runs.
        # executescript() implicitly commits, so we bundle everything into one script.
        idempotent_script = (
            "DROP TRIGGER IF EXISTS trg_validate_portfolio_weights;\n"
            "DROP VIEW IF EXISTS v_portfolio_allocation_history;\n"
            + schema_script
        )
        conn.executescript(idempotent_script)
    finally:
        conn.close()
    print(f"Database initialized at {DB_PATH}")


def query_db(query, args=(), one=False):
    """Execute a SELECT query and return results as list of dicts."""
    conn = get_db()
    cur = conn.execute(query, args)
    rows = cur.fetchall()
    conn.close()
    results = [dict(row) for row in rows]
    return results[0] if one and results else results if not one else None


def execute_db(query, args=()):
    """Execute an INSERT/UPDATE/DELETE query and return lastrowid."""
    conn = get_db()
    try:
        cur = conn.execute(query, args)
        conn.commit()
        lastrowid = cur.lastrowid
        conn.close()
        return lastrowid
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e


def execute_many_db(query, data):
    """Execute a bulk INSERT using executemany for batch operations."""
    conn = get_db()
    try:
        conn.executemany(query, data)
        conn.commit()
        conn.close()
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e


if __name__ == "__main__":
    init_db()
