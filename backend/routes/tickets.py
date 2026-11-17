"""
tickets.py - Missing and Lost Item ticket routes for FINDR.

Endpoints:
- POST /api/tickets/missing       (Student creates Missing Ticket + runs matcher)
- GET  /api/tickets/missing       (Student gets own tickets; Staff gets all tickets)
- GET  /api/tickets/missing/{id}  (Get specific Missing Ticket)
- PUT  /api/tickets/missing/{id}  (Update Missing Ticket - Staff or owner)
- POST /api/tickets/lost          (Staff creates Found/Lost Item Ticket + runs matcher)
- GET  /api/tickets/lost          (Staff gets all Lost Item Tickets)
- GET  /api/tickets/lost/{id}     (Staff gets specific Lost Item Ticket)
- PUT  /api/tickets/lost/{id}     (Staff updates Lost Item Ticket)
- GET  /api/tickets/returned      (Staff gets all returned/claimed items)
- PUT  /api/tickets/returned/{id} (Staff marks item as claimed/returned)

Note: Delete endpoints are intentionally omitted per system specification.
"""

import os
import uuid
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel

from backend.database import get_db
from backend.auth import get_current_user, require_role
from backend.models import CATEGORIES, MISSING_STATUSES, LOST_ITEM_STATUSES
from backend.utils.matcher import run_matcher_for_missing_ticket, run_matcher_for_lost_item

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

# Maximum allowed file upload size: 5 MB
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"


async def save_uploaded_photo(file: Optional[UploadFile]) -> Optional[str]:
    """
    Validates and saves an uploaded photo file.
    Returns relative path string '/uploads/filename.ext' or None if no file was uploaded.
    """
    if not file or not file.filename:
        return None

    # Check file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{ext}'. Allowed: JPG, PNG, WebP, GIF."
        )

    # Read and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds the 5 MB limit."
        )

    # Generate unique filename to avoid collisions
    unique_name = f"{uuid.uuid4().hex}{ext}"
    destination = UPLOADS_DIR / unique_name
    destination.write_bytes(content)

    return f"/uploads/{unique_name}"


# ==========================================
# 1. Missing Tickets (Student Reports)
# ==========================================

@router.post("/missing", status_code=status.HTTP_201_CREATED)
async def create_missing_ticket(
    request: Request,
    item_name: str = Form(..., description="Name of the missing item"),
    category: str = Form(..., description="Item category"),
    brand: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    date_lost: str = Form(..., description="ISO date when item was lost (e.g. 2026-09-11)"),
    time_lost: Optional[str] = Form(None),
    locations: str = Form(..., description="Possible locations where item was lost"),
    description: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None)
):
    """
    Student reports a missing item ("Lost Something?").
    1. Validates inputs.
    2. Saves missing ticket with status='open'.
    3. Runs matching algorithm against unclaimed found items.
    4. Notifies student if a match is found.
    """
    user = require_role(request, "student")

    # Validate category
    if category not in CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category '{category}'. Valid options: {CATEGORIES}"
        )

    photo_path = await save_uploaded_photo(photo)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO missing_tickets (
                student_id, item_name, category, brand, color,
                date_lost, time_lost, locations, description, photo_path, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open')
            """,
            (
                user["id"], item_name.strip(), category, brand.strip() if brand else None,
                color.strip() if color else None, date_lost.strip(),
                time_lost.strip() if time_lost else None, locations.strip(),
                description.strip() if description else None, photo_path
            )
        )
        new_ticket_id = cursor.lastrowid

        # Run automatic matcher immediately
        matched_lost_ids = run_matcher_for_missing_ticket(conn, new_ticket_id)

    return {
        "message": "Missing ticket created successfully.",
        "ticket_id": new_ticket_id,
        "matches_found": len(matched_lost_ids)
    }


@router.get("/missing")
def list_missing_tickets(request: Request):
    """
    Lists missing tickets:
    - If user is a student: returns only their own missing tickets.
    - If user is staff: returns all missing tickets from all students.
    """
    user = get_current_user(request)

    with get_db() as conn:
        cursor = conn.cursor()
        if user["role"] == "student":
            cursor.execute(
                """
                SELECT m.*, u.full_name as student_name, u.username as student_id_number
                FROM missing_tickets m
                JOIN users u ON m.student_id = u.id
                WHERE m.student_id = ?
                ORDER BY m.id DESC
                """,
                (user["id"],)
            )
        else:
            # Staff sees all tickets
            cursor.execute(
                """
                SELECT m.*, u.full_name as student_name, u.username as student_id_number
                FROM missing_tickets m
                JOIN users u ON m.student_id = u.id
                ORDER BY m.id DESC
                """
            )
        rows = [dict(r) for r in cursor.fetchall()]

    return {"tickets": rows}


@router.get("/missing/{ticket_id}")
def get_missing_ticket(ticket_id: int, request: Request):
    """Gets details of a single missing ticket."""
    user = get_current_user(request)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.*, u.full_name as student_name, u.username as student_id_number
            FROM missing_tickets m
            JOIN users u ON m.student_id = u.id
            WHERE m.id = ?
            """,
            (ticket_id,)
        )
        ticket = cursor.fetchone()

    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

    ticket_dict = dict(ticket)

    # Students can only view their own tickets
    if user["role"] == "student" and ticket_dict["student_id"] != user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return {"ticket": ticket_dict}


class UpdateMissingTicketRequest(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    color: Optional[str] = None
    date_lost: Optional[str] = None
    time_lost: Optional[str] = None
    locations: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


@router.put("/missing/{ticket_id}")
def update_missing_ticket(ticket_id: int, payload: UpdateMissingTicketRequest, request: Request):
    """
    Updates a missing ticket.
    - Owner student can update details.
    - Staff can update details or status ('open', 'matched', 'resolved').
    """
    user = get_current_user(request)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM missing_tickets WHERE id = ?", (ticket_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found.")

        existing_dict = dict(existing)
        if user["role"] == "student" and existing_dict["student_id"] != user["id"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

        # Prepare updated values
        item_name = payload.item_name if payload.item_name is not None else existing_dict["item_name"]
        category = payload.category if payload.category is not None else existing_dict["category"]
        brand = payload.brand if payload.brand is not None else existing_dict["brand"]
        color = payload.color if payload.color is not None else existing_dict["color"]
        date_lost = payload.date_lost if payload.date_lost is not None else existing_dict["date_lost"]
        time_lost = payload.time_lost if payload.time_lost is not None else existing_dict["time_lost"]
        locations = payload.locations if payload.locations is not None else existing_dict["locations"]
        description = payload.description if payload.description is not None else existing_dict["description"]

        # Only staff can change status directly
        new_status = existing_dict["status"]
        if payload.status is not None:
            if user["role"] != "staff":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only staff can change ticket status.")
            if payload.status not in MISSING_STATUSES:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status '{payload.status}'")
            new_status = payload.status

        cursor.execute(
            """
            UPDATE missing_tickets SET
                item_name = ?, category = ?, brand = ?, color = ?,
                date_lost = ?, time_lost = ?, locations = ?, description = ?,
                status = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (item_name, category, brand, color, date_lost, time_lost, locations, description, new_status, ticket_id)
        )

        # Re-run matcher if status is still active
        if new_status in ("open", "matched"):
            run_matcher_for_missing_ticket(conn, ticket_id)

    return {"message": "Missing ticket updated successfully."}


# ==========================================
# 2. Lost Item Tickets (Staff Logs)
# ==========================================

@router.post("/lost", status_code=status.HTTP_201_CREATED)
async def create_lost_item_ticket(
    request: Request,
    item_name: str = Form(..., description="Name of the found item"),
    category: str = Form(..., description="Category"),
    brand: Optional[str] = Form(None),
    color: Optional[str] = Form(None),
    date_found: str = Form(..., description="ISO date when item was found"),
    time_found: Optional[str] = Form(None),
    location_found: str = Form(..., description="Location where item was found"),
    description: Optional[str] = Form(None),
    ticket_status: Optional[str] = Form("unclaimed", alias="status"),
    photo: Optional[UploadFile] = File(None)
):
    """
    Staff logs a found item ("Found Something?").
    1. Validates inputs and role (staff only).
    2. Saves lost item ticket.
    3. Runs matching algorithm against open missing tickets.
    4. Notifies matched student(s) and staff.
    """
    user = require_role(request, "staff")

    if category not in CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category '{category}'."
        )

    if ticket_status not in LOST_ITEM_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status '{ticket_status}'."
        )

    photo_path = await save_uploaded_photo(photo)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO lost_item_tickets (
                logged_by, item_name, category, brand, color,
                date_found, time_found, location_found, description, photo_path, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user["id"], item_name.strip(), category, brand.strip() if brand else None,
                color.strip() if color else None, date_found.strip(),
                time_found.strip() if time_found else None, location_found.strip(),
                description.strip() if description else None, photo_path, ticket_status
            )
        )
        new_item_id = cursor.lastrowid

        # Run automatic matcher immediately
        matched_missing_ids = run_matcher_for_lost_item(conn, new_item_id)

    return {
        "message": "Lost item ticket created successfully.",
        "item_id": new_item_id,
        "matches_found": len(matched_missing_ids)
    }


@router.get("/lost")
def list_lost_item_tickets(request: Request):
    """Staff only: lists all lost item tickets."""
    require_role(request, "staff")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT l.*, u.full_name as logged_by_name
            FROM lost_item_tickets l
            JOIN users u ON l.logged_by = u.id
            ORDER BY l.id DESC
            """
        )
        items = [dict(r) for r in cursor.fetchall()]

    return {"items": items}


@router.get("/lost/{item_id}")
def get_lost_item_ticket(item_id: int, request: Request):
    """Staff only: gets details of a single lost item ticket."""
    require_role(request, "staff")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT l.*, u.full_name as logged_by_name
            FROM lost_item_tickets l
            JOIN users u ON l.logged_by = u.id
            WHERE l.id = ?
            """,
            (item_id,)
        )
        item = cursor.fetchone()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")

    return {"item": dict(item)}


class UpdateLostItemRequest(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    color: Optional[str] = None
    date_found: Optional[str] = None
    time_found: Optional[str] = None
    location_found: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


@router.put("/lost/{item_id}")
def update_lost_item_ticket(item_id: int, payload: UpdateLostItemRequest, request: Request):
    """Staff only: updates a lost item ticket."""
    require_role(request, "staff")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lost_item_tickets WHERE id = ?", (item_id,))
        existing = cursor.fetchone()
        if not existing:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")

        existing_dict = dict(existing)

        item_name = payload.item_name if payload.item_name is not None else existing_dict["item_name"]
        category = payload.category if payload.category is not None else existing_dict["category"]
        brand = payload.brand if payload.brand is not None else existing_dict["brand"]
        color = payload.color if payload.color is not None else existing_dict["color"]
        date_found = payload.date_found if payload.date_found is not None else existing_dict["date_found"]
        time_found = payload.time_found if payload.time_found is not None else existing_dict["time_found"]
        location_found = payload.location_found if payload.location_found is not None else existing_dict["location_found"]
        description = payload.description if payload.description is not None else existing_dict["description"]

        new_status = existing_dict["status"]
        if payload.status is not None:
            if payload.status not in LOST_ITEM_STATUSES:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status '{payload.status}'")
            new_status = payload.status

        cursor.execute(
            """
            UPDATE lost_item_tickets SET
                item_name = ?, category = ?, brand = ?, color = ?,
                date_found = ?, time_found = ?, location_found = ?, description = ?,
                status = ?, updated_at = datetime('now')
            WHERE id = ?
            """,
            (item_name, category, brand, color, date_found, time_found, location_found, description, new_status, item_id)
        )

        # If still unclaimed or pending, run matcher
        if new_status in ("unclaimed", "pending_verification"):
            run_matcher_for_lost_item(conn, item_id)

    return {"message": "Lost item ticket updated successfully."}


# ==========================================
# 3. Returned / Claimed Items (Staff Only)
# ==========================================

@router.get("/returned")
def list_returned_items(request: Request):
    """Staff only: returns all claimed / returned items."""
    require_role(request, "staff")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT l.*, u.full_name as logged_by_name
            FROM lost_item_tickets l
            JOIN users u ON l.logged_by = u.id
            WHERE l.status = 'claimed'
            ORDER BY l.updated_at DESC
            """
        )
        items = [dict(r) for r in cursor.fetchall()]

    return {"items": items}


class ReturnItemRequest(BaseModel):
    missing_ticket_id: Optional[int] = None


@router.put("/returned/{item_id}")
def mark_item_as_returned(item_id: int, payload: ReturnItemRequest, request: Request):
    """
    Staff marks a lost item as claimed/returned.
    If linked to a missing_ticket_id:
    - Sets lost item status -> 'claimed'
    - Sets winning missing ticket status -> 'resolved'
    - Sets winning match status -> 'verified'
    - Sets all other competing matches for this lost item -> 'rejected'
    """
    require_role(request, "staff")

    with get_db() as conn:
        cursor = conn.cursor()

        # Check lost item exists
        cursor.execute("SELECT * FROM lost_item_tickets WHERE id = ?", (item_id,))
        item = cursor.fetchone()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found.")

        # Mark lost item as claimed
        cursor.execute(
            "UPDATE lost_item_tickets SET status = 'claimed', updated_at = datetime('now') WHERE id = ?",
            (item_id,)
        )

        if payload.missing_ticket_id:
            # Mark winning missing ticket as resolved
            cursor.execute(
                "UPDATE missing_tickets SET status = 'resolved', updated_at = datetime('now') WHERE id = ?",
                (payload.missing_ticket_id,)
            )

            # Mark winning match as verified
            cursor.execute(
                "UPDATE matches SET status = 'verified' WHERE lost_item_id = ? AND missing_ticket_id = ?",
                (item_id, payload.missing_ticket_id)
            )

            # Find competing missing tickets
            cursor.execute(
                "SELECT missing_ticket_id FROM matches WHERE lost_item_id = ? AND missing_ticket_id != ?",
                (item_id, payload.missing_ticket_id)
            )
            competing_ids = [row["missing_ticket_id"] for row in cursor.fetchall()]

            # Mark other matches for this lost item as rejected
            cursor.execute(
                "UPDATE matches SET status = 'rejected' WHERE lost_item_id = ? AND missing_ticket_id != ?",
                (item_id, payload.missing_ticket_id)
            )

            # Revert competing missing tickets to 'open' if no other pending matches
            for comp_id in competing_ids:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM matches WHERE missing_ticket_id = ? AND status = 'pending'",
                    (comp_id,)
                )
                if cursor.fetchone()["count"] == 0:
                    cursor.execute(
                        "UPDATE missing_tickets SET status = 'open', updated_at = datetime('now') WHERE id = ? AND status = 'matched'",
                        (comp_id,)
                    )

            # Notify the winning student
            cursor.execute("SELECT student_id, item_name FROM missing_tickets WHERE id = ?", (payload.missing_ticket_id,))
            st = cursor.fetchone()
            if st:
                cursor.execute(
                    "INSERT INTO notifications (user_id, message, is_read) VALUES (?, ?, 0)",
                    (st["student_id"], f"Your missing item '{st['item_name']}' has been marked as claimed and resolved. Thank you!")
                )

    return {"message": "Item marked as returned/claimed successfully."}
