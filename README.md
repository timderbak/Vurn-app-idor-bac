# 🏥 VurnApp — Vulnerable Medical API (IDOR & BAC)

A **deliberately vulnerable** FastAPI application simulating a medical clinic management system. Built for learning and practicing **IDOR (Insecure Direct Object Reference)** and **BAC (Broken Access Control)** vulnerability detection and exploitation.

> ⚠️ **WARNING**: This application contains intentional security vulnerabilities. **DO NOT deploy in production.** Use only in isolated lab environments for educational purposes.

## 🎯 Purpose

This project provides a realistic medical API with **20+ intentional vulnerabilities** across multiple categories, designed as a hands-on training lab for:

- Security researchers & bug bounty hunters
- Penetration testers
- AppSec engineers
- Students learning web application security

## 🔓 Vulnerability Categories

| Category | Code | Description | Count |
|----------|------|-------------|-------|
| **IDOR** | I1–I11 | Horizontal & vertical object reference flaws | 11 |
| **Broken Access Control** | B1–B11 | Missing auth, role checks, mass assignment | 11 |

### IDOR Vulnerabilities (I1–I11)
- **Horizontal IDOR**: Access other users' profiles, appointments, prescriptions, medical records
- **Vertical IDOR**: Patients accessing doctor/admin-only endpoints
- **ID Enumeration**: Sequential IDs exposed in responses
- **File Access IDOR**: Download any patient's medical files

### Broken Access Control (B1–B11)
- **Missing function-level checks**: Endpoints accessible without proper role verification
- **Mass assignment**: Role escalation via registration/update endpoints
- **Method-based bypass**: DELETE without authentication while GET requires it
- **Parameter tampering**: Creating resources on behalf of other users
- **Missing authentication**: Admin endpoints without any auth

## 🏗️ Tech Stack

- **Framework**: FastAPI 0.104
- **Database**: SQLite (via SQLAlchemy 2.0)
- **Auth**: JWT Bearer tokens + API Key authentication
- **Password hashing**: passlib + bcrypt
- **Python**: 3.9+

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/timderbak/Vurn-app-idor-bac.git
cd Vurn-app-idor-bac

# Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The database is automatically seeded on first launch with test data.

## 📚 API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 👥 Test Accounts

| Email | Password | Role |
|-------|----------|------|
| `john@patient.com` | `patient123` | patient |
| `jane@patient.com` | `patient123` | patient |
| `bob@patient.com` | `patient123` | patient |
| `dr.smith@clinic.com` | `doctor123` | doctor |
| `dr.jones@clinic.com` | `doctor123` | doctor |
| `nurse.wilson@clinic.com` | `nurse123` | nurse |
| `admin@clinic.com` | `admin123` | admin |
| `reception@clinic.com` | `reception123` | receptionist |

## 🔑 Authentication

### JWT Token
```bash
# Login to get a token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"john@patient.com","password":"patient123"}'

# Use the token
curl http://localhost:8000/api/patients/ \
  -H "Authorization: Bearer <your_token>"
```

### API Key
```bash
curl http://localhost:8000/api/patients/ \
  -H "X-API-Key: pk_patient_john_123"
```

## 📁 Project Structure

```
Vurn-app-idor-bac/
├── app/
│   ├── main.py              # FastAPI app, lifespan, CORS
│   ├── auth.py               # JWT + API Key authentication
│   ├── database.py           # SQLAlchemy engine & session
│   ├── models.py             # ORM models (User, Patient, etc.)
│   ├── seed.py               # Database seeding with test data
│   └── routers/
│       ├── auth_router.py    # Login, register, token refresh
│       ├── patients.py       # Patient profile CRUD
│       ├── appointments.py   # Appointment management
│       ├── prescriptions.py  # Prescription management
│       ├── medical_records.py # Medical record management
│       ├── files.py          # File upload/download
│       └── admin.py          # Admin panel endpoints
├── requirements.txt
├── .gitignore
└── README.md
```

## 📝 License

This project is for **educational purposes only**. Use responsibly.
