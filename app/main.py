from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .database import engine, SessionLocal, Base
from .models import User, PatientProfile, Appointment, Prescription, MedicalRecord, File
from .seed import seed_database

from .routers.auth_router import router as auth_router
from .routers.patients import router as patients_router
from .routers.appointments import router as appointments_router
from .routers.prescriptions import router as prescriptions_router
from .routers.medical_records import router as records_router
from .routers.files import router as files_router
from .routers.admin import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    Base.metadata.create_all(bind=engine)
    # Seed data
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="🏥 MedClinic API",
    description="""
## MedClinic — Medical Clinic Management System

A REST API for managing patient records, appointments, prescriptions, and medical files.

### Authentication
- **JWT Bearer Token**: Login via `/api/auth/login` to get a token
- **API Key**: Pass `X-API-Key` header with your API key

### Roles
- **patient**: View own data, book appointments
- **doctor**: Manage patients, prescriptions, records
- **nurse**: View patient data, assist with records
- **receptionist**: Manage appointments
- **admin**: Full system access

### Quick Start
1. Login: `POST /api/auth/login` with `{"email": "john@patient.com", "password": "patient123"}`
2. Use the returned `access_token` as Bearer token
3. Explore the API endpoints below
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(appointments_router)
app.include_router(prescriptions_router)
app.include_router(records_router)
app.include_router(files_router)
app.include_router(admin_router)


# Simple landing page
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def landing_page():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MedClinic API</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0f172a;
                color: #e2e8f0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                max-width: 800px;
                padding: 2rem;
                text-align: center;
            }
            h1 {
                font-size: 3rem;
                margin-bottom: 0.5rem;
                background: linear-gradient(135deg, #3b82f6, #8b5cf6);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .subtitle {
                font-size: 1.2rem;
                color: #94a3b8;
                margin-bottom: 2rem;
            }
            .cards {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 1rem;
                margin-bottom: 2rem;
            }
            .card {
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 1.5rem;
                text-align: left;
                transition: border-color 0.2s;
            }
            .card:hover { border-color: #3b82f6; }
            .card h3 { color: #3b82f6; margin-bottom: 0.5rem; }
            .card p { color: #94a3b8; font-size: 0.9rem; }
            .btn {
                display: inline-block;
                padding: 0.75rem 2rem;
                background: linear-gradient(135deg, #3b82f6, #8b5cf6);
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 1.1rem;
                transition: opacity 0.2s;
            }
            .btn:hover { opacity: 0.9; }
            .creds {
                margin-top: 2rem;
                background: #1e293b;
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 1.5rem;
                text-align: left;
            }
            .creds h3 { color: #f59e0b; margin-bottom: 1rem; }
            .creds table { width: 100%; border-collapse: collapse; }
            .creds th, .creds td {
                padding: 0.4rem 0.8rem;
                text-align: left;
                border-bottom: 1px solid #334155;
            }
            .creds th { color: #94a3b8; font-size: 0.8rem; text-transform: uppercase; }
            .creds td { font-size: 0.9rem; }
            .role-badge {
                display: inline-block;
                padding: 0.15rem 0.5rem;
                border-radius: 4px;
                font-size: 0.8rem;
                font-weight: 600;
            }
            .role-patient { background: #065f46; color: #6ee7b7; }
            .role-doctor { background: #1e3a5f; color: #93c5fd; }
            .role-nurse { background: #4c1d95; color: #c4b5fd; }
            .role-receptionist { background: #78350f; color: #fcd34d; }
            .role-admin { background: #7f1d1d; color: #fca5a5; }
            code { background: #334155; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.85rem; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏥 MedClinic API</h1>
            <p class="subtitle">Medical Clinic Management System</p>

            <div class="cards">
                <div class="card">
                    <h3>👤 Patients</h3>
                    <p>Manage patient profiles, medical history, and personal data</p>
                </div>
                <div class="card">
                    <h3>📅 Appointments</h3>
                    <p>Schedule and manage doctor-patient appointments</p>
                </div>
                <div class="card">
                    <h3>💊 Prescriptions</h3>
                    <p>Create and track medication prescriptions</p>
                </div>
                <div class="card">
                    <h3>📋 Records</h3>
                    <p>Store lab results, X-rays, and medical records</p>
                </div>
                <div class="card">
                    <h3>📁 Files</h3>
                    <p>Upload and manage medical documents</p>
                </div>
                <div class="card">
                    <h3>⚙️ Admin</h3>
                    <p>User management and system statistics</p>
                </div>
            </div>

            <a href="/docs" class="btn">📖 Open API Documentation (Swagger)</a>

            <div class="creds">
                <h3>🔐 Test Credentials</h3>
                <table>
                    <tr><th>Email</th><th>Password</th><th>Role</th></tr>
                    <tr><td><code>john@patient.com</code></td><td><code>patient123</code></td><td><span class="role-badge role-patient">patient</span></td></tr>
                    <tr><td><code>jane@patient.com</code></td><td><code>patient123</code></td><td><span class="role-badge role-patient">patient</span></td></tr>
                    <tr><td><code>mike@patient.com</code></td><td><code>patient123</code></td><td><span class="role-badge role-patient">patient</span></td></tr>
                    <tr><td><code>sarah@doctor.com</code></td><td><code>doctor123</code></td><td><span class="role-badge role-doctor">doctor</span></td></tr>
                    <tr><td><code>james@doctor.com</code></td><td><code>doctor123</code></td><td><span class="role-badge role-doctor">doctor</span></td></tr>
                    <tr><td><code>anna@nurse.com</code></td><td><code>nurse123</code></td><td><span class="role-badge role-nurse">nurse</span></td></tr>
                    <tr><td><code>bob@nurse.com</code></td><td><code>nurse123</code></td><td><span class="role-badge role-nurse">nurse</span></td></tr>
                    <tr><td><code>lisa@reception.com</code></td><td><code>reception123</code></td><td><span class="role-badge role-receptionist">receptionist</span></td></tr>
                    <tr><td><code>admin@clinic.com</code></td><td><code>admin123</code></td><td><span class="role-badge role-admin">admin</span></td></tr>
                </table>
            </div>
        </div>
    </body>
    </html>
    """
