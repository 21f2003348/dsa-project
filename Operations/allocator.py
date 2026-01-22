"""
Phase 3: ICU Allocation System - Core Logic

This module implements the high-level ICU management algorithms:
- Patient admission
- Bed + Doctor allocation
- Waiting queue management
- Patient discharge
- Resource tracking

Uses Phase 1 data structures and Phase 2 operations.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from Prototype.structure import (
    Patient, ICUManagementSystem, PatientStatus, 
    AllocationReason, Doctor, DoctorSpecialization
)
from Prototype.Operations.patient import PatientListOperations
from Prototype.Operations.bed import BedArrayOperations
from Prototype.Operations.doctor import DoctorHeapOperations
from Prototype.Operations.queue import WaitingQueueOperations
from Prototype.Operations.log import AllocationLogOperations
from Prototype.sync import (
    save_patient_to_db, save_bed_to_db, save_doctor_to_db, 
    save_allocation_to_db, save_to_waiting_queue_db, remove_from_waiting_queue_db
)
from typing import Optional, Tuple
from datetime import datetime


class ICUAllocator:
    """
    Core allocation logic for ICU Management System
    
    Responsibilities:
    - Admit patients to system
    - Allocate bed + doctor when available
    - Queue patients when ICU full
    - Process waiting queue on discharge
    - Track all decisions in allocation log
    """
    
    def __init__(self, system: ICUManagementSystem):
        """Initialize allocator with ICU system"""
        self.system = system
    
    # PATIENT ADMISSION   
    def admit_patient(
        self,
        patient_id: str,
        name: str,
        age: int,
        severity_level: int,
        medical_notes: str = "",
        needs_bed: bool = True,
        bed_type: str = "GENERAL"
    ) -> Tuple[bool, str]:
        """
        Admit new patient to ICU system
        
        Algorithm:
        1. Create patient record
        2. Add to patient linked list
        3. Save patient to DB
        4. If needs_bed is False: return success
        5. Check if bed available:
           - If yes: allocate immediately
           - If no: add to waiting queue
        
        Args:
            patient_id: Unique patient identifier
            name: Patient name
            age: Patient age
            severity_level: Urgency (1=Critical, 10=Stable)
            medical_notes: Clinical notes
            needs_bed: Whether patient requires ICU bed
        
        Returns:
            (success: bool, message: str)
        """
        # Create patient
        patient = Patient(patient_id, name, age, severity_level, medical_notes)
        
        # Add to patient list
        PatientListOperations.insert_at_tail(self.system.patients, patient)
        self.system.total_patients_admitted += 1
        
        # Save to DB
        save_patient_to_db(patient)
        
        print(f"✓ Patient {patient_id} admitted to system")
        
        # If bed not needed, assign doctor if available
        if not needs_bed:
            available_doctor = DoctorHeapOperations.find_best_available_doctor(self.system.doctors)
            if available_doctor is not None:
                # Assign doctor
                available_doctor.current_workload += 1
                available_doctor.assigned_patients.append(patient.patient_id)
                # Re-heapify doctor (workload changed)
                DoctorHeapOperations.update_doctor_workload(
                    self.system.doctors,
                    available_doctor.doctor_id,
                    available_doctor.current_workload
                )
                patient.status = PatientStatus.STABLE
                patient.assigned_doctor_id = available_doctor.doctor_id
                save_patient_to_db(patient)
                save_doctor_to_db(available_doctor)
                return (True, f"Patient {patient_id} registered and assigned to Dr. {available_doctor.name}")
            else:
                patient.status = PatientStatus.STABLE
                save_patient_to_db(patient)
                return (True, f"Patient {patient_id} registered (No bed required, no doctor available)")

        # Check available resources for requested bed type using BedArrayOperations
        free_bed_id = BedArrayOperations.find_free_bed(
            self.system.beds,
            bed_type.upper()
        )
        available_doctor = DoctorHeapOperations.find_best_available_doctor(self.system.doctors)

        # If both bed and doctor available, attempt allocation
        if free_bed_id is not None and available_doctor is not None:
            success, msg = self._allocate_to_icu(patient, bed_type)
            if success:
                return (True, f"Admitted and allocated: {msg}")
            # Allocation failed (e.g., race), fall through to queue
            print(f"⏳ Allocation failed: {msg}. Queuing patient {patient_id}.")

        # Queue patient when bed missing or doctor at capacity or allocation failed
        # Store requested bed type for later matching
        setattr(patient, 'requested_bed_type', bed_type)
        
        # Also store in medical notes for persistence across DB reloads
        if patient.medical_notes:
            # Remove old REQUESTED_BED_TYPE if exists
            lines = patient.medical_notes.split('\n')
            lines = [line for line in lines if not line.startswith('REQUESTED_BED_TYPE:')]
            patient.medical_notes = '\n'.join(lines)
        if not patient.medical_notes:
            patient.medical_notes = ""
        patient.medical_notes += f"\nREQUESTED_BED_TYPE:{bed_type}"
        
        WaitingQueueOperations.enqueue(
            self.system.waiting_queue,
            patient_id,
            severity_level
        )
        patient.status = PatientStatus.WAITING
        save_patient_to_db(patient)

        queue_size = WaitingQueueOperations.get_size(self.system.waiting_queue)

        # Save to Queue DB
        save_to_waiting_queue_db(patient_id, severity_level, queue_size)

        reason = "no beds" if free_bed_id is None else "no doctors available (at capacity)"
        print(f"⏳ {reason.title()}. Patient {patient_id} added to waiting queue (position {queue_size})")
        return (True, f"Admitted to waiting queue (position {queue_size})")
    
    # ICU ALLOCATION
    def _allocate_to_icu(self, patient: Patient, bed_type: str = "GENERAL") -> Tuple[bool, str]:
        """
        Allocate patient to ICU bed and doctor
        
        Uses Operations from Operations folder:
        - BedArrayOperations.find_free_bed() and allocate_bed()
        - DoctorHeapOperations.find_best_available_doctor()
        - AllocationLogOperations.append_record()
        """
        # Find free bed of requested type using BedArrayOperations
        free_bed_id = BedArrayOperations.find_free_bed(
            self.system.beds, 
            bed_type.upper()
        )
        
        # Find best available doctor using DoctorHeapOperations
        best_doctor = DoctorHeapOperations.find_best_available_doctor(self.system.doctors)

        if free_bed_id is None:
            return (False, f"No {bed_type} beds available")

        if best_doctor is None:
            return (False, "No doctors available (all at capacity)")

        # Allocate bed using BedArrayOperations
        success = BedArrayOperations.allocate_bed(
            self.system.beds, 
            free_bed_id, 
            patient.patient_id
        )
        
        if not success:
            return (False, "Failed to allocate bed")

        # Update doctor workload
        best_doctor.current_workload += 1
        best_doctor.assigned_patients.append(patient.patient_id)

        # Re-heapify doctor (workload changed, priority decreased)
        DoctorHeapOperations.update_doctor_workload(
            self.system.doctors,
            best_doctor.doctor_id,
            best_doctor.current_workload
        )

        # Update patient record
        patient.status = PatientStatus.IN_ICU
        patient.assigned_bed_id = free_bed_id
        patient.assigned_doctor_id = best_doctor.doctor_id
        patient.assignment_time = datetime.now()

        # Log allocation using AllocationLogOperations
        doctor_priority = DoctorHeapOperations.get_priority(best_doctor)
        record = AllocationLogOperations.append_record(
            self.system.allocation_log,
            patient.patient_id,
            free_bed_id,
            best_doctor.doctor_id,
            patient.severity_level,
            doctor_priority,
            AllocationReason.AUTOMATIC
        )
        
        print(f"✓ Allocated: Patient {patient.patient_id} → Bed {free_bed_id} ({bed_type}) + Dr.{best_doctor.name}")
        
        # PERSIST DATA TO DB - Call DB for every update
        save_bed_to_db(self.system.beds.beds[free_bed_id])
        save_doctor_to_db(best_doctor)
        save_patient_to_db(patient)
        save_allocation_to_db(record)
        
        return (True, f"Bed {free_bed_id} ({bed_type}) + {best_doctor.name}")
    
    # PATIENT DISCHARGE   
    def discharge_patient(self, patient_id: str) -> Tuple[bool, str]:
        """
        Discharge patient from ICU
        
        Algorithm:
        1. Find patient in list
        2. Verify patient is in ICU
        3. Release bed
        4. Update doctor workload
        5. Update patient status
        6. Process waiting queue (if anyone waiting)
        7. Return success
        
        Args:
            patient_id: Patient to discharge
        
        Returns:
            (success: bool, message: str)
        """
        # Find patient
        patient = PatientListOperations.search_by_id(
            self.system.patients, 
            patient_id
        )
        
        if patient is None:
            return (False, f"Patient {patient_id} not found")
        
        if patient.status != PatientStatus.IN_ICU:
            return (False, f"Patient {patient_id} is not in ICU (status: {patient.status.value})")
        
        # Get assigned resources
        bed_id = patient.assigned_bed_id
        doctor_id = patient.assigned_doctor_id
        
        # Get the type of bed being freed
        bed_type = None
        for bed in self.system.beds.beds:
            if bed.bed_id == bed_id:
                bed_type = bed.bed_type.value
                break
        # Release bed
        BedArrayOperations.release_bed(self.system.beds, bed_id)
        
        # Update doctor workload - decrease workload on discharge
        doctor_found = False
        doctor_to_save = None
        for doc in self.system.doctors.heap:
            if doc.doctor_id == doctor_id:
                # Decrease workload
                if doc.current_workload > 0:
                    doc.current_workload -= 1
                if patient_id in doc.assigned_patients:
                    doc.assigned_patients.remove(patient_id)

                # Re-heapify (workload decreased, priority increased)
                DoctorHeapOperations.update_doctor_workload(
                    self.system.doctors,
                    doctor_id,
                    doc.current_workload
                )

                doctor_found = True
                doctor_to_save = doc
                break
        
        if not doctor_found:
            print(f"⚠ Warning: Doctor {doctor_id} not found in heap")
        
        # Update patient status
        patient.status = PatientStatus.DISCHARGED
        patient.discharge_time = datetime.now()
        patient.assigned_bed_id = None
        patient.assigned_doctor_id = None
        
        # PERSIST DATA TO DB (Discharge updates) - Call DB for every update
        save_bed_to_db(self.system.beds.beds[bed_id])
        if doctor_found and doctor_to_save:
            save_doctor_to_db(doctor_to_save)
        save_patient_to_db(patient)
        
        print(f"✓ Patient {patient_id} discharged from Bed {bed_id}")

        # Process waiting queue - try to allocate to waiting patients
        # Queue is already sorted by severity (highest priority first)
        self._process_waiting_queue_after_discharge(bed_type)

        return (True, f"Discharged from Bed {bed_id}")
    
    # WAITING QUEUE PROCESSING    
    def _process_waiting_queue(self) -> None:
        """
        Internal: Allocate next waiting patient to ICU
        
        Algorithm:
        1. Dequeue next patient (sorted by severity)
        2. Find patient in list
        3. Allocate to ICU
        4. Log decision
        """
        if WaitingQueueOperations.is_empty(self.system.waiting_queue):
            return
        
        # Get next waiting patient (highest priority first due to severity sorting)
        next_patient_id = WaitingQueueOperations.dequeue(self.system.waiting_queue)
        
        # Remove from Queue DB
        if next_patient_id:
            remove_from_waiting_queue_db(next_patient_id)
        
        if next_patient_id is None:
            return
        
        # Find patient
        patient = PatientListOperations.search_by_id(
            self.system.patients,
            next_patient_id
        )
        
        if patient is None:
            print(f"⚠ Warning: Waiting patient {next_patient_id} not found in list")
            return
        
        # Get requested bed type if stored
        requested_bed_type = getattr(patient, 'requested_bed_type', 'GENERAL')
        
        # Allocate to ICU
        print(f"→ Processing waiting patient {next_patient_id}")
        success, msg = self._allocate_to_icu(patient, requested_bed_type)
        
        if not success:
            print(f"⚠ Failed to allocate waiting patient: {msg}")
            # Re-queue if allocation failed (will maintain severity order)
            WaitingQueueOperations.enqueue(
                self.system.waiting_queue,
                next_patient_id,
                patient.severity_level
            )
            # Re-add to DB
            queue_size = WaitingQueueOperations.get_size(self.system.waiting_queue)
            save_to_waiting_queue_db(next_patient_id, patient.severity_level, queue_size)
    
    def _process_waiting_queue_after_discharge(self, freed_bed_type: str) -> None:
        """
        Process waiting queue after a bed is freed
        
        Algorithm:
        1. Check waiting queue (sorted by severity)
        2. For each waiting patient, check if they need the freed bed type
        3. Try to allocate the first matching patient
        4. Stop after first successful allocation
        
        Args:
            freed_bed_type: Type of bed that was just freed
        """
        if WaitingQueueOperations.is_empty(self.system.waiting_queue):
            return
        
        # Get all waiting patients (already sorted by severity)
        waiting_ids = WaitingQueueOperations.get_all_waiting(self.system.waiting_queue)
        
        for next_patient_id in waiting_ids:
            # Find patient object
            next_patient = PatientListOperations.search_by_id(
                self.system.patients, 
                next_patient_id
            )
            
            if next_patient is None or next_patient.status != PatientStatus.WAITING:
                continue
            
            # Get requested bed type
            requested_bed_type = getattr(next_patient, 'requested_bed_type', 'GENERAL')
            
            # Check if this patient needs the freed bed type
            if requested_bed_type.upper() == freed_bed_type.upper():
                # Remove from queue
                # Find and remove the node from queue
                for idx, node in enumerate(self.system.waiting_queue.queue):
                    if node.patient_id == next_patient_id:
                        self.system.waiting_queue.queue.remove(node)
                        remove_from_waiting_queue_db(next_patient_id)
                        break
                
                # Try to allocate
                success, msg = self._allocate_to_icu(next_patient, freed_bed_type)
                if success:
                    print(f"✓ Allocated freed {freed_bed_type} bed to waiting patient {next_patient_id}")
                    return  # Successfully allocated, stop processing
                else:
                    # If allocation fails, re-queue (maintains severity order)
                    WaitingQueueOperations.enqueue(
                        self.system.waiting_queue,
                        next_patient_id,
                        next_patient.severity_level
                    )
                    queue_size = WaitingQueueOperations.get_size(self.system.waiting_queue)
                    save_to_waiting_queue_db(next_patient_id, next_patient.severity_level, queue_size)
                    print(f"⚠ Could not allocate {freed_bed_type} bed to {next_patient_id}: {msg}")
                    return  # Stop after first attempt
    
    # SYSTEM STATUS & REPORTING
    def get_system_status(self) -> dict:
        """
        Get current system status
        
        Returns:
            Dictionary with system metrics
        """
        free_beds = BedArrayOperations.count_free_beds(self.system.beds)
        total_beds = self.system.beds.num_beds
        occupied_beds = total_beds - free_beds
        
        # Calculate doctor metrics
        total_doctor_capacity = sum(d.max_capacity for d in self.system.doctors.heap)
        total_doctor_workload = sum(d.current_workload for d in self.system.doctors.heap)
        avg_doctor_workload = total_doctor_workload / len(self.system.doctors.heap) if self.system.doctors.heap else 0
        
        # Calculate occupancy rate
        occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
        
        return {
            # Patient metrics
            'total_patients': self.system.patients.size,
            'patients_in_icu': occupied_beds,
            'patients_waiting': WaitingQueueOperations.get_size(self.system.waiting_queue),
            'patients_discharged': self._count_discharged(),
            
            # Bed metrics (with aliases for compatibility)
            'beds_occupied': occupied_beds,
            'occupied_beds': occupied_beds,
            'beds_free': free_beds,
            'available_beds': free_beds,
            'beds_total': total_beds,
            'total_beds': total_beds,
            'occupancy_rate': occupancy_rate,
            
            # Doctor metrics
            'doctors_active': len(self.system.doctors.heap),
            'total_doctors': len(self.system.doctors.heap),
            'average_doctor_workload': avg_doctor_workload,
            'total_doctor_capacity': total_doctor_capacity,
            
            # Allocation metrics
            'total_allocations': AllocationLogOperations.get_total_count(self.system.allocation_log),
            'waiting_queue_size': WaitingQueueOperations.get_size(self.system.waiting_queue)
        }
    
    def _count_discharged(self) -> int:
        """Count discharged patients"""
        discharged = 0
        patients = PatientListOperations.traverse_all(self.system.patients)
        for p in patients:
            if p.status == PatientStatus.DISCHARGED:
                discharged += 1
        return discharged
    
    def print_system_status(self) -> None:
        """Print formatted system status"""
        status = self.get_system_status()
        print("\n" + "="*60)
        print("ICU MANAGEMENT SYSTEM STATUS")
        print("="*60)
        print(f"Patients:")
        print(f"  • Total Admitted: {status['total_patients']}")
        print(f"  • In ICU: {status['patients_in_icu']}")
        print(f"  • Waiting: {status['patients_waiting']}")
        print(f"  • Discharged: {status['patients_discharged']}")
        print(f"\nBeds:")
        print(f"  • Occupied: {status['beds_occupied']}/{status['beds_total']}")
        print(f"  • Free: {status['beds_free']}/{status['beds_total']}")
        print(f"\nDoctors:")
        print(f"  • Active: {status['doctors_active']}")
        print(f"\nAllocations:")
        print(f"  • Total Logged: {status['total_allocations']}")
        print("="*60 + "\n")
    
    def print_bed_status(self) -> None:
        """Print detailed bed status"""
        print("\nBed Status:")
        print("-" * 60)
        for bed in self.system.beds.beds:
            print(f"  {bed}")
        print("-" * 60 + "\n")
    
    def print_waiting_queue(self) -> None:
        """Print waiting queue"""
        waiting_patients = WaitingQueueOperations.get_all_waiting(self.system.waiting_queue)
        print("\nWaiting Queue:")
        print("-" * 60)
        if not waiting_patients:
            print("  (empty)")
        else:
            for idx, pid in enumerate(waiting_patients, 1):
                print(f"  {idx}. Patient {pid}")
        print("-" * 60 + "\n")


# HELPER FUNCTIONS FOR SYSTEM INITIALIZATION
def initialize_icu_system(num_beds: int = 10, doctors_config: list = None) -> ICUManagementSystem:
    """
    Initialize ICU Management System with beds and doctors
    
    Args:
        num_beds: Number of ICU beds
        doctors_config: List of (name, experience, specialization) tuples
    
    Returns:
        Initialized ICUManagementSystem
    """
    system = ICUManagementSystem(num_beds=num_beds)
    
    # Add doctors
    if doctors_config is None:
        doctors_config = [
            ("Dr. Smith", 15, DoctorSpecialization.CARDIAC),
            ("Dr. Johnson", 10, DoctorSpecialization.NEURO),
            ("Dr. Williams", 8, DoctorSpecialization.PULMONARY),
            ("Dr. Brown", 12, DoctorSpecialization.GENERAL),
            ("Dr. Davis", 6, DoctorSpecialization.GENERAL)
        ]
    
    for idx, (name, exp, spec) in enumerate(doctors_config, start=1):
        doctor = Doctor(idx, name, exp, spec, max_capacity=5)
        DoctorHeapOperations.insert_doctor(system.doctors, doctor)
        print(f"✓ Added {name} (Exp: {exp}y, {spec.value})")
    
    print(f"✓ ICU System initialized: {num_beds} beds, {len(doctors_config)} doctors\n")
    return system


# TEST & DEMO
if __name__ == "__main__":
    print("="*60)
    print("ICU ALLOCATION SYSTEM - Phase 3")
    print("="*60 + "\n")
    
    # Initialize system
    system = initialize_icu_system(num_beds=5)
    allocator = ICUAllocator(system)
    
    # Test scenario
    print("\n--- Admitting Patients ---\n")
    
    # Admit 3 patients (should get beds)
    allocator.admit_patient("P001", "Alice Johnson", 45, 2, "Cardiac arrest")
    allocator.admit_patient("P002", "Bob Smith", 60, 1, "Stroke - critical")
    allocator.admit_patient("P003", "Carol White", 35, 3, "Pneumonia")
    
    allocator.print_system_status()
    allocator.print_bed_status()
    
    # Admit 3 more (should overflow to queue)
    print("\n--- Admitting More Patients ---\n")
    allocator.admit_patient("P004", "David Brown", 50, 2, "Respiratory failure")
    allocator.admit_patient("P005", "Emma Davis", 28, 4, "Post-surgery monitoring")
    allocator.admit_patient("P006", "Frank Miller", 55, 1, "Critical condition")
    
    allocator.print_system_status()
    allocator.print_waiting_queue()
    
    # Discharge one patient
    print("\n--- Discharging Patient ---\n")
    allocator.discharge_patient("P001")
    
    allocator.print_system_status()
    allocator.print_bed_status()
    allocator.print_waiting_queue()
    
    # Discharge another
    print("\n--- Discharging Another Patient ---\n")
    allocator.discharge_patient("P002")
    
    allocator.print_system_status()
    allocator.print_waiting_queue()