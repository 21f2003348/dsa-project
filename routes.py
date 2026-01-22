"""
Flask Routes for ICU Management System

All application routes and view functions
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from models import db, PatientModel, DoctorModel, BedModel
from structure import DoctorSpecialization
from sync import save_patient_to_db, save_doctor_to_db, save_bed_to_db, save_allocation_to_db
from database import get_next_patient_id, get_next_doctor_id, get_database_stats
from datetime import datetime
import app as app_module
from io import BytesIO, StringIO
import csv


# Create blueprint
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Dashboard/Home page"""
    system = app_module.icu_system
    allocator = app_module.allocator
    
    if not system:
        from flask import current_app
        app_module.initialize_system(current_app)
        system = app_module.icu_system
        allocator = app_module.allocator
    
    # Get system status
    status = allocator.get_system_status()
    
    # Get recent allocations (last 5)
    recent_allocations = list(system.allocation_log.records)[-5:]
    recent_allocations.reverse()
    
    # Get waiting queue
    waiting_patients = []
    for node in system.waiting_queue.queue:
        from Operations.patient import PatientListOperations
        patient = PatientListOperations.search_by_id(system.patients, node.patient_id)
        if patient:
            waiting_patients.append({
                'patient': patient,
                'wait_time': (datetime.now() - node.enqueue_time).total_seconds() / 60  # minutes
            })
    
    return render_template('dashboard.html',
                         status=status,
                         recent_allocations=recent_allocations,
                         waiting_patients=waiting_patients)


@main_bp.route('/patients/admit', methods=['GET', 'POST'])
def admit_patient():
    """Admit new patient"""
    system = app_module.icu_system
    allocator = app_module.allocator
    
    if request.method == 'POST':
        # Get form data
        patient_id = request.form.get('patient_id')
        if not patient_id or patient_id == 'auto':
            # Auto-generate ID
            from flask import current_app
            patient_id = get_next_patient_id(current_app)

        name = request.form.get('name')
        age = int(request.form.get('age'))
        severity = int(request.form.get('severity'))
        notes = request.form.get('medical_notes', '')
        needs_bed = 'needs_bed' in request.form
        bed_type = request.form.get('bed_type', 'GENERAL')

        # Admit patient
        if allocator is None:
            flash("System not initialized. Please initialize the system first.", "danger")
            return redirect(url_for('main.initialize'))
        success, message = allocator.admit_patient(patient_id, name, age, severity, notes, needs_bed, bed_type)

        if success:
            flash(message, 'success')
        else:
            flash(message, 'danger')

        return redirect(url_for('main.index'))
    
    # GET request - show form
    from flask import current_app
    next_id = get_next_patient_id(current_app)
    return render_template('admit_patient.html', next_patient_id=next_id)


@main_bp.route('/patients/discharge', methods=['GET', 'POST'])
def discharge_patient():
    """Discharge patient"""
    system = app_module.icu_system
    allocator = app_module.allocator
    
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        
        # Discharge patient
        success, message = allocator.discharge_patient(patient_id)
        
        if success:
            flash(message, 'success')
        else:
            flash(message, 'error')
        
        return redirect(url_for('main.index'))
    
    # GET request - show current ICU patients
    from Operations.patient import PatientListOperations
    icu_patients = []
    for bed in system.beds.beds:
        if bed.is_occupied:
            patient = PatientListOperations.search_by_id(system.patients, bed.assigned_patient_id)
            if patient:
                icu_patients.append(patient)
    
    return render_template('discharge_patient.html', icu_patients=icu_patients)


@main_bp.route('/patients/search', methods=['GET', 'POST'])
def search_patient():
    """Search for patient"""
    system = app_module.icu_system
    patient = None
    
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        
        from Operations.patient import PatientListOperations
        patient = PatientListOperations.search_by_id(system.patients, patient_id)
        
        if not patient:
            flash(f'Patient {patient_id} not found', 'error')
    
    return render_template('search_patient.html', patient=patient)


@main_bp.route('/doctors/add', methods=['GET', 'POST'])
def add_doctor():
    """Add new doctor"""
    system = app_module.icu_system
    
    if request.method == 'POST':
        # Get form data
        from flask import current_app
        doctor_id = get_next_doctor_id(current_app)
        
        name = request.form.get('name')
        experience = int(request.form.get('experience'))
        specialization = request.form.get('specialization')
        max_capacity = int(request.form.get('max_capacity', 5))
        
        # Create doctor
        from structure import Doctor
        doctor = Doctor(
            doctor_id=doctor_id,
            name=name,
            experience_years=experience,
            specialization=DoctorSpecialization(specialization),
            max_capacity=max_capacity
        )
        
        # Add to heap
        from Operations.doctor import DoctorHeapOperations
        DoctorHeapOperations.insert_doctor(system.doctors, doctor)
        
        # Save to database
        save_doctor_to_db(doctor)
        
        flash(f'Doctor {name} added successfully!', 'success')
        return redirect(url_for('main.doctor_workload'))
    
    # GET request - show form
    specializations = [spec.value for spec in DoctorSpecialization]
    return render_template('add_doctor.html', specializations=specializations)


@main_bp.route('/doctors/workload')
def doctor_workload():
    """View doctor workload"""
    system = app_module.icu_system
    
    from Operations.doctor import DoctorHeapOperations
    
    # Get all doctors sorted by priority
    doctors = sorted(
        system.doctors.heap,
        key=lambda d: DoctorHeapOperations.get_priority(d),
        reverse=True
    )
    
    # Calculate utilization for each
    doctor_data = []
    for doc in doctors:
        utilization = (doc.current_workload / doc.max_capacity) * 100 if doc.max_capacity > 0 else 0
        doctor_data.append({
            'doctor': doc,
            'utilization': utilization,
            'priority': DoctorHeapOperations.get_priority(doc)
        })
    
    return render_template('doctor_workload.html', doctors=doctor_data)


@main_bp.route('/beds/status')
def bed_status():
    """View bed status"""
    system = app_module.icu_system
    if not system:
        flash("System not initialized. Please initialize the system first.", "danger")
        return redirect(url_for('main.initialize'))

    from Operations.patient import PatientListOperations

    # Get bed information with patient details
    bed_data = []
    for bed in system.beds.beds:
        patient = None
        if bed.is_occupied:
            patient = PatientListOperations.search_by_id(system.patients, bed.assigned_patient_id)
        bed_data.append({
            'bed': bed,
            'patient': patient
        })

    return render_template('bed_status.html', beds=bed_data)


@main_bp.route('/queue/waiting')
def waiting_queue():
    """View waiting queue"""
    system = app_module.icu_system
    
    from Operations.patient import PatientListOperations
    
    # Get waiting queue with patient details
    queue_data = []
    position = 1
    for node in system.waiting_queue.queue:
        patient = PatientListOperations.search_by_id(system.patients, node.patient_id)
        if patient:
            wait_time = (datetime.now() - node.enqueue_time).total_seconds() / 60  # minutes
            queue_data.append({
                'position': position,
                'patient': patient,
                'wait_time': wait_time,
                'enqueue_time': node.enqueue_time
            })
            position += 1
    
    return render_template('waiting_queue.html', queue=queue_data)


@main_bp.route('/logs/allocations')
def allocation_log():
    """View allocation log"""
    system = app_module.icu_system
    
    # Get all allocations (reversed for newest first)
    allocations = list(system.allocation_log.records)
    allocations.reverse()
    
    return render_template('allocation_log.html', allocations=allocations)


@main_bp.route('/status')
def system_status():
    """View system status"""
    allocator = app_module.allocator
    
    status = allocator.get_system_status()
    
    return render_template('system_status.html', status=status)


@main_bp.route('/reports/export')
def export_reports():
    """Export reports as CSV"""
    system = app_module.icu_system
    
    # Create CSV in memory
    output = StringIO()
    
    writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    # Write allocation log
    writer.writerow(['Allocation Log Report'])
    writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
    writer.writerow([])
    writer.writerow(['Record ID', 'Patient ID', 'Bed ID', 'Doctor ID', 'Patient Severity', 
                     'Doctor Priority', 'Allocation Time', 'Reason'])
    
    for record in system.allocation_log.records:
        writer.writerow([
            record.record_id,
            record.patient_id,
            record.bed_id,
            record.doctor_id,
            record.patient_severity,
            record.doctor_priority_score,
            record.allocation_time.strftime('%Y-%m-%d %H:%M:%S'),
            record.decision_reason.value
        ])
    
    # Convert to bytes
    mem = BytesIO()
    mem.write(output.getvalue().encode('utf-8-sig')) # UTF-8 with BOM
    mem.seek(0)
    
    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'icu_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )


@main_bp.route('/initialize', methods=['GET', 'POST'])
def initialize():
    """Initialize or reinitialize system"""
    if request.method == 'POST':
        # Reinitialize system
        from flask import current_app
        app_module.initialize_system(current_app)
        flash('System reinitialized successfully!', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('initialize.html')
