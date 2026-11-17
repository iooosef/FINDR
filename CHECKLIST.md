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

- [ ] `database.py` — SQLite connection helper
- [ ] `models.py` — All 5 table schemas as SQL strings
- [ ] `auth.py` — `/api/auth/register`, `/api/auth/login`, `/api/auth/logout`
- [ ] Session middleware wired into `main.py`
- [ ] Role-based route guards working (student vs staff)
- [ ] `seed.py` auto-called on startup if DB is missing

---

## Stage 3 — Backend: Tickets & Matching

- [ ] `routes/tickets.py` — Missing ticket CRUD (student)
- [ ] `routes/tickets.py` — Lost item ticket CRUD (staff)
- [ ] `utils/matcher.py` — Matching algorithm (category + fuzzy fields)
- [ ] Matching triggered on new Missing Ticket creation
- [ ] Matching triggered on new Lost Item Ticket creation
- [ ] Conflict handling: multiple students → one lost item → `pending_verification`
- [ ] `routes/notifications.py` — Get and mark-as-read

---

## Stage 4 — Frontend: Login Page

- [ ] Clean up prototype `index.html` — remove About links
- [ ] Sign In form wired to `POST /api/auth/login`
- [ ] Sign Up form wired to `POST /api/auth/register`
- [ ] On success: redirect to `/dashboard` (role-based redirect from server)
- [ ] Error messages shown on bad credentials

---

## Stage 5 — Frontend: Student Pages

- [ ] Student dashboard — list of own Missing Tickets + status badges
- [ ] "Lost Something?" form page — all fields, photo upload, validation
- [ ] "Found Something?" — static info page (steps to visit L&F office)
- [ ] Notifications page — list of match alerts (no lost item details shown)

---

## Stage 6 — Frontend: Staff Pages

- [ ] Staff dashboard — summary counts (Lost Items, Missing Tickets, Returned)
- [ ] "Found Something?" form page — Lost Item Ticket form
- [ ] Lost Items table — all tickets, Update only (no Delete)
- [ ] Missing Items table — all student tickets, Update only
- [ ] Returned Items table — claimed items, Update only
- [ ] Staff notifications page

---

## Stage 7 — Polish & Deployment

- [ ] Remove all `#about` links and About references from every file
- [ ] Mobile responsive check on all pages
- [ ] Input validation on all forms (frontend + backend)
- [ ] Photo upload working end-to-end (5 MB limit enforced)
- [ ] Final Render deploy — test full flow: register → report → match → notify
- [ ] Seed script confirmed to auto-run on fresh Render deploy
