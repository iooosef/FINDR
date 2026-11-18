"""
seed.py - Database setup and initialization script.
Run this script once to create the SQLite database tables and seed the default staff account.
Usage: python backend/seed.py
"""

import os
import sqlite3
import bcrypt

# Path to the SQLite database file
DB_PATH = os.path.join(os.path.dirname(__file__), "findr.db")

def hash_password(password: str) -> str:
    """Hashes a password string using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def init_db():
    # Connect to (or create) the SQLite database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable foreign key support in SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        username      TEXT NOT NULL UNIQUE,  -- Student ID or staff username
        full_name     TEXT NOT NULL,
        role          TEXT NOT NULL CHECK(role IN ('student', 'staff')),
        password_hash TEXT NOT NULL,
        created_at    TEXT DEFAULT (datetime('now'))
    );
    """)

    # 2. missing_tickets table (student reports)
    cursor.execute("""
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
    """)

    # 3. lost_item_tickets table (staff logs for found items)
    cursor.execute("""
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
    """)

    # 4. matches table (links missing ticket to lost item ticket)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        missing_ticket_id INTEGER NOT NULL REFERENCES missing_tickets(id),
        lost_item_id      INTEGER NOT NULL REFERENCES lost_item_tickets(id),
        match_score       REAL,            -- confidence score 0.0 to 1.0
        status            TEXT NOT NULL DEFAULT 'pending'
                              CHECK(status IN ('pending', 'verified', 'rejected')),
        created_at        TEXT DEFAULT (datetime('now'))
    );
    """)

    # 5. notifications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL REFERENCES users(id),
        message    TEXT NOT NULL,
        is_read    INTEGER NOT NULL DEFAULT 0,  -- 0 = unread, 1 = read
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)

    # Seed initial staff account
    staff_username = "admin"
    staff_fullname = "FINDR Administrator"
    staff_password = "adminpassword123"  # Default staff credentials

    cursor.execute("SELECT id FROM users WHERE username = ?", (staff_username,))
    existing_staff = cursor.fetchone()

    if not existing_staff:
        hashed_pw = hash_password(staff_password)
        cursor.execute(
            "INSERT INTO users (username, full_name, role, password_hash) VALUES (?, ?, 'staff', ?)",
            (staff_username, staff_fullname, hashed_pw)
        )
        print(f"Default staff account created: Username='{staff_username}', Password='{staff_password}'")
    else:
        print(f"Staff account '{staff_username}' already exists.")

    # Seed sample student accounts
    sample_students = [
        {
            "username": "2026-0001",
            "full_name": "Juan Dela Cruz",
            "password": "studentpassword123"
        },
        {
            "username": "2026-0002",
            "full_name": "Maria Clara Santos",
            "password": "studentpassword123"
        }
    ]

    for student in sample_students:
        cursor.execute("SELECT id FROM users WHERE username = ?", (student["username"],))
        if not cursor.fetchone():
            hashed_student_pw = hash_password(student["password"])
            cursor.execute(
                "INSERT INTO users (username, full_name, role, password_hash) VALUES (?, ?, 'student', ?)",
                (student["username"], student["full_name"], hashed_student_pw)
            )
            print(f"Student account created: ID='{student['username']}', Name='{student['full_name']}', Password='{student['password']}'")
        else:
            print(f"Student account '{student['username']}' already exists.")

    conn.commit()
    conn.close()
    print(f"Database setup complete at: {DB_PATH}")


if __name__ == "__main__":
    init_db()
