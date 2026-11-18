"""
seed.py - Database setup and initialization script for FINDR.

Creates the SQLite database tables and seeds:
1. Default staff account ('admin')
2. Sample student accounts ('2026-0001' through '2026-0005')
3. Comprehensive lost & missing tickets representing all realistic scenarios:
   - Received/Claimed items (resolved missing ticket + claimed lost item + verified match)
   - Not yet received items (unmatched 'open' missing tickets & 'unclaimed' lost items)
   - Matched items not yet received (single pending match awaiting student verification)
   - Conflicting matches: One Lost Item matched to Many Missing Reports ('pending_verification')
   - Conflicting matches: One Missing Report matched to Many Lost Items (multiple potential matches)
4. Correlated notifications for students and staff.

Usage:
    python backend/seed.py          # Initialize & seed if empty
    python backend/seed.py --reset  # Wipe and reseed cleanly
"""

import sys
import os
import sqlite3
import bcrypt

# Path to the SQLite database file
DB_PATH = os.path.join(os.path.dirname(__file__), "findr.db")


def hash_password(password: str) -> str:
    """Hashes a password string using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def init_db(force_reseed: bool = False):
    """
    Initializes SQLite tables and seeds initial users & sample tickets.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON;")

    if force_reseed:
        print("🧹 Wiping existing database tables for clean reseed...")
        cursor.execute("DROP TABLE IF EXISTS notifications;")
        cursor.execute("DROP TABLE IF EXISTS matches;")
        cursor.execute("DROP TABLE IF EXISTS lost_item_tickets;")
        cursor.execute("DROP TABLE IF EXISTS missing_tickets;")
        cursor.execute("DROP TABLE IF EXISTS users;")

    # ==========================================
    # 1. Table Definitions
    # ==========================================

    # users table
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

    # missing_tickets table (student reports)
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

    # lost_item_tickets table (staff logs for found items)
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

    # matches table (links missing ticket to lost item ticket)
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

    # notifications table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id         INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL REFERENCES users(id),
        message    TEXT NOT NULL,
        is_read    INTEGER NOT NULL DEFAULT 0,  -- 0 = unread, 1 = read
        created_at TEXT DEFAULT (datetime('now'))
    );
    """)

    # ==========================================
    # 2. Seed Users
    # ==========================================

    # Staff Account
    staff_username = "admin"
    staff_fullname = "FINDR Administrator"
    staff_password = "adminpassword123"

    cursor.execute("SELECT id FROM users WHERE username = ?", (staff_username,))
    staff_row = cursor.fetchone()
    if not staff_row:
        hashed_pw = hash_password(staff_password)
        cursor.execute(
            "INSERT INTO users (username, full_name, role, password_hash) VALUES (?, ?, 'staff', ?)",
            (staff_username, staff_fullname, hashed_pw)
        )
        staff_id = cursor.lastrowid
        print(f"✅ Staff account seeded: Username='{staff_username}', Password='{staff_password}'")
    else:
        staff_id = staff_row[0]

    # Sample Student Accounts
    sample_students = [
        {"username": "2026-0001", "full_name": "Juan Dela Cruz", "password": "studentpassword123"},
        {"username": "2026-0002", "full_name": "Maria Clara Santos", "password": "studentpassword123"},
        {"username": "2026-0003", "full_name": "Mark Joseph Bautista", "password": "studentpassword123"},
        {"username": "2026-0004", "full_name": "Angelo Reyes", "password": "studentpassword123"},
        {"username": "2026-0005", "full_name": "Alyssa Mae Rivera", "password": "studentpassword123"}
    ]

    student_id_map = {}
    for student in sample_students:
        cursor.execute("SELECT id FROM users WHERE username = ?", (student["username"],))
        s_row = cursor.fetchone()
        if not s_row:
            hashed_student_pw = hash_password(student["password"])
            cursor.execute(
                "INSERT INTO users (username, full_name, role, password_hash) VALUES (?, ?, 'student', ?)",
                (student["username"], student["full_name"], hashed_student_pw)
            )
            student_id_map[student["username"]] = cursor.lastrowid
            print(f"✅ Student account seeded: ID='{student['username']}', Name='{student['full_name']}'")
        else:
            student_id_map[student["username"]] = s_row[0]

    conn.commit()

    # ==========================================
    # 3. Seed Comprehensive Sample Tickets & Matches
    # ==========================================

    cursor.execute("SELECT COUNT(*) FROM missing_tickets;")
    missing_count = cursor.fetchone()[0]

    if missing_count == 0 or force_reseed:
        print("\n📦 Seeding realistic sample tickets across all workflow states...")

        # ----------------------------------------------------
        # SCENARIO 1: RECEIVED / RETURNED (Resolved & Claimed)
        # ----------------------------------------------------
        # Juan reported a lost Casio calculator. Staff found it, verified him in-person,
        # and handed it back. Status: missing='resolved', lost='claimed', match='verified'.
        cursor.execute("""
            INSERT INTO missing_tickets (
                student_id, item_name, category, brand, color,
                date_lost, time_lost, locations, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'resolved', datetime('now', '-7 days'), datetime('now', '-5 days'))
        """, (
            student_id_map["2026-0001"],
            "Black Casio Scientific Calculator",
            "Electronics",
            "Casio",
            "Black",
            "2026-11-10",
            "Around 10:00 AM",
            "Library 2nd Floor",
            "Casio fx-991CW with CCC Math Club sticker on the rear cover"
        ))
        t1_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO lost_item_tickets (
                logged_by, item_name, category, brand, color,
                date_found, time_found, location_found, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'claimed', datetime('now', '-7 days'), datetime('now', '-5 days'))
        """, (
            staff_id,
            "Casio fx-991CW Scientific Calculator",
            "Electronics",
            "Casio",
            "Black",
            "2026-11-10",
            "11:30 AM",
            "Library Reading Area Table 4",
            "Black calculator with yellow sticker on protective cover, surrendered by librarian"
        ))
        l1_id = cursor.lastrowid

        # Verified Match
        cursor.execute("""
            INSERT INTO matches (missing_ticket_id, lost_item_id, match_score, status, created_at)
            VALUES (?, ?, 0.95, 'verified', datetime('now', '-6 days'))
        """, (t1_id, l1_id))

        # Notifications for Scenario 1
        cursor.execute("""
            INSERT INTO notifications (user_id, message, is_read, created_at) VALUES
            (?, 'We found a possible match for your missing ''Black Casio Scientific Calculator''. Please visit the Lost and Found Office for in-person verification.', 1, datetime('now', '-6 days')),
            (?, 'Your missing item ''Black Casio Scientific Calculator'' has been successfully verified and returned. Ticket resolved.', 1, datetime('now', '-5 days')),
            (?, 'Lost item #1 (Casio fx-991CW) has been returned and claimed by Juan Dela Cruz.', 1, datetime('now', '-5 days'))
        """, (student_id_map["2026-0001"], student_id_map["2026-0001"], staff_id))

        # ----------------------------------------------------
        # SCENARIO 2: NOT YET RECEIVED (Open / Unclaimed - No Match)
        # ----------------------------------------------------
        # 2A. Maria reported a lost AquaFlask. No one has turned it in yet.
        cursor.execute("""
            INSERT INTO missing_tickets (
                student_id, item_name, category, brand, color,
                date_lost, time_lost, locations, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', datetime('now', '-3 days'), datetime('now', '-3 days'))
        """, (
            student_id_map["2026-0002"],
            "AquaFlask 32oz Insulated Tumbler",
            "Personal Items",
            "AquaFlask",
            "Olive Green",
            "2026-11-15",
            "Around 2:15 PM",
            "Gymnasium Bleachers, Canteen",
            "32oz olive green flask with black silicone boot and small dent near bottom"
        ))
        t2_id = cursor.lastrowid

        # 2B. Maria lost a calculus textbook. No one has turned it in yet.
        cursor.execute("""
            INSERT INTO missing_tickets (
                student_id, item_name, category, brand, color,
                date_lost, time_lost, locations, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', datetime('now', '-2 days'), datetime('now', '-2 days'))
        """, (
            student_id_map["2026-0002"],
            "Calculus and Analytic Geometry 9th Edition",
            "Books",
            "Thomas",
            "Blue and White",
            "2026-11-16",
            "11:00 AM",
            "Library Study Carrel 14",
            "Hardcover textbook with handwritten study notes inside chapter 4"
        ))
        t3_id = cursor.lastrowid

        # 2C. Staff logged a found silver watch. No student has reported it yet.
        cursor.execute("""
            INSERT INTO lost_item_tickets (
                logged_by, item_name, category, brand, color,
                date_found, time_found, location_found, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'unclaimed', datetime('now', '-2 days'), datetime('now', '-2 days'))
        """, (
            staff_id,
            "Silver Stainless Steel Watch",
            "Accessories",
            "Fossil",
            "Silver",
            "2026-11-16",
            "4:45 PM",
            "Balbago Building Restroom 1st Floor",
            "Men's wristwatch with metal link strap, found on sink counter"
        ))
        l2_id = cursor.lastrowid

        # 2D. Staff logged a CCC PE jacket. No student has reported it yet.
        cursor.execute("""
            INSERT INTO lost_item_tickets (
                logged_by, item_name, category, brand, color,
                date_found, time_found, location_found, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'unclaimed', datetime('now', '-1 days'), datetime('now', '-1 days'))
        """, (
            staff_id,
            "CCC College PE Jacket",
            "Clothing",
            "CCC Tailoring",
            "Yellow and Charcoal",
            "2026-11-17",
            "5:15 PM",
            "Gymnasium Bleachers Row 3",
            "Size Medium college department jacket with embroidered seal"
        ))
        l3_id = cursor.lastrowid

        # ----------------------------------------------------
        # SCENARIO 3: MATCHED AND NOT YET RECEIVED (Single Pending Match)
        # ----------------------------------------------------
        # Mark lost his leather ID holder. Staff logged a matching found ID holder.
        # Match detected! Mark was notified, but has NOT yet visited the office.
        # Status: missing='matched', lost='unclaimed', match='pending'.
        cursor.execute("""
            INSERT INTO missing_tickets (
                student_id, item_name, category, brand, color,
                date_lost, time_lost, locations, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'matched', datetime('now', '-2 days'), datetime('now', '-1 days'))
        """, (
            student_id_map["2026-0003"],
            "Brown Leather CCC ID Holder with Lanyard",
            "ID & Cards",
            "Generic",
            "Brown",
            "2026-11-16",
            "9:45 AM recess",
            "Balbago Building Hallway",
            "CCC maroon/gold lanyard with brown leather sleeve holding Student ID and Beep card"
        ))
        t4_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO lost_item_tickets (
                logged_by, item_name, category, brand, color,
                date_found, time_found, location_found, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'unclaimed', datetime('now', '-2 days'), datetime('now', '-1 days'))
        """, (
            staff_id,
            "Brown ID Holder with CCC Lanyard",
            "ID & Cards",
            "Generic",
            "Brown",
            "2026-11-16",
            "10:30 AM",
            "Balbago Quadrangle near flagpole",
            "Leather ID holder with lanyard, surrendered by campus guard on duty"
        ))
        l4_id = cursor.lastrowid

        # Pending Match
        cursor.execute("""
            INSERT INTO matches (missing_ticket_id, lost_item_id, match_score, status, created_at)
            VALUES (?, ?, 0.88, 'pending', datetime('now', '-1 days'))
        """, (t4_id, l4_id))

        cursor.execute("""
            INSERT INTO notifications (user_id, message, is_read, created_at) VALUES
            (?, 'We found a possible match for your missing ''Brown Leather CCC ID Holder with Lanyard''. Please visit the Lost and Found Office for in-person verification.', 0, datetime('now', '-1 days')),
            (?, 'Match found: Missing Report #4 matches Found Item #4 (ID Holder). Awaiting student in-person verification.', 0, datetime('now', '-1 days'))
        """, (student_id_map["2026-0003"], staff_id))

        # ----------------------------------------------------
        # SCENARIO 4: CONFLICTING MATCH — ONE LOST, MANY MISSING
        # ----------------------------------------------------
        # Staff logged found Apple AirPods Pro in Canteen.
        # Two different students (Juan and Angelo) both reported lost AirPods Pro in Canteen!
        # Status: lost='pending_verification', both missing='matched', both matches='pending'.
        cursor.execute("""
            INSERT INTO lost_item_tickets (
                logged_by, item_name, category, brand, color,
                date_found, time_found, location_found, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending_verification', datetime('now', '-1 days'), datetime('now', '-12 hours'))
        """, (
            staff_id,
            "Apple AirPods Pro 2nd Gen in White Case",
            "Electronics",
            "Apple",
            "White",
            "2026-11-17",
            "1:30 PM",
            "College Canteen Table 12",
            "White charging case with minor surface scuffs, turned in by canteen staff"
        ))
        l5_id = cursor.lastrowid

        # Student Juan's Missing Report
        cursor.execute("""
            INSERT INTO missing_tickets (
                student_id, item_name, category, brand, color,
                date_lost, time_lost, locations, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'matched', datetime('now', '-1 days'), datetime('now', '-12 hours'))
        """, (
            student_id_map["2026-0001"],
            "Apple AirPods Pro Charging Case",
            "Electronics",
            "Apple",
            "White",
            "2026-11-17",
            "Around 12:45 PM",
            "Canteen, Balbago ground floor",
            "AirPods Pro white case with small blue ink dot near the metal hinge"
        ))
        t5_id = cursor.lastrowid

        # Student Angelo's Missing Report
        cursor.execute("""
            INSERT INTO missing_tickets (
                student_id, item_name, category, brand, color,
                date_lost, time_lost, locations, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'matched', datetime('now', '-1 days'), datetime('now', '-12 hours'))
        """, (
            student_id_map["2026-0004"],
            "White Apple AirPods Pro 2",
            "Electronics",
            "Apple",
            "White",
            "2026-11-17",
            "1:15 PM lunch",
            "Canteen or Balbago Room 102",
            "AirPods Pro 2 in white case, slight yellow sticker residue on the front"
        ))
        t6_id = cursor.lastrowid

        # Matches for Scenario 4 (both pending)
        cursor.execute("""
            INSERT INTO matches (missing_ticket_id, lost_item_id, match_score, status, created_at)
            VALUES (?, ?, 0.90, 'pending', datetime('now', '-12 hours'))
        """, (t5_id, l5_id))

        cursor.execute("""
            INSERT INTO matches (missing_ticket_id, lost_item_id, match_score, status, created_at)
            VALUES (?, ?, 0.90, 'pending', datetime('now', '-12 hours'))
        """, (t6_id, l5_id))

        cursor.execute("""
            INSERT INTO notifications (user_id, message, is_read, created_at) VALUES
            (?, 'We found a possible match for your missing ''Apple AirPods Pro Charging Case''. Please visit the Lost and Found Office for in-person verification.', 0, datetime('now', '-12 hours')),
            (?, 'We found a possible match for your missing ''White Apple AirPods Pro 2''. Please visit the Lost and Found Office for in-person verification.', 0, datetime('now', '-12 hours')),
            (?, 'CONFLICT ALERT: 2 missing reports match Found Item #5 (Apple AirPods Pro). Item status transitioned to ''pending_verification''. Staff in-person verification required.', 0, datetime('now', '-12 hours'))
        """, (student_id_map["2026-0001"], student_id_map["2026-0004"], staff_id))

        # ----------------------------------------------------
        # SCENARIO 5: CONFLICTING MATCH — ONE MISSING, MANY LOST
        # ----------------------------------------------------
        # Alyssa lost a Black Fibrella umbrella. Staff has logged TWO different black umbrellas
        # found in that vicinity! Alyssa's ticket matches both items.
        # Status: Alyssa's ticket='matched', both found items='pending_verification', matches='pending'.
        cursor.execute("""
            INSERT INTO missing_tickets (
                student_id, item_name, category, brand, color,
                date_lost, time_lost, locations, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'matched', datetime('now', '-1 days'), datetime('now', '-6 hours'))
        """, (
            student_id_map["2026-0005"],
            "Black Folding Umbrella",
            "Personal Items",
            "Fibrella",
            "Black",
            "2026-11-17",
            "3:30 PM dismissal",
            "Balbago Building, Canteen",
            "Automatic 3-fold black umbrella with black wrist cord and silver release button"
        ))
        t7_id = cursor.lastrowid

        # Found Item A
        cursor.execute("""
            INSERT INTO lost_item_tickets (
                logged_by, item_name, category, brand, color,
                date_found, time_found, location_found, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending_verification', datetime('now', '-1 days'), datetime('now', '-6 hours'))
        """, (
            staff_id,
            "Black Automatic Folding Umbrella",
            "Personal Items",
            "Fibrella",
            "Black",
            "2026-11-17",
            "4:00 PM",
            "Balbago Ground Floor Lobby umbrella rack",
            "Black Fibrella umbrella left behind during heavy afternoon downpour"
        ))
        l6_id = cursor.lastrowid

        # Found Item B
        cursor.execute("""
            INSERT INTO lost_item_tickets (
                logged_by, item_name, category, brand, color,
                date_found, time_found, location_found, description, status, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending_verification', datetime('now', '-1 days'), datetime('now', '-6 hours'))
        """, (
            staff_id,
            "Black Compact Folding Umbrella",
            "Personal Items",
            "Generic",
            "Black",
            "2026-11-17",
            "4:20 PM",
            "Canteen hallway entrance",
            "Standard black folding umbrella with silver push button"
        ))
        l7_id = cursor.lastrowid

        # Matches for Scenario 5 (both pending)
        cursor.execute("""
            INSERT INTO matches (missing_ticket_id, lost_item_id, match_score, status, created_at)
            VALUES (?, ?, 0.92, 'pending', datetime('now', '-6 hours'))
        """, (t7_id, l6_id))

        cursor.execute("""
            INSERT INTO matches (missing_ticket_id, lost_item_id, match_score, status, created_at)
            VALUES (?, ?, 0.75, 'pending', datetime('now', '-6 hours'))
        """, (t7_id, l7_id))

        cursor.execute("""
            INSERT INTO notifications (user_id, message, is_read, created_at) VALUES
            (?, 'We found a possible match for your missing ''Black Folding Umbrella''. Please visit the Lost and Found Office for in-person verification.', 0, datetime('now', '-6 hours')),
            (?, 'Multiple candidate found items match Missing Report #7 (Black Folding Umbrella). In-person inspection required.', 0, datetime('now', '-6 hours'))
        """, (student_id_map["2026-0005"], staff_id))

        conn.commit()
        print("✅ Sample tickets, matches, and notifications successfully seeded!")

    conn.close()
    print(f"Database ready at: {DB_PATH}")


if __name__ == "__main__":
    force = "--reset" in sys.argv
    init_db(force_reseed=force)
