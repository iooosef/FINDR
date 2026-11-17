"""
main.py - Entry point for the FINDR FastAPI application.

Responsibilities:
- Initializes FastAPI app and loads .env configuration
- Adds Starlette SessionMiddleware for signed cookie authentication
- Ensures database tables & seed data exist on startup (handles Render restarts)
- Mounts static files and frontend pages
- Registers API route handlers
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

# Import database seed script to auto-initialize on startup
from backend.seed import init_db
from backend.auth import router as auth_router

# ==========================================
# Configuration & Secrets
# ==========================================

# Base paths
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
UPLOADS_DIR = BACKEND_DIR / "uploads"

# Ensure uploads directory exists for photo attachments
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables from backend/.env (or root .env if present)
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(PROJECT_ROOT / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-dev-key-change-in-production-123456789")

# ==========================================
# FastAPI Initialization
# ==========================================

app = FastAPI(
    title="FINDR API",
    description="Fast Item Notification, Detection, and Recovery — Cainta Catholic College",
    version="1.0.0"
)

# Wire in SessionMiddleware
# Cookies are signed with SECRET_KEY so users cannot forge their user_id or role
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    session_cookie="findr_session",
    max_age=7 * 24 * 60 * 60,  # Session lasts 7 days
    same_site="lax",
    https_only=False           # Set to True on production with HTTPS
)


# ==========================================
# Startup Event
# ==========================================

@app.on_event("startup")
def on_startup():
    """
    Runs automatically when the server boots.
    Ensures all 5 SQLite tables exist and default staff account is seeded.
    This guarantees FINDR recovers automatically if Render spins down or redeploys.
    """
    print("🚀 FINDR server starting up...")
    init_db()
    print("✅ Database ready.")


# ==========================================
# Static Files & Frontend Routing
# ==========================================

# Serve uploaded item photos at /uploads/...
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

# Serve frontend static assets (CSS, JS, SVG images)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/", include_in_schema=False)
def serve_index():
    """Serves the login / registration page."""
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/login", include_in_schema=False)
def serve_login():
    """Alias for login page."""
    return RedirectResponse(url="/")


@app.get("/dashboard", include_in_schema=False)
def serve_dashboard(request: Request):
    """
    Serves the dashboard page.
    Redirects to login if user has no active session.
    """
    if "user_id" not in request.session:
        return RedirectResponse(url="/")
    return FileResponse(FRONTEND_DIR / "dashboard" / "dashboard.html")


@app.get("/api/health")
def health_check():
    """Simple health check endpoint for monitoring."""
    return {"status": "ok", "app": "FINDR"}


# ==========================================
# Register API Routers
# ==========================================

app.include_router(auth_router)


# If executed directly with 'python backend/main.py'
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
