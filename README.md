# EduConnect

Centralised device-donation, refurbishment and permanent allocation platform for TUT Missing Middle students.

## Structure

- `frontend/` — React, Vite, TypeScript, Axios-ready operations portal.
- `backend/` — FastAPI foundation for PostgreSQL-backed allocation services.

## Run locally

```powershell
cd frontend
pnpm install
pnpm dev
```

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://avnadmin:REPLACE_WITH_PASSWORD@pg-2c79e9bb-ictsport-app.j.aivencloud.com:16958/defaultdb?sslmode=require"
$env:BOOTSTRAP_TOKEN = "REPLACE_WITH_A_LONG_RANDOM_BOOTSTRAP_TOKEN"
uvicorn app.main:app --reload
```

For local development, the API uses `sqlite:///./educonnect.db` by default and creates `backend/educonnect.db` automatically. To use PostgreSQL instead, set `DATABASE_URL` to your PostgreSQL connection string. `BOOTSTRAP_TOKEN` is still required for the secure staff-account bootstrap endpoint. The database stores users, sessions, applications, inventory, students, and refurbishment records; no demo records are seeded.

For a manual database bootstrap, run `backend/sql/bootstrap.sql` with `psql`. The script creates temporary accounts for each role and does not insert demo programme records. Replace the shared temporary password immediately after setup.

Create the first staff account once the API is running:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/auth/bootstrap -Headers @{ 'X-Bootstrap-Token' = $env:BOOTSTRAP_TOKEN } -ContentType 'application/json' -Body (@{ number = 'ADMIN_NUMBER'; name = 'Programme Admin'; role = 'admin'; password = 'USE_A_NEW_PASSWORD_AT_LEAST_12_CHARS' } | ConvertTo-Json)
```

Students and donors can register through `/api/auth/register`; staff accounts must be created through the bootstrap endpoint. Never commit the real `.env` file or expose the database password in source control.

## Core policy model

One canonical FIFO queue uses the timestamp at which an application becomes complete. Faculty views are filters over this one queue, not separate allocation queues. Eligibility requires Missing Middle registration, active Diploma/Advanced Diploma registration, South African citizenship and an academic average of at least 60%. A permanently allocated device cannot normally be allocated again; reservations expire after 14 days if not collected.

## Documented product baseline

The supplied `Problem statement.pdf`, `Planning.docx`, `Missing Middle.pdf`, `Desktop filtered by faculty1.pdf`, and `Device_Allocation_System_Specification_v1.0.docx` define EduConnect as a centralized permanent-allocation system for TUT Missing Middle students. The current frontend is the Allocation Officer operations prototype; its navigation mirrors the required overall and faculty queue, inventory, refurbishment, and student views.

The implementation must preserve these rules as the product is expanded:

- Students must be registered for a TUT Diploma or Advanced Diploma, meet the approved Missing Middle criteria, pass verification, and have an academic average of at least 60%.
- One canonical FIFO population is used. Faculty views are filters and reports, not separate queues or tie-breakers.
- Device matching is based on the student's programme and remaining mandatory academic computing requirements, not faculty alone.
- Technician-recorded hardware specifications are authoritative for matching; refurbishment and quality assurance must be tracked.
- A successful allocation is permanent. A reserved device has a 14-calendar-day collection window and cannot be reserved for two students.
- The target workflow is application, document verification, academic requirement profile, donation/device intake, refurbishment, classification, matching, reservation, collection, permanent handover, notification, and audit explanation.
- The target actors are Student, Donor, Supervisor, Technician, Application Reviewer, Allocation Officer, and System Administrator, with role-controlled access to personal and financial information.

Authentication and core allocation records are now database-backed. Document storage, matching, notifications, and audit persistence remain follow-on capabilities.
