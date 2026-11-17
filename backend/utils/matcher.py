"""
matcher.py - Automatic matching algorithm for FINDR.

How Matching Works:
1. Category must match exactly (e.g. 'Electronics' == 'Electronics').
2. In addition, at least ONE of the following must match:
   - Color match (e.g., 'black' in both)
   - Brand match (e.g., 'casio' in both)
   - Keyword overlap in item_name or description
3. Status check:
   - Only match against lost items that are 'unclaimed' or 'pending_verification'.
   - Only match against missing tickets that are 'open' or 'matched'.
4. Notification Privacy:
   - Students are NOT shown any details of the lost item.
   - The notification directs them to visit the Lost and Found Office for in-person verification.
5. Conflicting Matches:
   - If two or more students match one lost item, that lost item's status changes to 'pending_verification'.
"""

import re
import sqlite3
from typing import Tuple, Dict, Any, List

# Stop words to ignore during keyword matching
STOP_WORDS = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for",
    "of", "with", "is", "was", "my", "lost", "found", "near", "around"
}


def extract_keywords(text: str) -> set:
    """Extracts cleaned lowercase words from text, ignoring short words and stop words."""
    if not text:
        return set()
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {w for w in words if len(w) > 2 and w not in STOP_WORDS}


def calculate_match(missing: Dict[str, Any], lost: Dict[str, Any]) -> Tuple[bool, float]:
    """
    Compares a missing ticket to a lost item ticket.
    Returns (is_match: bool, score: float).
    Score ranges from 0.0 to 1.0.
    """
    # 1. Category MUST match
    missing_cat = (missing.get("category") or "").strip().lower()
    lost_cat = (lost.get("category") or "").strip().lower()

    if not missing_cat or missing_cat != lost_cat:
        return False, 0.0

    score = 0.4  # Base score for category match
    matched_criteria = 0

    # 2. Check Color
    missing_color = (missing.get("color") or "").strip().lower()
    lost_color = (lost.get("color") or "").strip().lower()
    if missing_color and lost_color:
        if missing_color in lost_color or lost_color in missing_color:
            score += 0.2
            matched_criteria += 1

    # 3. Check Brand
    missing_brand = (missing.get("brand") or "").strip().lower()
    lost_brand = (lost.get("brand") or "").strip().lower()
    if missing_brand and lost_brand:
        if missing_brand in lost_brand or lost_brand in missing_brand:
            score += 0.2
            matched_criteria += 1

    # 4. Check Keyword overlap in item_name and description
    missing_text = f"{missing.get('item_name', '')} {missing.get('description', '')}"
    lost_text = f"{lost.get('item_name', '')} {lost.get('description', '')}"

    missing_keywords = extract_keywords(missing_text)
    lost_keywords = extract_keywords(lost_text)

    overlap = missing_keywords.intersection(lost_keywords)
    if overlap:
        score += min(0.2, len(overlap) * 0.1)
        matched_criteria += 1

    # Must have matched category PLUS at least one other criterion (color, brand, or keywords)
    is_match = matched_criteria >= 1
    final_score = round(min(1.0, score), 2) if is_match else 0.0

    return is_match, final_score


def create_notification(conn: sqlite3.Connection, user_id: int, message: str):
    """Inserts a notification record for the specified user."""
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notifications (user_id, message, is_read) VALUES (?, ?, 0)",
        (user_id, message)
    )


def run_matcher_for_missing_ticket(conn: sqlite3.Connection, missing_ticket_id: int) -> List[int]:
    """
    Called when a student creates or updates a missing ticket.
    Finds potential matches among active lost items and records matches & notifications.
    Returns list of matched lost_item IDs.
    """
    cursor = conn.cursor()

    # Load missing ticket
    cursor.execute("SELECT * FROM missing_tickets WHERE id = ?", (missing_ticket_id,))
    missing = cursor.fetchone()
    if not missing or missing["status"] == "resolved":
        return []

    missing_dict = dict(missing)

    # Find available lost items (unclaimed or pending_verification) in the same category
    cursor.execute(
        """
        SELECT * FROM lost_item_tickets
        WHERE category = ? AND status IN ('unclaimed', 'pending_verification')
        """,
        (missing_dict["category"],)
    )
    lost_candidates = cursor.fetchall()

    newly_matched_lost_ids = []

    for lost in lost_candidates:
        lost_dict = dict(lost)
        is_match, score = calculate_match(missing_dict, lost_dict)

        if is_match:
            # Check if match already recorded
            cursor.execute(
                "SELECT id FROM matches WHERE missing_ticket_id = ? AND lost_item_id = ?",
                (missing_ticket_id, lost_dict["id"])
            )
            existing_match = cursor.fetchone()

            if not existing_match:
                # 1. Insert match
                cursor.execute(
                    "INSERT INTO matches (missing_ticket_id, lost_item_id, match_score, status) VALUES (?, ?, ?, 'pending')",
                    (missing_ticket_id, lost_dict["id"], score)
                )

                # 2. Update missing ticket status to 'matched'
                cursor.execute(
                    "UPDATE missing_tickets SET status = 'matched', updated_at = datetime('now') WHERE id = ?",
                    (missing_ticket_id,)
                )

                # 3. Notify student (WITHOUT revealing sensitive lost item details)
                student_msg = (
                    f"We found a possible match for your missing '{missing_dict['item_name']}'. "
                    f"Please visit the Lost and Found Office for in-person verification."
                )
                create_notification(conn, missing_dict["student_id"], student_msg)

                # 4. Check if multiple students matched this same lost item (conflict handling)
                cursor.execute(
                    "SELECT COUNT(DISTINCT missing_ticket_id) as student_matches FROM matches WHERE lost_item_id = ?",
                    (lost_dict["id"],)
                )
                match_count = cursor.fetchone()["student_matches"]

                if match_count >= 2:
                    # Update status to pending_verification
                    cursor.execute(
                        "UPDATE lost_item_tickets SET status = 'pending_verification', updated_at = datetime('now') WHERE id = ?",
                        (lost_dict["id"],)
                    )

                # 5. Notify staff who logged the found item
                staff_msg = (
                    f"Possible match found: Missing Ticket #{missing_ticket_id} ('{missing_dict['item_name']}') "
                    f"matches Lost Item #{lost_dict['id']} ('{lost_dict['item_name']}')."
                )
                create_notification(conn, lost_dict["logged_by"], staff_msg)

                newly_matched_lost_ids.append(lost_dict["id"])

    return newly_matched_lost_ids


def run_matcher_for_lost_item(conn: sqlite3.Connection, lost_item_id: int) -> List[int]:
    """
    Called when staff creates or updates a lost item ticket.
    Finds potential matches among open missing tickets and records matches & notifications.
    Returns list of matched missing_ticket IDs.
    """
    cursor = conn.cursor()

    # Load lost item ticket
    cursor.execute("SELECT * FROM lost_item_tickets WHERE id = ?", (lost_item_id,))
    lost = cursor.fetchone()
    if not lost or lost["status"] == "claimed":
        return []

    lost_dict = dict(lost)

    # Find open or matched missing tickets in the same category
    cursor.execute(
        """
        SELECT * FROM missing_tickets
        WHERE category = ? AND status IN ('open', 'matched')
        """,
        (lost_dict["category"],)
    )
    missing_candidates = cursor.fetchall()

    newly_matched_missing_ids = []

    for missing in missing_candidates:
        missing_dict = dict(missing)
        is_match, score = calculate_match(missing_dict, lost_dict)

        if is_match:
            # Check if match already recorded
            cursor.execute(
                "SELECT id FROM matches WHERE missing_ticket_id = ? AND lost_item_id = ?",
                (missing_dict["id"], lost_item_id)
            )
            existing_match = cursor.fetchone()

            if not existing_match:
                # 1. Insert match record
                cursor.execute(
                    "INSERT INTO matches (missing_ticket_id, lost_item_id, match_score, status) VALUES (?, ?, ?, 'pending')",
                    (missing_dict["id"], lost_item_id, score)
                )

                # 2. Update missing ticket status to 'matched'
                cursor.execute(
                    "UPDATE missing_tickets SET status = 'matched', updated_at = datetime('now') WHERE id = ?",
                    (missing_dict["id"],)
                )

                # 3. Notify student (WITHOUT revealing sensitive lost item details)
                student_msg = (
                    f"We found a possible match for your missing '{missing_dict['item_name']}'. "
                    f"Please visit the Lost and Found Office for in-person verification."
                )
                create_notification(conn, missing_dict["student_id"], student_msg)

                # 4. Notify staff
                staff_msg = (
                    f"Possible match found: Missing Ticket #{missing_dict['id']} ('{missing_dict['item_name']}') "
                    f"matches Lost Item #{lost_item_id} ('{lost_dict['item_name']}')."
                )
                create_notification(conn, lost_dict["logged_by"], staff_msg)

                newly_matched_missing_ids.append(missing_dict["id"])

    # If 2 or more missing tickets match this lost item, mark status as pending_verification
    if len(newly_matched_missing_ids) >= 2 or lost_dict["status"] == "unclaimed":
        cursor.execute(
            "SELECT COUNT(DISTINCT missing_ticket_id) as total_matches FROM matches WHERE lost_item_id = ?",
            (lost_item_id,)
        )
        total_matches = cursor.fetchone()["total_matches"]
        if total_matches >= 2:
            cursor.execute(
                "UPDATE lost_item_tickets SET status = 'pending_verification', updated_at = datetime('now') WHERE id = ?",
                (lost_item_id,)
            )

    return newly_matched_missing_ids
