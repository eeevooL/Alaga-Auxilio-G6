# Alaga — Elderly Care Coordination System

A full-stack Django and PostgreSQL (Supabase) web application designed to help local caregivers and remote family members coordinate medication logs, daily wellness check-ins, appointments, and emergency SOS alerts.

## Tech Stack
- **Backend & Templates:** Django
- **Database:** PostgreSQL (Supabase)

## Increment 1: Account Feature
- **Account Registration:** Role-locked registration (Remote Family Member or Local Caregiver) with email uniqueness validation and password hashing.
- **Authentication:** Email/password login, session logout, and @login_required route protection.
- **Role-Based Dashboards:** Dedicated dashboards and URL access guards for Local Caregiver and Remote Family Member roles.
- **User Profile:** Authenticated profile view and update page.

## How to Run It on Your Computer

### What you need first
- Python 3.10 or newer
- Git

---

### Step 1: Clone the repo
Open Terminal (Mac) or PowerShell (Windows) and type:
```bash
git clone https://github.com/eeevooL/Alaga-Auxilio-G6.git
cd Alaga-Auxilio-G6
```

---

### Step 2: Make a virtual environment and install the packages

**Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```powershell
python -m venv venv
venv\Scripts\Activate
pip install -r requirements.txt
```

---

### Step 3: Set up the database (Supabase / PostgreSQL)

Make a file named `.env` in the main project folder (`Alaga-Auxilio-G6/.env`) and paste this:

```env
DB_NAME=postgres
DB_USER=postgres.your-project-ref
DB_PASSWORD=your_actual_database_password
DB_HOST=aws-0-region.pooler.supabase.com
DB_PORT=5432
```

You can find these details in Supabase under **Project Settings → Database**.

> Note: Make sure `alaga_project/settings.py` has `'sslmode': 'require'` in the database options so the connection works.

---

### Step 4: Run the migrations and start the server

**Mac:**
```bash
python3 manage.py migrate
python3 manage.py runserver 8080
```

**Windows:**
```powershell
python manage.py migrate
python manage.py runserver 8080
```

Then open **http://127.0.0.1:8080** in your browser.

---

## Features Done (Phase 1)
- **Register and choose a role:** Users can sign up as either a *Remote Family Member* or a *Local Caregiver*.
- **Login:** Log in with email and password. Passwords are hashed and sessions are handled.
- **Dashboards per role:** Each role has its own dashboard. The `@role_required` decorator blocks users from opening the other role's pages through the URL.
