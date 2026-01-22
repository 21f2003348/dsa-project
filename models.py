"""
Database Models for ICU Management System

SQLAlchemy ORM models that map to the DSA structures:
- PatientModel -> Patient class
- DoctorModel -> Doctor class
- BedModel -> ICUBed class
- AllocationModel -> AllocationRecord class
- WaitingQueueModel -> WaitingQueueNode class
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class PatientModel(db.Model):
    """Patient database model"""
    __tablename__ = 'patients'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Patient Information
    patient_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    
    # Medical Information
    severity_level = db.Column(db.Integer, nullable=False)  # 1-10 (1=Critical, 10=Stable)
    medical_notes = db.Column(db.Text, default="")
    
    # Status
    status = db.Column(db.String(20), nullable=False, default="WAITING")  # WAITING, IN_ICU, DISCHARGED
    
    # Resource Assignment
    assigned_bed_id = db.Column(db.Integer, db.ForeignKey('beds.bed_id'), nullable=True)
    assigned_doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=True)
    
    # Timestamps
    arrival_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    assignment_time = db.Column(db.DateTime, nullable=True)
    discharge_time = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    bed = db.relationship('BedModel', back_populates='patient')
    doctor = db.relationship('DoctorModel', back_populates='patients')
    allocations = db.relationship('AllocationModel', back_populates='patient', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Patient {self.patient_id}: {self.name}>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'patient_id': self.patient_id,
            'name': self.name,
            'age': self.age,
            'severity_level': self.severity_level,
            'medical_notes': self.medical_notes,
            'status': self.status,
            'assigned_bed_id': self.assigned_bed_id,
            'assigned_doctor_id': self.assigned_doctor_id,
            'arrival_time': self.arrival_time.isoformat() if self.arrival_time else None,
            'assignment_time': self.assignment_time.isoformat() if self.assignment_time else None,
            'discharge_time': self.discharge_time.isoformat() if self.discharge_time else None
        }


class DoctorModel(db.Model):
    """Doctor database model"""
    __tablename__ = 'doctors'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Doctor Information
    doctor_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    experience_years = db.Column(db.Integer, nullable=False)
    specialization = db.Column(db.String(50), nullable=False, default="GENERAL")
    
    # Capacity Management
    max_capacity = db.Column(db.Integer, nullable=False, default=5)
    current_workload = db.Column(db.Integer, nullable=False, default=0)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patients = db.relationship('PatientModel', back_populates='doctor')
    allocations = db.relationship('AllocationModel', back_populates='doctor', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Doctor {self.doctor_id}: Dr. {self.name}>"
    
    def get_priority_score(self):
        """Calculate priority score for heap"""
        return self.experience_years - self.current_workload
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'doctor_id': self.doctor_id,
            'name': self.name,
            'experience_years': self.experience_years,
            'specialization': self.specialization,
            'max_capacity': self.max_capacity,
            'current_workload': self.current_workload,
            'is_available': self.is_available,
            'priority_score': self.get_priority_score()
        }


class BedModel(db.Model):
    """ICU Bed database model"""
    __tablename__ = 'beds'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Bed Information
    bed_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    bed_type = db.Column(db.String(50), nullable=False, default="GENERAL")
    
    # Status
    is_occupied = db.Column(db.Boolean, nullable=False, default=False)
    assigned_patient_id = db.Column(db.String(50), nullable=True)
    
    # Timestamps
    last_occupied_time = db.Column(db.DateTime, nullable=True)
    last_freed_time = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    patient = db.relationship('PatientModel', back_populates='bed', uselist=False)
    
    def __repr__(self):
        status = "OCCUPIED" if self.is_occupied else "FREE"
        return f"<Bed {self.bed_id}: {status}>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'bed_id': self.bed_id,
            'bed_type': self.bed_type,
            'is_occupied': self.is_occupied,
            'assigned_patient_id': self.assigned_patient_id,
            'last_occupied_time': self.last_occupied_time.isoformat() if self.last_occupied_time else None,
            'last_freed_time': self.last_freed_time.isoformat() if self.last_freed_time else None
        }


class AllocationModel(db.Model):
    """Allocation Record database model"""
    __tablename__ = 'allocations'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Record Information
    record_id = db.Column(db.Integer, unique=True, nullable=False, index=True)
    
    # References
    patient_id = db.Column(db.String(50), db.ForeignKey('patients.patient_id'), nullable=False)
    bed_id = db.Column(db.Integer, nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.doctor_id'), nullable=False)
    
    # Snapshots
    patient_severity = db.Column(db.Integer, nullable=False)
    doctor_priority_score = db.Column(db.Integer, nullable=False)
    
    # Metadata
    allocation_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    decision_reason = db.Column(db.String(50), nullable=False, default="AUTOMATIC")
    
    # Relationships
    patient = db.relationship('PatientModel', back_populates='allocations')
    doctor = db.relationship('DoctorModel', back_populates='allocations')
    
    def __repr__(self):
        return f"<Allocation {self.record_id}: Patient {self.patient_id} -> Bed {self.bed_id}>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'record_id': self.record_id,
            'patient_id': self.patient_id,
            'bed_id': self.bed_id,
            'doctor_id': self.doctor_id,
            'patient_severity': self.patient_severity,
            'doctor_priority_score': self.doctor_priority_score,
            'allocation_time': self.allocation_time.isoformat() if self.allocation_time else None,
            'decision_reason': self.decision_reason
        }


class WaitingQueueModel(db.Model):
    """Waiting Queue database model"""
    __tablename__ = 'waiting_queue'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Queue Information
    patient_id = db.Column(db.String(50), nullable=False, index=True)
    priority_snapshot = db.Column(db.Integer, nullable=False)
    
    # Timestamps
    enqueue_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    position = db.Column(db.Integer, nullable=False)  # Position in queue (for FIFO ordering)
    
    def __repr__(self):
        return f"<WaitingQueue: Patient {self.patient_id} at position {self.position}>"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'patient_id': self.patient_id,
            'priority_snapshot': self.priority_snapshot,
            'enqueue_time': self.enqueue_time.isoformat() if self.enqueue_time else None,
            'position': self.position
        }
