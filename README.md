# FINDR — Fast Item Notification, Detection, and Recovery

> Official Lost and Found web system for **Cainta Catholic College (CCC)**.

---

## 🔑 Default Seed Credentials

Use these pre-seeded accounts to test student and staff workflows:

| Role | Username / Student ID | Full Name | Password | Access Level |
|---|---|---|---|---|
| **Staff Admin** | `admin` | FINDR Administrator | `adminpassword123` | Management Hub, Found Intake Form, 4 Management Tables, Verification Controls |
| **Student 1** | `2026-0001` | Juan Dela Cruz | `studentpassword123` | Student Dashboard, "Lost Something?" Report Form, Match Notifications |
| **Student 2** | `2026-0002` | Maria Clara Santos | `studentpassword123` | Student Dashboard, "Lost Something?" Report Form, Match Notifications |
| **Student 3** | `2026-0003` | Mark Joseph Bautista | `studentpassword123` | Student Dashboard, "Lost Something?" Report Form, Match Notifications |
| **Student 4** | `2026-0004` | Angelo Reyes | `studentpassword123` | Student Dashboard, "Lost Something?" Report Form, Match Notifications |
| **Student 5** | `2026-0005` | Alyssa Mae Rivera | `studentpassword123` | Student Dashboard, "Lost Something?" Report Form, Match Notifications |

> **Note:** Students can also self-register a new account anytime on the login page using their own Student ID number.

### 📋 Pre-Seeded Demonstration Scenarios

| Scenario | Missing Item (Student) | Found Item (Staff) | Status / Workflow State |
|---|---|---|---|
| **1. Received & Claimed** | Casio Calculator (Juan `2026-0001`) | Casio Calculator (Staff) | Missing: `resolved`, Found: `claimed`, Match: `verified`. Appears in Returned Ledger. |
| **2. Not Received (Open)** | AquaFlask Tumbler (Maria `2026-0002`) | — | Missing: `open` (no match turned in yet). |
| **2. Not Received (Unclaimed)** | — | Fossil Watch & PE Jacket (Staff) | Found: `unclaimed` (no student reports matching). |
| **3. Matched & Pending** | Leather ID Holder (Mark `2026-0003`) | Brown ID Holder (Staff) | Missing: `matched`, Found: `unclaimed`, Match: `pending`. Unread notification sent to Mark. |
| **4. Conflict: 1 Lost, 2 Missing** | AirPods Case (Juan `2026-0001`) & AirPods 2 (Angelo `2026-0004`) | AirPods Pro 2nd Gen Case (Staff) | Found: `pending_verification`, both Missing: `matched`. Both students notified for office verification. |
| **5. Conflict: 1 Missing, 2 Lost** | Fibrella Umbrella (Alyssa `2026-0005`) | Fibrella Umbrella + Generic Umbrella (Staff) | Missing: `matched`, both Found: `pending_verification`. Multiple candidate matches. |

---

## 🛠️ Tech Stack

- **Frontend**: HTML5, Vanilla CSS3, JavaScript (ES6+), Font Awesome 6, Montserrat (Google Fonts)
- **Backend**: Python 3.9+ using FastAPI & Uvicorn
- **Database**: SQLite (persisted locally, automatically initialized on server boot)
- **Authentication**: Starlette signed `SessionMiddleware` (cookie-based) with `bcrypt` password hashing
- **Deployment**: Render Free Tier

---

## 🚀 Local Development Setup

### 1. Prerequisites
- Python 3.9 or higher
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/iooosef/FINDR.git
cd FINDR
```

### 3. Create & Activate Virtual Environment
```powershell
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Environment Secrets (`backend/.env`)
Create a `.env` file inside the `backend/` directory with a secure secret key:
```env
SECRET_KEY=your_generated_secret_key_here
```
*(You can generate one using `python -c "import secrets; print(secrets.token_hex(32))"`)*

### 6. Initialize Database & Seed Accounts
```bash
python backend/seed.py
```

### 7. Run the Application
```bash
uvicorn backend.main:app --reload
```
Open your browser and navigate to **`http://127.0.0.1:8000`**.

---

## 🌐 Deploying to Render Free Tier

1. Push your repository to GitHub.
2. Go to [dashboard.render.com](https://dashboard.render.com) and create a **New Web Service**.
3. Select your repository: `iooosef/FINDR`.
4. Configure service settings:
   - **Root Directory**: *(Leave blank)*
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Under **Environment Variables**, add:
   - `SECRET_KEY` = *(Your 64-character secret key)*
6. Click **Create Web Service**.
