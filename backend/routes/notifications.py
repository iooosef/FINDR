"""
notifications.py - Notification routes for FINDR.

Endpoints:
- GET /api/notifications          (Gets user's notifications + unread count)
- PUT /api/notifications/{id}/read (Marks a specific notification as read)
- PUT /api/notifications/read-all  (Marks all notifications for current user as read)
"""

from fastapi import APIRouter, Request, HTTPException, status
from backend.database import get_db
from backend.auth import get_current_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications(request: Request):
    """
    Returns all notifications for the currently logged-in user.
    Ordered newest first, with unread count.
    """
    user = get_current_user(request)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, message, is_read, created_at
            FROM notifications
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user["id"],)
        )
        notifications = [dict(r) for r in cursor.fetchall()]

        # Count unread
        cursor.execute(
            "SELECT COUNT(*) as unread_count FROM notifications WHERE user_id = ? AND is_read = 0",
            (user["id"],)
        )
        unread = cursor.fetchone()["unread_count"]

    return {
        "unread_count": unread,
        "notifications": notifications
    }


@router.put("/{notification_id}/read")
def mark_notification_as_read(notification_id: int, request: Request):
    """Marks a single notification as read."""
    user = get_current_user(request)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM notifications WHERE id = ? AND user_id = ?",
            (notification_id, user["id"])
        )
        notif = cursor.fetchone()
        if not notif:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")

        cursor.execute(
            "UPDATE notifications SET is_read = 1 WHERE id = ?",
            (notification_id,)
        )

    return {"message": "Notification marked as read."}


@router.put("/read-all")
def mark_all_notifications_as_read(request: Request):
    """Marks all notifications for the current user as read."""
    user = get_current_user(request)

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE notifications SET is_read = 1 WHERE user_id = ?",
            (user["id"],)
        )

    return {"message": "All notifications marked as read."}
