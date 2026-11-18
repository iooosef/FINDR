"""
models.py - Database schemas and constants for FINDR.

This file defines the SQL schemas for all 5 SQLite tables:
1. users             - Student and staff accounts
2. missing_tickets   - Reports filed by students ("Lost Something?")
3. lost_item_tickets - Found items logged by staff ("Found Something?")
4. matches           - Links missing reports to found items
5. notifications     - In-app notification alerts
"""

import sqlite3

# Valid categories matching the student report form
CATEGORIES = [
    "ID & Cards",
    "Electronics",
    "Clothing",
    "Bags",
    "School Supplies",
    "Books",
    "Accessories",
    "Sports Gear",
    "Personal Items",
    "Others",
]

# Valid user roles
ROLES = ["student", "staff"]

# Valid missing ticket statuses
MISSING_STATUSES = ["open", "matched", "resolved"]

# Valid lost item ticket statuses
LOST_ITEM_STATUSES = ["unclaimed", "pending_verification", "claimed"]

# Valid match statuses
MATCH_STATUSES = ["pending", "verified", "rejected"]

# SQL statements to create all tables
CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,  -- Student ID or staff username
    full_name     TEXT NOT NULL,
    role          TEXT NOT NULL CHECK(role IN ('student', 'staff')),
    password_hash TEXT NOT NULL,
    created_at    TEXT DEFAULT (datetime('now'))
);
"""

CREATE_MISSING_TICKETS_TABLE = """
CREATE TABLE IF NOT EXISTS missing_tickets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id  INTEGER NOT NULL REFERENCES users(id),
    item_name   TEXT NOT NULL,
    category    TEXT NOT NULL,
    brand       TEXT,
    color       TEXT,
    date_lost   TEXT NOT NULL,       -- ISO date string e.g. 2026-09-11
    time_lost   TEXT,                -- e.g. "Around 10:30 AM"
    locations   TEXT NOT NULL,       -- free text e.g. "Library, Canteen"
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'open'
                    CHECK(status IN ('open', 'matched', 'resolved')),
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);
"""

CREATE_LOST_ITEM_TICKETS_TABLE = """
CREATE TABLE IF NOT EXISTS lost_item_tickets (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    logged_by      INTEGER NOT NULL REFERENCES users(id),  -- staff user
    item_name      TEXT NOT NULL,
    category       TEXT NOT NULL,
    brand          TEXT,
    color          TEXT,
    date_found     TEXT NOT NULL,
    time_found     TEXT,
    location_found TEXT NOT NULL,
    description    TEXT,
    status         TEXT NOT NULL DEFAULT 'unclaimed'
                       CHECK(status IN ('unclaimed', 'pending_verification', 'claimed')),
    created_at     TEXT DEFAULT (datetime('now')),
    updated_at     TEXT DEFAULT (datetime('now'))
);
"""

CREATE_MATCHES_TABLE = """
CREATE TABLE IF NOT EXISTS matches (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    missing_ticket_id INTEGER NOT NULL REFERENCES missing_tickets(id),
    lost_item_id      INTEGER NOT NULL REFERENCES lost_item_tickets(id),
    match_score       REAL,            -- confidence score 0.0 to 1.0
    status            TEXT NOT NULL DEFAULT 'pending'
                          CHECK(status IN ('pending', 'verified', 'rejected')),
    created_at        TEXT DEFAULT (datetime('now'))
);
"""

CREATE_NOTIFICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS notifications (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    message    TEXT NOT NULL,
    is_read    INTEGER NOT NULL DEFAULT 0,  -- 0 = unread, 1 = read
    created_at TEXT DEFAULT (datetime('now'))
);
"""


def create_all_tables(conn: sqlite3.Connection):
    """
    Executes table creation queries on the provided connection.
    Safe to call multiple times because all statements use CREATE TABLE IF NOT EXISTS.
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute(CREATE_USERS_TABLE)
    cursor.execute(CREATE_MISSING_TICKETS_TABLE)
    cursor.execute(CREATE_LOST_ITEM_TICKETS_TABLE)
    cursor.execute(CREATE_MATCHES_TABLE)
    cursor.execute(CREATE_NOTIFICATIONS_TABLE)
    conn.commit()
