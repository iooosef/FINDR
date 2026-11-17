"""
auth.py - Authentication routes and session utilities for FINDR.

Handles:
- Password hashing and verification via bcrypt
- Student account registration (Student ID + Name + Password)
- Sign-in for both Students and Staff
- Session cookie management (Starlette SessionMiddleware)
- Role verification helpers (student vs. staff)
"""

from typing import Dict, Any, Optional
import bcrypt
from fastapi import APIRouter, Request, HTTPException, status
from pydantic import BaseModel, Field

from backend.database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ==========================================
# Password Hashing Functions (bcrypt)
# ==========================================

def hash_password(plain_password: str) -> str:
    """Hashes a plaintext password using bcrypt and returns a UTF-8 string."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Compares a plaintext password against a stored bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# ==========================================
# Pydantic Request Models (Input Validation)
# ==========================================

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Student's full name")
    id_number: str = Field(..., min_length=3, description="Student ID number")
    password: str = Field(..., min_length=4, description="Account password")


class LoginRequest(BaseModel):
    id_number: str = Field(..., description="Student ID or staff username")
    password: str = Field(..., description="Account password")


# ==========================================
# Session & Role Helpers
# ==========================================

def get_current_user(request: Request) -> Dict[str, Any]:
    """
    Reads the signed session cookie from the incoming request.
    If valid, returns the user record from the database.
    If missing or invalid, raises HTTP 401 Unauthorized.
    """
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not logged in. Please sign in first."
        )

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, full_name, role, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        user = cursor.fetchone()

    if not user:
        # Session references a user ID that no longer exists in DB
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found. Please log in again."
        )

    return dict(user)


def require_role(request: Request, allowed_role: str) -> Dict[str, Any]:
    """
    Verifies that the current user has the specified role ('student' or 'staff').
    Raises HTTP 403 Forbidden if the user's role does not match.
    """
    user = get_current_user(request)
    if user["role"] != allowed_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Requires '{allowed_role}' role."
        )
    return user


# ==========================================
# API Endpoints
# ==========================================

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_student(payload: RegisterRequest, request: Request):
    """
    Student registration endpoint.
    - Validates name, ID number, and password.
    - Checks for duplicate Student ID.
    - Hashes password and stores new user with role='student'.
    - Automatically logs in the student by setting session cookie.
    """
    student_id = payload.id_number.strip()
    full_name = payload.name.strip()
    plain_pw = payload.password

    with get_db() as conn:
        cursor = conn.cursor()

        # Check if ID number already exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (student_id,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this Student ID is already registered."
            )

        # Hash password and insert student
        hashed = hash_password(plain_pw)
        cursor.execute(
            "INSERT INTO users (username, full_name, role, password_hash) VALUES (?, ?, 'student', ?)",
            (student_id, full_name, hashed)
        )
        new_user_id = cursor.lastrowid

    # Store user identity in the signed session cookie
    request.session["user_id"] = new_user_id
    request.session["role"] = "student"

    return {
        "message": "Account created successfully.",
        "user": {
            "id": new_user_id,
            "username": student_id,
            "full_name": full_name,
            "role": "student"
        }
    }


@router.post("/login")
def login(payload: LoginRequest, request: Request):
    """
    Login endpoint for both Students and Staff.
    - Finds user by username (Student ID or staff username).
    - Verifies password hash.
    - Sets user_id and role inside request.session.
    """
    username = payload.id_number.strip()
    plain_pw = payload.password

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, full_name, role, password_hash FROM users WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()

    # Reject if user doesn't exist or password doesn't match
    if not user or not verify_password(plain_pw, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ID Number / Username or password."
        )

    # Save credentials into signed session cookie
    request.session["user_id"] = user["id"]
    request.session["role"] = user["role"]

    return {
        "message": "Login successful.",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
    }


@router.post("/logout")
def logout(request: Request):
    """Clears the session cookie, logging the user out."""
    request.session.clear()
    return {"message": "Logged out successfully."}


@router.get("/me")
def get_profile(request: Request):
    """Returns the profile of the currently logged-in user."""
    user = get_current_user(request)
    return {"user": user}
