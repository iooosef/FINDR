"""
database.py - Database connection setup for FINDR.

This file provides a helper function to connect to the SQLite database.
It sets row_factory to sqlite3.Row so you can access columns by name (e.g., row['username']).
It also enables PRAGMA foreign_keys so references between tables are strictly enforced.
"""

import os
import sqlite3
from contextlib import contextmanager

# Absolute path to findr.db inside the backend directory
DB_PATH = os.path.join(os.path.dirname(__file__), "findr.db")


def get_db_connection() -> sqlite3.Connection:
    """
    Creates and returns a connection to the SQLite database.
    - sqlite3.Row allows column access by name: user['username'] instead of user[1]
    - foreign_keys = ON ensures relational integrity between tables
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db():
    """
    Context manager for database operations.
    Automatically commits changes on success and rolls back if an error occurs.
    Always closes the connection when finished.

    Usage example:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
