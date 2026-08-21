-- EduConnect PostgreSQL bootstrap
-- Run this script against defaultdb. It creates the application tables and
-- temporary role accounts. Change every temporary password after first login.

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    number VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    role VARCHAR(40) NOT NULL CHECK (role IN ('student', 'donor', 'supervisor', 'technician', 'reviewer', 'allocation_officer', 'admin')),
    password_hash VARCHAR(300) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS records (
    id VARCHAR(80) PRIMARY KEY,
    record_type VARCHAR(40) NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS records_record_type_idx ON records (record_type);

CREATE TABLE IF NOT EXISTS session_tokens (
    token VARCHAR(128) PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS session_tokens_user_id_idx ON session_tokens (user_id);

-- Temporary development password for all accounts: EduConnect@2026!
-- The application stores PBKDF2-SHA256 hashes, not plaintext passwords.
INSERT INTO users (number, name, role, password_hash)
VALUES
    ('EDU-ADMIN-001', 'EduConnect Admin', 'admin', 'pbkdf2_sha256$600000$c66befa7ccb9b73d2870b5aa32d14f4d$2bdab55e33cb77717ad5407e8abce2f4ef72fdc29008c60f48f2551b5c409e7d'),
    ('EDU-OFFICER-001', 'Allocation Officer', 'allocation_officer', 'pbkdf2_sha256$600000$c66befa7ccb9b73d2870b5aa32d14f4d$2bdab55e33cb77717ad5407e8abce2f4ef72fdc29008c60f48f2551b5c409e7d'),
    ('EDU-REVIEWER-001', 'Application Reviewer', 'reviewer', 'pbkdf2_sha256$600000$c66befa7ccb9b73d2870b5aa32d14f4d$2bdab55e33cb77717ad5407e8abce2f4ef72fdc29008c60f48f2551b5c409e7d'),
    ('EDU-SUPERVISOR-001', 'Collection Supervisor', 'supervisor', 'pbkdf2_sha256$600000$c66befa7ccb9b73d2870b5aa32d14f4d$2bdab55e33cb77717ad5407e8abce2f4ef72fdc29008c60f48f2551b5c409e7d'),
    ('EDU-TECHNICIAN-001', 'Technical Officer', 'technician', 'pbkdf2_sha256$600000$c66befa7ccb9b73d2870b5aa32d14f4d$2bdab55e33cb77717ad5407e8abce2f4ef72fdc29008c60f48f2551b5c409e7d'),
    ('EDU-STUDENT-001', 'Student Account', 'student', 'pbkdf2_sha256$600000$c66befa7ccb9b73d2870b5aa32d14f4d$2bdab55e33cb77717ad5407e8abce2f4ef72fdc29008c60f48f2551b5c409e7d'),
    ('EDU-DONOR-001', 'Donor Account', 'donor', 'pbkdf2_sha256$600000$c66befa7ccb9b73d2870b5aa32d14f4d$2bdab55e33cb77717ad5407e8abce2f4ef72fdc29008c60f48f2551b5c409e7d')
ON CONFLICT (number) DO NOTHING;

-- No demo applications, students, inventory, or refurbishment records are inserted.
