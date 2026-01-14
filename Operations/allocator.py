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
        medical_notes: str = ""
    ) -> Tuple[bool, str]:
        """
        Admit new patient to ICU system
        
        Algorithm:
        1. Create patient record
        2. Add to patient linked list
        3. Check if bed available:
           - If yes: allocate immediately
           - If no: add to waiting queue
        4. Return success status and message
        
        Args:
            patient_id: Unique patient identifier
            name: Patient name
            age: Patient age
            severity_level: Urgency (1=Critical, 5=Stable)
            medical_notes: Clinical notes
        
        Returns:
            (success: bool, message: str)
        """
        # Create patient
        patient = Patient(patient_id, name, age, severity_level, medical_notes)
        
        # Add to patient list
        PatientListOperations.insert_at_tail(self.system.patients, patient)
        self.system.total_patients_admitted += 1
        
        print(f"✓ Patient {patient_id} admitted to system")
        
        # Try immediate allocation
        free_bed_id = BedArrayOperations.find_free_bed(self.system.beds)
        
        if free_bed_id is not None:
            # Bed available - allocate immediately
            success, msg = self._allocate_to_icu(patient)
            return (True, f"Admitted and allocated: {msg}")
        else:
            # No bed - add to waiting queue
            WaitingQueueOperations.enqueue(
                self.system.waiting_queue, 
                patient_id, 
                severity_level
            )
            patient.status = PatientStatus.WAITING
            queue_size = WaitingQueueOperations.get_size(self.system.waiting_queue)
            print(f"⏳ No beds available. Patient {patient_id} added to waiting queue (position {queue_size})")
            return (True, f"Admitted to waiting queue (position {queue_size})")
    
    # ICU ALLOCATION
    def _allocate_to_icu(self, patient: Patient) -> Tuple[bool, str]:
        """
        Internal: Allocate bed and doctor to patient
        
        Algorithm:
        1. Find free bed
        2. Find best available doctor (from heap)
        3. Allocate bed
        4. Update doctor workload
        5. Update patient record
        6. Log allocation
        7. Return success
        
        Args:
            patient: Patient object to allocate
        
        Returns:
            (success: bool, message: str)
        """
        # Find resources
        free_bed_id = BedArrayOperations.find_free_bed(self.system.beds)
        best_doctor = DoctorHeapOperations.peek_max(self.system.doctors)
        
        if free_bed_id is None:
            return (False, "No beds available")
        
        if best_doctor is None:
            return (False, "No doctors available")
        
        # Allocate bed
        BedArrayOperations.allocate_bed(
            self.system.beds, 
            free_bed_id, 
            patient.patient_id
        )
        
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
        
        # Log allocation
        doctor_priority = DoctorHeapOperations.get_priority(best_doctor)
        AllocationLogOperations.append_record(
            self.system.allocation_log,
            patient.patient_id,
            free_bed_id,
            best_doctor.doctor_id,
            patient.severity_level,
            doctor_priority,
            AllocationReason.AUTOMATIC
        )
        
        print(f"✓ Allocated: Patient {patient.patient_id} → Bed {free_bed_id} + Dr.{best_doctor.name}")
        
        return (True, f"Bed {free_bed_id} + {best_doctor.name}")
    
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
        
        # Release bed
        BedArrayOperations.release_bed(self.system.beds, bed_id)
        
        # Update doctor workload
        doctor_found = False
        for doc in self.system.doctors.heap:
            if doc.doctor_id == doctor_id:
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
                break
        
        if not doctor_found:
            print(f"⚠ Warning: Doctor {doctor_id} not found in heap")
        
        # Update patient status
        patient.status = PatientStatus.DISCHARGED
        patient.discharge_time = datetime.now()
        patient.assigned_bed_id = None
        patient.assigned_doctor_id = None
        
        print(f"✓ Patient {patient_id} discharged from Bed {bed_id}")
        
        # Process waiting queue
        waiting_size = WaitingQueueOperations.get_size(self.system.waiting_queue)
        if waiting_size > 0:
            self._process_waiting_queue()
        
        return (True, f"Discharged from Bed {bed_id}")
    
    # WAITING QUEUE PROCESSING    
    def _process_waiting_queue(self) -> None:
        """
        Internal: Allocate next waiting patient to ICU
        
        Algorithm:
        1. Dequeue next patient (FIFO)
        2. Find patient in list
        3. Allocate to ICU
        4. Log decision
        """
        if WaitingQueueOperations.is_empty(self.system.waiting_queue):
            return
        
        # Get next waiting patient
        next_patient_id = WaitingQueueOperations.dequeue(self.system.waiting_queue)
        
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
        
        # Allocate to ICU
        print(f"→ Processing waiting patient {next_patient_id}")
        success, msg = self._allocate_to_icu(patient)
        
        if not success:
            print(f"⚠ Failed to allocate waiting patient: {msg}")
            # Re-queue if allocation failed
            WaitingQueueOperations.enqueue(
                self.system.waiting_queue,
                next_patient_id,
                patient.severity_level
            )
    
    # SYSTEM STATUS & REPORTING
    def get_system_status(self) -> dict:
        """
        Get current system status
        
        Returns:
            Dictionary with system metrics
        """
        free_beds = BedArrayOperations.count_free_beds(self.system.beds)
        total_beds = self.system.beds.num_beds
        
        return {
            'total_patients': self.system.patients.size,
            'patients_in_icu': sum(1 for b in self.system.beds.beds if b.is_occupied),
            'patients_waiting': WaitingQueueOperations.get_size(self.system.waiting_queue),
            'patients_discharged': self._count_discharged(),
            'beds_occupied': total_beds - free_beds,
            'beds_free': free_beds,
            'beds_total': total_beds,
            'doctors_active': len(self.system.doctors.heap),
            'total_allocations': AllocationLogOperations.get_total_count(self.system.allocation_log)
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