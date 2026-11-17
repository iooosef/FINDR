"""
matches.py - Match query and resolution routes for FINDR.

Endpoints:
- GET /api/matches             (Student gets redacted own matches; Staff gets full match details)
- PUT /api/matches/{id}/verify (Staff verifies in-person ownership: marks match verified, lost item claimed, missing ticket resolved)
- PUT /api/matches/{id}/reject (Staff rejects invalid match)

Important Privacy Rule:
Students are NEVER shown the specific details (description, photo, location found) of the found item.
Verification must occur in-person at the Lost and Found office.
"""

from fastapi import APIRouter, Request, HTTPException, status
from backend.database import get_db
from backend.auth import get_current_user, require_role

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("")
def list_matches(request: Request):
    """
    Lists matches.
    - Students: only see matches linked to their own missing tickets, with lost item details redacted.
    - Staff: see full match records with comparison details.
    """
    user = get_current_user(request)

    with get_db() as conn:
        cursor = conn.cursor()

        if user["role"] == "student":
            # Redacted view for students (protects found item details)
            cursor.execute(
                """
                SELECT 
                    m.id as match_id,
                    m.missing_ticket_id,
                    m.status as match_status,
                    m.created_at as match_date,
                    mt.item_name as missing_item_name,
                    mt.category as missing_category,
                    mt.status as missing_status
                FROM matches m
                JOIN missing_tickets mt ON m.missing_ticket_id = mt.id
                WHERE mt.student_id = ?
                ORDER BY m.id DESC
                """,
                (user["id"],)
            )
            matches = [dict(r) for r in cursor.fetchall()]

        else:
            # Full view for staff
            cursor.execute(
                """
                SELECT 
                    m.id as match_id,
                    m.missing_ticket_id,
                    m.lost_item_id,
                    m.match_score,
                    m.status as match_status,
                    m.created_at as match_date,
                    -- Missing ticket info
                    mt.item_name as missing_item_name,
                    mt.category as missing_category,
                    mt.brand as missing_brand,
                    mt.color as missing_color,
                    mt.date_lost,
                    mt.locations as missing_locations,
                    mt.status as missing_ticket_status,
                    u.full_name as student_name,
                    u.username as student_id_number,
                    -- Lost item info
                    lt.item_name as lost_item_name,
                    lt.category as lost_category,
                    lt.brand as lost_brand,
                    lt.color as lost_color,
                    lt.date_found,
                    lt.location_found,
                    lt.status as lost_item_status
                FROM matches m
                JOIN missing_tickets mt ON m.missing_ticket_id = mt.id
                JOIN users u ON mt.student_id = u.id
                JOIN lost_item_tickets lt ON m.lost_item_id = lt.id
                ORDER BY m.id DESC
                """
            )
            matches = [dict(r) for r in cursor.fetchall()]

    return {"matches": matches}


@router.put("/{match_id}/verify")
def verify_match(match_id: int, request: Request):
    """
    Staff only: Confirms that a missing ticket correctly matches a lost item after in-person verification.
    Actions:
    - Match status -> 'verified'
    - Lost item ticket -> 'claimed'
    - Winning missing ticket -> 'resolved'
    - Competing matches for the same lost item -> 'rejected'
    - Student notified of successful retrieval
    """
    require_role(request, "staff")

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
        match_row = cursor.fetchone()
        if not match_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found.")

        missing_id = match_row["missing_ticket_id"]
        lost_id = match_row["lost_item_id"]

        # 1. Update this match to verified
        cursor.execute(
            "UPDATE matches SET status = 'verified' WHERE id = ?",
            (match_id,)
        )

        # 2. Find other competing matches for the same lost item
        cursor.execute(
            "SELECT missing_ticket_id FROM matches WHERE lost_item_id = ? AND id != ?",
            (lost_id, match_id)
        )
        competing_missing_ids = [row["missing_ticket_id"] for row in cursor.fetchall()]

        # Reject those competing matches
        cursor.execute(
            "UPDATE matches SET status = 'rejected' WHERE lost_item_id = ? AND id != ?",
            (lost_id, match_id)
        )

        # Revert competing missing tickets back to 'open' if they have no other pending matches
        for comp_id in competing_missing_ids:
            cursor.execute(
                "SELECT COUNT(*) as count FROM matches WHERE missing_ticket_id = ? AND status = 'pending'",
                (comp_id,)
            )
            if cursor.fetchone()["count"] == 0:
                cursor.execute(
                    "UPDATE missing_tickets SET status = 'open', updated_at = datetime('now') WHERE id = ? AND status = 'matched'",
                    (comp_id,)
                )

        # 3. Mark lost item as claimed
        cursor.execute(
            "UPDATE lost_item_tickets SET status = 'claimed', updated_at = datetime('now') WHERE id = ?",
            (lost_id,)
        )

        # 4. Mark winning missing ticket as resolved
        cursor.execute(
            "UPDATE missing_tickets SET status = 'resolved', updated_at = datetime('now') WHERE id = ?",
            (missing_id,)
        )

        # 5. Notify winning student
        cursor.execute("SELECT student_id, item_name FROM missing_tickets WHERE id = ?", (missing_id,))
        student = cursor.fetchone()
        if student:
            cursor.execute(
                "INSERT INTO notifications (user_id, message, is_read) VALUES (?, ?, 0)",
                (
                    student["student_id"],
                    f"Ownership verified! Your missing item '{student['item_name']}' has been officially claimed."
                )
            )

    return {"message": "Match verified and item marked as claimed successfully."}


@router.put("/{match_id}/reject")
def reject_match(match_id: int, request: Request):
    """
    Staff only: Rejects a match (item did not match student's report during verification).
    Actions:
    - Match status -> 'rejected'
    - Re-evaluates ticket statuses
    """
    require_role(request, "staff")

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
        match_row = cursor.fetchone()
        if not match_row:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found.")

        missing_id = match_row["missing_ticket_id"]
        lost_id = match_row["lost_item_id"]

        # 1. Update match to rejected
        cursor.execute("UPDATE matches SET status = 'rejected' WHERE id = ?", (match_id,))

        # 2. Check if missing ticket has any other pending matches
        cursor.execute(
            "SELECT COUNT(*) as count FROM matches WHERE missing_ticket_id = ? AND status = 'pending'",
            (missing_id,)
        )
        if cursor.fetchone()["count"] == 0:
            cursor.execute(
                "UPDATE missing_tickets SET status = 'open', updated_at = datetime('now') WHERE id = ? AND status = 'matched'",
                (missing_id,)
            )

        # 3. Check if lost item still has 2 or more pending matches
        cursor.execute(
            "SELECT COUNT(DISTINCT missing_ticket_id) as count FROM matches WHERE lost_item_id = ? AND status = 'pending'",
            (lost_id,)
        )
        remaining = cursor.fetchone()["count"]
        if remaining < 2:
            cursor.execute(
                "UPDATE lost_item_tickets SET status = 'unclaimed', updated_at = datetime('now') WHERE id = ? AND status = 'pending_verification'",
                (lost_id,)
            )

    return {"message": "Match rejected successfully."}
