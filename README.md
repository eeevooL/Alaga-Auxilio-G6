# Alaga — Elderly Care Coordination System

A full-stack Django and PostgreSQL (Supabase) web application designed to help local caregivers and remote family members coordinate medication logs, daily wellness check-ins, appointments, and emergency SOS alerts.

## Tech Stack
- **Backend & Templates:** Django
- **Database:** PostgreSQL (Supabase)
- **Timezone:** Asia/Manila (Philippine Standard Time)

---

## Increment 2: Core Feature (Vertical Slice) — Medication Management & Adherence Tracking

The core feature provides end-to-end management and verification of daily medication routines between remote family members and local caregivers:

1. **Care Profile & Care Circle:**
   - Detailed profile of the elderly relative (blood type, medical conditions, allergies, insurance, and emergency medical notes).
   - Multi-user Care Circle linking both Remote Family and Local Caregiver accounts to a shared patient.
2. **Medication & Schedule Management (CRUD):**
   - Full CRUD operations for medicines linked to a Care Profile.
   - Configure multiple daily dose times (e.g., 08:00, 13:00, 20:00) with pre-dose reminder windows (0–120 minutes).
   - Business validations: end date must be on or after start date; soft-deactivation protection if a medicine already has logged adherence records.
3. **Daily Dose Adherence Checklist (`dose_today`):**
   - Filtered daily checklist showing today's scheduled doses in Philippine local time.
   - One-click actions for caregivers to log doses as **Given** or **Missed**.
   - Database-enforced uniqueness preventing duplicate logs for the same dose time on the same calendar date.
   - Real-time adherence history displaying user attribution and timestamps.
4. **Background Automation:**
   - Management command (`python manage.py mark_missed_doses`) to automatically flag past unrecorded doses as missed.

---

## Increment 1: Account Features (Standard Features)
- **Account Registration:** Role-locked registration (Remote Family Member or Local Caregiver) with email uniqueness validation and password hashing.
- **Authentication:** Email/password login, session logout, and `@login_required` route protection.
- **Role-Based Dashboards:** Dedicated dashboards and URL access guards for Local Caregiver and Remote Family Member roles.
- **User Profile:** Authenticated profile view and update page.

---

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

### Step 5: Optional Background Task for Missed Doses
To automatically mark past unrecorded doses for today as missed:
```powershell
python manage.py mark_missed_doses
```
