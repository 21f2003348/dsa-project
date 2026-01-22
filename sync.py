"""
Synchronization layer between database and DSA structures

This module bridges the gap between persistent database storage
and in-memory DSA structures (linked lists, heaps, queues).

Key functions:
- load_data_from_db(): Load all data from DB into DSA structures
- sync_to_db(): Save DSA structures to database
"""

from models import db, PatientModel, DoctorModel, BedModel, AllocationModel, WaitingQueueModel
from structure import (
    Patient, Doctor, ICUBed, AllocationRecord, WaitingQueueNode,
    PatientStatus, DoctorSpecialization, BedType, AllocationReason,
    ICUManagementSystem
)
from Operations.patient import PatientListOperations
from Operations.doctor import DoctorHeapOperations
from Operations.bed import BedArrayOperations
from Operations.queue import WaitingQueueOperations
from Operations.log import AllocationLogOperations
from datetime import datetime


def load_system_from_db(app, system):
    """
    Load all data from database into DSA structures
    
    Args:
        app: Flask application instance
        system: ICUManagementSystem instance to populate
        
    Returns:
        ICUManagementSystem: Populated system
    """
    with app.app_context():
        print("📥 Loading data from database into DSA structures...")
        
        # Load beds
        beds_loaded = sync_beds_from_db(system)
        print(f"   ✓ Loaded {beds_loaded} beds")
        
        # Load doctors
        doctors_loaded = sync_doctors_from_db(system)
        print(f"   ✓ Loaded {doctors_loaded} doctors")
        
        # Load patients
        patients_loaded = sync_patients_from_db(system)
        print(f"   ✓ Loaded {patients_loaded} patients")
        
        # Load waiting queue
        queue_loaded = sync_waiting_queue_from_db(system)
        print(f"   ✓ Loaded {queue_loaded} waiting patients")
        
        # Load allocation log
        allocations_loaded = sync_allocations_from_db(system)
        print(f"   ✓ Loaded {allocations_loaded} allocation records")
        
        print("✅ Data loaded successfully into DSA structures")
        
        return system


def sync_beds_from_db(system):
    """
    Load beds from database into bed array
    
    Args:
        system: ICUManagementSystem instance
        
    Returns:
        int: Number of beds loaded
    """
    from structure import BedType
    
    bed_models = BedModel.query.order_by(BedModel.bed_id).all()
    
    for bed_model in bed_models:
        # Update existing bed in array
        if bed_model.bed_id < len(system.beds.beds):
            bed = system.beds.beds[bed_model.bed_id]
            # Ensure bed type is set correctly from DB
            bed.bed_type = BedType(bed_model.bed_type)
            bed.is_occupied = bed_model.is_occupied
            bed.assigned_patient_id = bed_model.assigned_patient_id
            bed.last_occupied_time = bed_model.last_occupied_time
            bed.last_freed_time = bed_model.last_freed_time
    
    return len(bed_models)


def sync_doctors_from_db(system):
    """
    Load doctors from database into doctor heap
    
    Args:
        system: ICUManagementSystem instance
        
    Returns:
        int: Number of doctors loaded
    """
    doctor_models = DoctorModel.query.all()
    
    # Build a mapping of doctor_id to Doctor object
    doctor_map = {}
    for doc_model in doctor_models:
        doctor = Doctor(
            doctor_id=doc_model.doctor_id,
            name=doc_model.name,
            experience_years=doc_model.experience_years,
            specialization=DoctorSpecialization(doc_model.specialization),
            max_capacity=doc_model.max_capacity
        )
        doctor.is_available = doc_model.is_available
        doctor_map[doctor.doctor_id] = doctor
        DoctorHeapOperations.insert_doctor(system.doctors, doctor)

    # Assign patients to doctors and set workload
    patient_models = PatientModel.query.all()
    for patient in patient_models:
        if patient.assigned_doctor_id is not None and patient.status in ('IN_ICU', 'STABLE'):
            doc = doctor_map.get(patient.assigned_doctor_id)
            if doc:
                doc.assigned_patients.append(patient.patient_id)
                doc.current_workload += 1
    return len(doctor_models)
    
    return len(doctor_models)


def sync_patients_from_db(system):
    """
    Load patients from database into patient linked list
    
    Args:
        system: ICUManagementSystem instance
        
    Returns:
        int: Number of patients loaded
    """
    patient_models = PatientModel.query.all()
    
    for patient_model in patient_models:
        # Create Patient object
        patient = Patient(
            patient_id=patient_model.patient_id,
            name=patient_model.name,
            age=patient_model.age,
            severity_level=patient_model.severity_level,
            medical_notes=patient_model.medical_notes or ""
        )
        
        # Set status and timestamps
        patient.status = PatientStatus(patient_model.status)
        patient.arrival_time = patient_model.arrival_time
        patient.assignment_time = patient_model.assignment_time
        patient.discharge_time = patient_model.discharge_time
        
        # Set assignments
        patient.assigned_bed_id = patient_model.assigned_bed_id
        patient.assigned_doctor_id = patient_model.assigned_doctor_id
        
        # If patient is waiting, try to infer requested bed type from medical notes
        # or set a default based on status
        if patient.status == PatientStatus.WAITING:
            # Try to extract bed type from medical notes if stored there
            # Format: "REQUESTED_BED_TYPE:ISOLATION" or similar
            if patient_model.medical_notes and "REQUESTED_BED_TYPE:" in patient_model.medical_notes:
                for line in patient_model.medical_notes.split('\n'):
                    if "REQUESTED_BED_TYPE:" in line:
                        bed_type = line.split("REQUESTED_BED_TYPE:")[1].strip()
                        setattr(patient, 'requested_bed_type', bed_type)
                        break
            # If not found, check if we can infer from any previous bed assignment
            # For now, default to GENERAL if not specified
            if not hasattr(patient, 'requested_bed_type'):
                setattr(patient, 'requested_bed_type', 'GENERAL')
        
        # Add to linked list
        PatientListOperations.insert_at_tail(system.patients, patient)
        system.total_patients_admitted += 1
    
    return len(patient_models)


def sync_waiting_queue_from_db(system):
    """
    Load waiting queue from database
    
    Args:
        system: ICUManagementSystem instance
        
    Returns:
        int: Number of waiting patients loaded
    """
    queue_models = WaitingQueueModel.query.order_by(WaitingQueueModel.position).all()
    
    for queue_model in queue_models:
        # Add to queue using correct signature
        WaitingQueueOperations.enqueue(
            system.waiting_queue,
            queue_model.patient_id,
            queue_model.priority_snapshot
        )
        # Optionally, set enqueue_time if needed (not supported by enqueue directly)
        # This would require a custom method or direct manipulation if needed for audit
    return len(queue_models)


def sync_allocations_from_db(system):
    """
    Load allocation log from database
    
    Args:
        system: ICUManagementSystem instance
        
    Returns:
        int: Number of allocations loaded
    """
    allocation_models = AllocationModel.query.order_by(AllocationModel.record_id).all()
    
    for alloc_model in allocation_models:
        # Create AllocationRecord
        record = AllocationRecord(
            record_id=alloc_model.record_id,
            patient_id=alloc_model.patient_id,
            bed_id=alloc_model.bed_id,
            doctor_id=alloc_model.doctor_id,
            patient_severity=alloc_model.patient_severity,
            doctor_priority_score=alloc_model.doctor_priority_score,
            decision_reason=AllocationReason(alloc_model.decision_reason)
        )
        record.allocation_time = alloc_model.allocation_time
        
        # Add to log
        system.allocation_log.records.append(record)
        
        # Update next_record_id
        if alloc_model.record_id >= system.allocation_log.next_record_id:
            system.allocation_log.next_record_id = alloc_model.record_id + 1
    
    return len(allocation_models)


# Database persistence functions (called from allocator)

def save_patient_to_db(patient):
    """
    Save or update patient in database
    
    Args:
        patient: Patient object
    """
    patient_model = PatientModel.query.filter_by(patient_id=patient.patient_id).first()
    
    if patient_model:
        # Update existing
        patient_model.name = patient.name
        patient_model.age = patient.age
        patient_model.severity_level = patient.severity_level
        patient_model.medical_notes = patient.medical_notes
        patient_model.status = patient.status.value
        patient_model.assigned_bed_id = patient.assigned_bed_id
        patient_model.assigned_doctor_id = patient.assigned_doctor_id
        patient_model.assignment_time = patient.assignment_time
        patient_model.discharge_time = patient.discharge_time
    else:
        # Create new
        patient_model = PatientModel(
            patient_id=patient.patient_id,
            name=patient.name,
            age=patient.age,
            severity_level=patient.severity_level,
            medical_notes=patient.medical_notes,
            status=patient.status.value,
            assigned_bed_id=patient.assigned_bed_id,
            assigned_doctor_id=patient.assigned_doctor_id,
            arrival_time=patient.arrival_time,
            assignment_time=patient.assignment_time,
            discharge_time=patient.discharge_time
        )
        db.session.add(patient_model)
    
    db.session.commit()


def save_doctor_to_db(doctor):
    """
    Save or update doctor in database
    
    Args:
        doctor: Doctor object
    """
    doctor_model = DoctorModel.query.filter_by(doctor_id=doctor.doctor_id).first()
    
    if doctor_model:
        # Update existing
        doctor_model.name = doctor.name
        doctor_model.experience_years = doctor.experience_years
        doctor_model.specialization = doctor.specialization.value
        doctor_model.max_capacity = doctor.max_capacity
        doctor_model.current_workload = doctor.current_workload
        doctor_model.is_available = doctor.is_available
        doctor_model.updated_at = datetime.utcnow()
    else:
        # Create new
        doctor_model = DoctorModel(
            doctor_id=doctor.doctor_id,
            name=doctor.name,
            experience_years=doctor.experience_years,
            specialization=doctor.specialization.value,
            max_capacity=doctor.max_capacity,
            current_workload=doctor.current_workload,
            is_available=doctor.is_available
        )
        db.session.add(doctor_model)
    
    db.session.commit()


def save_bed_to_db(bed):
    """
    Save or update bed in database
    
    Args:
        bed: ICUBed object
    """
    bed_model = BedModel.query.filter_by(bed_id=bed.bed_id).first()
    
    if bed_model:
        # Update existing
        bed_model.is_occupied = bed.is_occupied
        bed_model.assigned_patient_id = bed.assigned_patient_id
        bed_model.last_occupied_time = bed.last_occupied_time
        bed_model.last_freed_time = bed.last_freed_time
    else:
        # Create new
        bed_model = BedModel(
            bed_id=bed.bed_id,
            bed_type=bed.bed_type.value,
            is_occupied=bed.is_occupied,
            assigned_patient_id=bed.assigned_patient_id,
            last_occupied_time=bed.last_occupied_time,
            last_freed_time=bed.last_freed_time
        )
        db.session.add(bed_model)
    
    db.session.commit()


def save_allocation_to_db(allocation):
    """
    Save allocation record to database
    
    Args:
        allocation: AllocationRecord object
    """
    allocation_model = AllocationModel(
        record_id=allocation.record_id,
        patient_id=allocation.patient_id,
        bed_id=allocation.bed_id,
        doctor_id=allocation.doctor_id,
        patient_severity=allocation.patient_severity,
        doctor_priority_score=allocation.doctor_priority_score,
        allocation_time=allocation.allocation_time,
        decision_reason=allocation.decision_reason.value
    )
    db.session.add(allocation_model)
    db.session.commit()


def save_to_waiting_queue_db(patient_id, priority_snapshot, position):
    """
    Add patient to waiting queue in database
    
    Args:
        patient_id: Patient ID
        priority_snapshot: Severity level snapshot
        position: Position in queue
    """
    queue_model = WaitingQueueModel(
        patient_id=patient_id,
        priority_snapshot=priority_snapshot,
        position=position
    )
    db.session.add(queue_model)
    db.session.commit()


def remove_from_waiting_queue_db(patient_id):
    """
    Remove patient from waiting queue in database
    
    Args:
        patient_id: Patient ID to remove
    """
    WaitingQueueModel.query.filter_by(patient_id=patient_id).delete()
    db.session.commit()
    
    # Reorder positions
    remaining = WaitingQueueModel.query.order_by(WaitingQueueModel.position).all()
    for idx, queue_model in enumerate(remaining):
        queue_model.position = idx
    db.session.commit()
