# FINDR — Project Checklist

> Track development progress here. Check off items as they are completed.
> Last updated: 2026-11-17

---

## Stage 1 — Project Setup & Configuration

### 1.1 Folder Structure
- [x] Create `backend/` with subdirectories (`routes/`, `utils/`)
- [x] Create `frontend/` with subdirectories (`dashboard/`, `assets/`)
- [x] Create all empty backend Python files (`main.py`, `database.py`, `models.py`, `auth.py`, route files, `matcher.py`)
- [x] Move existing prototype files into the correct `frontend/` folders
- [x] Remove old `LOGIN PAGE/` and `Inside FINDR/` folders

### 1.2 Python Environment
- [x] Create virtual environment (`python -m venv venv`)
- [x] Activate virtual environment
- [x] Create `requirements.txt` with all packages
- [x] Run `pip install -r requirements.txt`

### 1.3 Secrets & Config
- [x] Generate a `SECRET_KEY` (`python -c "import secrets; print(secrets.token_hex(32))"`)
- [x] Create `backend/.env` and paste the key
- [x] Confirm `.env` is in `.gitignore` and will never be committed

### 1.4 Project Config Files
- [x] Create `.gitignore`
- [x] Create `render.yaml` (or `Procfile`) for Render deployment

### 1.5 Database Initialization
- [x] Create `backend/seed.py` with all 5 table definitions
- [x] Add staff account seeding logic to `seed.py`
- [x] Run `python backend/seed.py` — confirm `backend/findr.db` is created
- [x] Confirm staff login works via a quick test

### 1.6 Git & Hosting
- [x] Run `git init`
- [x] Add all files and make initial commit
- [ ] Push to GitHub
- [ ] Create Render Web Service, connect to GitHub repo
- [ ] Set `SECRET_KEY` environment variable in Render dashboard
- [ ] Confirm Render deploy succeeds (even if the app is empty at this point)

---

## Stage 2 — Backend: Auth & Core API

- [x] `database.py` — SQLite connection helper
- [x] `models.py` — All 5 table schemas as SQL strings
- [x] `auth.py` — `/api/auth/register`, `/api/auth/login`, `/api/auth/logout`
- [x] Session middleware wired into `main.py`
- [x] Role-based route guards working (student vs staff)
- [x] `seed.py` auto-called on startup if DB is missing

---

## Stage 3 — Backend: Tickets & Matching

- [x] `routes/tickets.py` — Missing ticket CRUD (student)
- [x] `routes/tickets.py` — Lost item ticket CRUD (staff)
- [x] `utils/matcher.py` — Matching algorithm (category + fuzzy fields)
- [x] Matching triggered on new Missing Ticket creation
- [x] Matching triggered on new Lost Item Ticket creation
- [x] Conflict handling: multiple students → one lost item → `pending_verification`
- [x] `routes/notifications.py` — Get and mark-as-read

---

## Stage 4 — Frontend: Login Page

- [x] Clean up prototype `index.html` — remove About links
- [x] Sign In form wired to `POST /api/auth/login`
- [x] Sign Up form wired to `POST /api/auth/register`
- [x] On success: redirect to `/dashboard` (role-based redirect from server)
- [x] Error messages shown on bad credentials

---

## Stage 5 — Frontend: Student Pages

- [x] Student dashboard — list of own Missing Tickets + status badges
- [x] "Lost Something?" form page — all fields, photo upload, validation
- [x] "Found Something?" — static info page (steps to visit L&F office)
- [x] Notifications page — list of match alerts (no lost item details shown)

---

## Stage 6 — Frontend: Staff Pages

- [x] Staff dashboard — summary counts (Lost Items, Missing Tickets, Returned)
- [x] "Found Something?" form page — Lost Item Ticket form
- [x] Lost Items table — all tickets, Update only (no Delete)
- [x] Missing Items table — all student tickets, Update only
- [x] Returned Items table — claimed items, Update only
- [x] Staff notifications page

---

## Stage 7 — Polish & Deployment

- [x] Remove all `#about` links and About references from every file
- [x] Mobile responsive check on all pages
- [x] Input validation on all forms (frontend + backend)
- [x] Photo upload working end-to-end (5 MB limit enforced)
- [x] Final Render deploy — test full flow: register → report → match → notify
- [x] Seed script confirmed to auto-run on fresh Render deploy
