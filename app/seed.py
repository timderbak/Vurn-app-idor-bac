import uuid
import os
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session

from .auth import get_password_hash
from .models import User, PatientProfile, Appointment, Prescription, MedicalRecord, File


SEED_USERS = [
    # Patients
    {"email": "john@patient.com", "name": "John Smith", "password": "patient123", "role": "patient", "api_key": "pk_patient_john_123"},
    {"email": "jane@patient.com", "name": "Jane Doe", "password": "patient123", "role": "patient", "api_key": "pk_patient_jane_456"},
    {"email": "mike@patient.com", "name": "Mike Wilson", "password": "patient123", "role": "patient", "api_key": "pk_patient_mike_789"},
    # Doctors
    {"email": "sarah@doctor.com", "name": "Dr. Sarah Connor", "password": "doctor123", "role": "doctor", "api_key": "pk_doctor_sarah_111"},
    {"email": "james@doctor.com", "name": "Dr. James House", "password": "doctor123", "role": "doctor", "api_key": "pk_doctor_james_222"},
    # Nurses
    {"email": "anna@nurse.com", "name": "Nurse Anna Lee", "password": "nurse123", "role": "nurse", "api_key": "pk_nurse_anna_333"},
    {"email": "bob@nurse.com", "name": "Nurse Bob Chen", "password": "nurse123", "role": "nurse", "api_key": "pk_nurse_bob_444"},
    # Receptionists
    {"email": "lisa@reception.com", "name": "Lisa Front", "password": "reception123", "role": "receptionist", "api_key": "pk_recep_lisa_555"},
    {"email": "tom@reception.com", "name": "Tom Desk", "password": "reception123", "role": "receptionist", "api_key": "pk_recep_tom_666"},
    # Admin
    {"email": "admin@clinic.com", "name": "Admin Root", "password": "admin123", "role": "admin", "api_key": "pk_admin_root_777"},
]


def seed_database(db: Session):
    """Seed the database with initial data. Idempotent — skips if data exists."""

    # Check if already seeded
    if db.query(User).count() > 0:
        return

    print("🌱 Seeding database...")

    # --- Create Users ---
    users = {}
    for u in SEED_USERS:
        user = User(
            email=u["email"],
            name=u["name"],
            hashed_password=get_password_hash(u["password"]),
            role=u["role"],
            api_key=u["api_key"],
        )
        db.add(user)
        db.flush()
        users[u["email"]] = user

    # --- Create Patient Profiles ---
    patient_profiles = [
        {
            "user": users["john@patient.com"],
            "dob": "1985-03-15",
            "blood_type": "A+",
            "allergies": "Penicillin, Peanuts",
            "insurance": "INS-001-JKS",
            "phone": "+1-555-0101",
            "address": "123 Main St, Springfield, IL 62701",
            "emergency": "Mary Smith (wife): +1-555-0102",
        },
        {
            "user": users["jane@patient.com"],
            "dob": "1992-07-22",
            "blood_type": "O-",
            "allergies": "None known",
            "insurance": "INS-002-JND",
            "phone": "+1-555-0201",
            "address": "456 Oak Ave, Springfield, IL 62702",
            "emergency": "Bob Doe (father): +1-555-0202",
        },
        {
            "user": users["mike@patient.com"],
            "dob": "1978-11-08",
            "blood_type": "B+",
            "allergies": "Latex, Sulfa drugs",
            "insurance": "INS-003-MKW",
            "phone": "+1-555-0301",
            "address": "789 Pine Rd, Springfield, IL 62703",
            "emergency": "Sarah Wilson (sister): +1-555-0302",
        },
    ]

    for p in patient_profiles:
        profile = PatientProfile(
            user_id=p["user"].id,
            date_of_birth=p["dob"],
            blood_type=p["blood_type"],
            allergies=p["allergies"],
            insurance_number=p["insurance"],
            phone=p["phone"],
            address=p["address"],
            emergency_contact=p["emergency"],
        )
        db.add(profile)

    # --- Create Appointments ---
    appointments_data = [
        {
            "patient": users["john@patient.com"],
            "doctor": users["sarah@doctor.com"],
            "date": "2025-04-10",
            "time": "09:00",
            "status": "completed",
            "notes": "Annual physical exam",
            "diagnosis": "Healthy, mild vitamin D deficiency",
        },
        {
            "patient": users["john@patient.com"],
            "doctor": users["james@doctor.com"],
            "date": "2025-04-25",
            "time": "14:30",
            "status": "scheduled",
            "notes": "Follow-up for blood test results",
            "diagnosis": None,
        },
        {
            "patient": users["jane@patient.com"],
            "doctor": users["sarah@doctor.com"],
            "date": "2025-04-12",
            "time": "10:00",
            "status": "completed",
            "notes": "Persistent cough for 2 weeks",
            "diagnosis": "Upper respiratory infection",
        },
        {
            "patient": users["jane@patient.com"],
            "doctor": users["sarah@doctor.com"],
            "date": "2025-05-01",
            "time": "11:00",
            "status": "scheduled",
            "notes": "Cough follow-up",
            "diagnosis": None,
        },
        {
            "patient": users["mike@patient.com"],
            "doctor": users["james@doctor.com"],
            "date": "2025-04-15",
            "time": "16:00",
            "status": "completed",
            "notes": "Knee pain after running",
            "diagnosis": "Mild patellar tendinitis",
        },
        {
            "patient": users["mike@patient.com"],
            "doctor": users["james@doctor.com"],
            "date": "2025-05-10",
            "time": "09:30",
            "status": "scheduled",
            "notes": "Physical therapy progress check",
            "diagnosis": None,
        },
    ]

    for a in appointments_data:
        appt = Appointment(
            patient_id=a["patient"].id,
            doctor_id=a["doctor"].id,
            date=a["date"],
            time=a["time"],
            status=a["status"],
            notes=a["notes"],
            diagnosis=a["diagnosis"],
        )
        db.add(appt)

    # --- Create Prescriptions ---
    prescriptions_data = [
        {
            "patient": users["john@patient.com"],
            "doctor": users["sarah@doctor.com"],
            "medication": "Vitamin D3",
            "dosage": "2000 IU",
            "frequency": "Once daily",
            "duration": "3 months",
            "notes": "Take with food",
            "status": "active",
        },
        {
            "patient": users["jane@patient.com"],
            "doctor": users["sarah@doctor.com"],
            "medication": "Amoxicillin",
            "dosage": "500mg",
            "frequency": "Three times daily",
            "duration": "10 days",
            "notes": "Complete full course even if symptoms improve",
            "status": "active",
        },
        {
            "patient": users["jane@patient.com"],
            "doctor": users["sarah@doctor.com"],
            "medication": "Dextromethorphan",
            "dosage": "30mg",
            "frequency": "Every 6-8 hours as needed",
            "duration": "1 week",
            "notes": "Do not exceed 4 doses in 24 hours",
            "status": "active",
        },
        {
            "patient": users["mike@patient.com"],
            "doctor": users["james@doctor.com"],
            "medication": "Ibuprofen",
            "dosage": "400mg",
            "frequency": "Twice daily with meals",
            "duration": "2 weeks",
            "notes": "Take with food to avoid stomach irritation",
            "status": "active",
        },
    ]

    for rx in prescriptions_data:
        prescription = Prescription(
            id=str(uuid.uuid4()),
            patient_id=rx["patient"].id,
            doctor_id=rx["doctor"].id,
            medication=rx["medication"],
            dosage=rx["dosage"],
            frequency=rx["frequency"],
            duration=rx["duration"],
            notes=rx["notes"],
            status=rx["status"],
        )
        db.add(prescription)

    # --- Create Medical Records ---
    records_data = [
        {
            "patient": users["john@patient.com"],
            "doctor": users["sarah@doctor.com"],
            "type": "blood_test",
            "result": "WBC: 6.5, RBC: 4.8, Hemoglobin: 14.5, Vitamin D: 18 ng/mL (low)",
            "notes": "Vitamin D deficiency detected. Supplement recommended.",
        },
        {
            "patient": users["jane@patient.com"],
            "doctor": users["sarah@doctor.com"],
            "type": "general_checkup",
            "result": "Lungs: mild crackles in lower right lobe. Throat: red, slightly swollen.",
            "notes": "Consistent with upper respiratory infection.",
        },
        {
            "patient": users["mike@patient.com"],
            "doctor": users["james@doctor.com"],
            "type": "xray",
            "result": "No fracture detected. Soft tissue swelling around patella.",
            "notes": "X-ray of right knee. Findings consistent with tendinitis.",
        },
        {
            "patient": users["john@patient.com"],
            "doctor": users["sarah@doctor.com"],
            "type": "general_checkup",
            "result": "BP: 120/80, HR: 72, Weight: 82kg, Height: 178cm, BMI: 25.9",
            "notes": "Overall healthy. Slight overweight. Diet counseling provided.",
        },
    ]

    for r in records_data:
        record = MedicalRecord(
            patient_id=r["patient"].id,
            doctor_id=r["doctor"].id,
            record_type=r["type"],
            result=r["result"],
            notes=r["notes"],
        )
        db.add(record)

    # --- Create Sample Files ---
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)

    files_data = [
        {
            "owner": users["john@patient.com"],
            "filename": "1_bloodwork_results.pdf",
            "original": "bloodwork_results_2025.pdf",
            "type": "application/pdf",
            "content": "CONFIDENTIAL - John Smith Blood Test Results 2025\nVitamin D: 18 ng/mL\nCholesterol: 195 mg/dL",
        },
        {
            "owner": users["mike@patient.com"],
            "filename": "3_knee_xray_report.pdf",
            "original": "knee_xray_march2025.pdf",
            "type": "application/pdf",
            "content": "CONFIDENTIAL - Mike Wilson Knee X-Ray Report\nRight knee, AP and lateral views\nNo fracture. Soft tissue swelling.",
        },
        {
            "owner": users["sarah@doctor.com"],
            "filename": "4_treatment_protocol.pdf",
            "original": "uri_treatment_protocol.pdf",
            "type": "application/pdf",
            "content": "INTERNAL - Upper Respiratory Infection Treatment Protocol\nDr. Sarah Connor\nFirst-line: Amoxicillin 500mg TID x 10 days",
        },
    ]

    for f in files_data:
        # Create actual files on disk
        file_path = uploads_dir / f["filename"]
        with open(file_path, "w") as fh:
            fh.write(f["content"])

        file_record = File(
            owner_id=f["owner"].id,
            filename=f["filename"],
            original_name=f["original"],
            file_path=str(file_path),
            file_type=f["type"],
        )
        db.add(file_record)

    db.commit()
    print("✅ Database seeded successfully!")
    print(f"   - {len(SEED_USERS)} users")
    print(f"   - {len(patient_profiles)} patient profiles")
    print(f"   - {len(appointments_data)} appointments")
    print(f"   - {len(prescriptions_data)} prescriptions")
    print(f"   - {len(records_data)} medical records")
    print(f"   - {len(files_data)} files")
