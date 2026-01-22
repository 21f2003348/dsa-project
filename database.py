"""
Database initialization and default data seeding

This module handles:
- Database creation
- Default data seeding (beds, doctors)
- Data loading from database into DSA structures
"""

from models import db, PatientModel, DoctorModel, BedModel, AllocationModel, WaitingQueueModel
from structure import DoctorSpecialization
from datetime import datetime
import os


def init_database(app):
    """
    Initialize database and create all tables
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully")


def check_database_exists(app):
    """
    Check if database file exists
    
    Args:
        app: Flask application instance
        
    Returns:
        bool: True if database exists, False otherwise
    """
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    return os.path.exists(db_path)


def seed_default_data(app):
    """
    Seed database with default beds and doctors
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        # Check if data already exists
        if BedModel.query.first() is not None:
            print("ℹ️  Database already contains data. Skipping seeding.")
            return
        
        print("🌱 Seeding default data...")
        
        # Create default beds with a mix of types
        num_beds = app.config.get('DEFAULT_NUM_BEDS', 10)
        bed_types = ["GENERAL", "VENTILATOR", "ISOLATION"]
        for i in range(num_beds):
            bed_type = bed_types[i % len(bed_types)]
            bed = BedModel(
                bed_id=i,
                bed_type=bed_type,
                is_occupied=False,
                assigned_patient_id=None
            )
            db.session.add(bed)
        print(f"   ✓ Created {num_beds} ICU beds (types: {', '.join(bed_types)})")
        
        # Create default doctors
        default_doctors = [
            {
                'doctor_id': 1,
                'name': 'Dr. Sarah Johnson',
                'experience_years': 15,
                'specialization': DoctorSpecialization.CARDIAC.value,
                'max_capacity': 5
            },
            {
                'doctor_id': 2,
                'name': 'Dr. Michael Chen',
                'experience_years': 12,
                'specialization': DoctorSpecialization.NEURO.value,
                'max_capacity': 5
            },
            {
                'doctor_id': 3,
                'name': 'Dr. Emily Rodriguez',
                'experience_years': 10,
                'specialization': DoctorSpecialization.PULMONARY.value,
                'max_capacity': 5
            },
            {
                'doctor_id': 4,
                'name': 'Dr. James Wilson',
                'experience_years': 8,
                'specialization': DoctorSpecialization.GENERAL.value,
                'max_capacity': 6
            },
            {
                'doctor_id': 5,
                'name': 'Dr. Lisa Anderson',
                'experience_years': 6,
                'specialization': DoctorSpecialization.GENERAL.value,
                'max_capacity': 6
            }
        ]
        
        for doc_data in default_doctors:
            doctor = DoctorModel(
                doctor_id=doc_data['doctor_id'],
                name=doc_data['name'],
                experience_years=doc_data['experience_years'],
                specialization=doc_data['specialization'],
                max_capacity=doc_data['max_capacity'],
                current_workload=0,
                is_available=True
            )
            db.session.add(doctor)
        print(f"   ✓ Created {len(default_doctors)} doctors")
        
        # Commit all changes
        db.session.commit()
        print("✅ Default data seeded successfully")


def get_next_patient_id(app):
    """
    Get next available patient ID
    
    Args:
        app: Flask application instance
        
    Returns:
        str: Next patient ID (e.g., 'P001')
    """
    with app.app_context():
        last_patient = PatientModel.query.order_by(PatientModel.id.desc()).first()
        if last_patient:
            # Extract number from patient_id (e.g., 'P001' -> 1)
            last_num = int(last_patient.patient_id[1:])
            return f"P{last_num + 1:03d}"
        return "P001"


def get_next_doctor_id(app):
    """
    Get next available doctor ID
    
    Args:
        app: Flask application instance
        
    Returns:
        int: Next doctor ID
    """
    with app.app_context():
        last_doctor = DoctorModel.query.order_by(DoctorModel.doctor_id.desc()).first()
        if last_doctor:
            return last_doctor.doctor_id + 1
        return 1


def get_next_allocation_id(app):
    """
    Get next available allocation record ID
    
    Args:
        app: Flask application instance
        
    Returns:
        int: Next allocation record ID
    """
    with app.app_context():
        last_allocation = AllocationModel.query.order_by(AllocationModel.record_id.desc()).first()
        if last_allocation:
            return last_allocation.record_id + 1
        return 1


def clear_database(app):
    """
    Clear all data from database (useful for testing)
    
    Args:
        app: Flask application instance
    """
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("✅ Database cleared and recreated")


def get_database_stats(app):
    """
    Get database statistics
    
    Args:
        app: Flask application instance
        
    Returns:
        dict: Database statistics
    """
    with app.app_context():
        return {
            'total_patients': PatientModel.query.count(),
            'total_doctors': DoctorModel.query.count(),
            'total_beds': BedModel.query.count(),
            'total_allocations': AllocationModel.query.count(),
            'patients_in_icu': PatientModel.query.filter_by(status='IN_ICU').count(),
            'patients_waiting': WaitingQueueModel.query.count(),
            'patients_discharged': PatientModel.query.filter_by(status='DISCHARGED').count(),
            'beds_occupied': BedModel.query.filter_by(is_occupied=True).count(),
            'beds_free': BedModel.query.filter_by(is_occupied=False).count()
        }
