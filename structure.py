from datetime import datetime
from typing import Optional, List
from enum import Enum

# Users
class PatientStatus(Enum):
    WAITING = "WAITING"           # Awaiting bed
    IN_ICU = "IN_ICU"             # Currently in ICU bed
    DISCHARGED = "DISCHARGED"     # Left ICU


class DoctorSpecialization(Enum):
    GENERAL = "GENERAL"
    CARDIAC = "CARDIAC"
    NEURO = "NEURO"
    PULMONARY = "PULMONARY"


class BedType(Enum):
    GENERAL = "GENERAL"
    VENTILATOR = "VENTILATOR"
    ISOLATION = "ISOLATION"

class AllocationReason(Enum):
    """Why allocation was made"""
    AUTOMATIC = "AUTOMATIC"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
    EMERGENCY = "EMERGENCY"


# Patient Record
class Patient:
    def __init__(
        self,
        patient_id: str,
        name: str,
        age: int,
        severity_level: int,
        medical_notes: str = ""
    ):
        # Identity & Demographics
        self.patient_id: str = patient_id
        self.name: str = name
        self.age: int = age
        
        # Medical Classification
        self.severity_level: int = severity_level  # Range: 1-5
        self.medical_notes: str = medical_notes
        
        # Lifecycle Management
        self.arrival_time: datetime = datetime.now()
        self.status: PatientStatus = PatientStatus.WAITING
        
        # Resource Assignment
        self.assigned_bed_id: Optional[int] = None
        self.assigned_doctor_id: Optional[int] = None
        
        # Audit Trail
        self.assignment_time: Optional[datetime] = None
        self.discharge_time: Optional[datetime] = None
    
    def __repr__(self) -> str:
        return (
            f"Patient(ID={self.patient_id}, Name={self.name}, Age={self.age}, "
            f"Severity={self.severity_level}, Status={self.status.value}, "
            f"Bed={self.assigned_bed_id}, Doctor={self.assigned_doctor_id})"
        )
    
    def __str__(self) -> str:
        return f"[{self.patient_id}] {self.name} ({self.age}y) - Severity: {self.severity_level}"


# ICU Bed Record
class ICUBed:    
    def __init__(self, bed_id: int, bed_type: BedType = BedType.GENERAL):
        # Identity
        self.bed_id: int = bed_id
        self.bed_type: BedType = bed_type
        
        # Status
        self.is_occupied: bool = False
        self.assigned_patient_id: Optional[str] = None
        
        # Audit
        self.last_occupied_time: Optional[datetime] = None
        self.last_freed_time: Optional[datetime] = None
    
    def __repr__(self) -> str:
        status = "OCCUPIED" if self.is_occupied else "FREE"
        patient_info = f" (Patient: {self.assigned_patient_id})" if self.is_occupied else ""
        return f"Bed#{self.bed_id} [{status}]{patient_info}"
    
    def __str__(self) -> str:
        if self.is_occupied:
            return f"Bed {self.bed_id}: OCCUPIED by {self.assigned_patient_id}"
        else:
            return f"Bed {self.bed_id}: FREE"

# Doctor Record
class Doctor:    
    def __init__(
        self,
        doctor_id: int,
        name: str,
        experience_years: int,
        specialization: DoctorSpecialization = DoctorSpecialization.GENERAL,
        max_capacity: int = 5
    ):
        # Identity & Profile
        self.doctor_id: int = doctor_id
        self.name: str = name
        self.experience_years: int = experience_years
        self.specialization: DoctorSpecialization = specialization
        
        # Capacity Management
        self.max_capacity: int = max_capacity # At a particular time in the day He can only handle x patients
        self.current_workload: int = 0  # Current No of patients assigned 
        self.is_available: bool = True  # On-duty status
        
        # Patient Assignment
        self.assigned_patients: List[str] = []  # Patient IDs
    
    def get_priority_score(self) -> int:
        # return self.experience_years - self.current_workload
        pass
    
    def __repr__(self) -> str:
        return (
            f"Doctor(ID={self.doctor_id}, Name={self.name}, "
            f"Experience={self.experience_years}y, Workload={self.current_workload}/{self.max_capacity}, "
            f"Available={self.is_available})"
        )
    
    def __str__(self) -> str:
        availability = "Available" if self.is_available else "Unavailable"
        return (
            f"Dr. {self.name} ({self.specialization.value}) - "
            f"Exp: {self.experience_years}y, Load: {self.current_workload}/{self.max_capacity} [{availability}]"
        )

# doctor = Doctor(1, "Alice Smith", 10, DoctorSpecialization.CARDIAC)
# print(doctor)

# Waiting Queue Node
class WaitingQueueNode:    
    def __init__(self, patient_id: str, priority_snapshot: int):
        # Link to patient
        self.patient_id: str = patient_id
        
        # Queue metadata
        self.enqueue_time: datetime = datetime.now()
        self.priority_snapshot: int = priority_snapshot
        
        # Linked list pointers (if implementing with linked list)
        self.next_node: Optional['WaitingQueueNode'] = None
    
    def __repr__(self) -> str:
        return f"WaitingNode(PatientID={self.patient_id}, Priority={self.priority_snapshot})"
    
    def __str__(self) -> str:
        return f"Waiting: Patient {self.patient_id} (Severity {self.priority_snapshot})"

# Allocation Record (Immutable)
class AllocationRecord:
    def __init__(
        self,
        record_id: int,
        patient_id: str,
        bed_id: int,
        doctor_id: int,
        patient_severity: int,
        doctor_priority_score: int,
        decision_reason: AllocationReason = AllocationReason.AUTOMATIC
    ):
        # Record Identity
        self.record_id: int = record_id
        
        # References
        self.patient_id: str = patient_id
        self.bed_id: int = bed_id
        self.doctor_id: int = doctor_id
        
        # Snapshots (for audit)
        self.patient_severity: int = patient_severity
        self.doctor_priority_score: int = doctor_priority_score
        
        # Metadata
        self.allocation_time: datetime = datetime.now()
        self.decision_reason: AllocationReason = decision_reason
    
    def __repr__(self) -> str:
        return (
            f"AllocationRecord(ID={self.record_id}, "
            f"Patient={self.patient_id}, Bed={self.bed_id}, Doctor={self.doctor_id})"
        )
    
    def __str__(self) -> str:
        return (
            f"[{self.record_id}] Patient {self.patient_id} → "
            f"Bed {self.bed_id} with Dr#{self.doctor_id} [{self.decision_reason.value}]"
        )

# DATA STRUCTURE WRAPPERS

# Linked list node for patients
class PatientLinkedListNode:
    """
    Node for linked list implementation
    Wraps Patient data container with next pointer
    """
    def __init__(self, patient: Patient):
        self.patient = patient
        self.next: Optional['PatientLinkedListNode'] = None


class PatientLinkedList:
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0
    
    def __repr__(self) -> str:
        return f"PatientLinkedList(size={self.size})"
    
    def __str__(self) -> str:
        return f"Patient List: {self.size} patients"


class ICUBedArray:
    def __init__(self, num_beds: int = 10):
        self.beds: List[ICUBed] = [
            ICUBed(bed_id=i) for i in range(num_beds)
        ]
        self.num_beds = num_beds
    
    def __repr__(self) -> str:
        return f"ICUBedArray(capacity={self.num_beds})"
    
    def __str__(self) -> str:
        return f"ICU Bed Array: {self.num_beds} beds"


class DoctorMaxHeap:
    def __init__(self):
        self.heap: List[Doctor] = []
        self.doctor_map: dict = {}  # doctor_id -> index (for O(1) updates)
    
    def __repr__(self) -> str:
        return f"DoctorMaxHeap(size={len(self.heap)})"
    
    def __str__(self) -> str:
        return f"Doctor Heap: {len(self.heap)} doctors"


class WaitingQueueFIFO:
    def __init__(self):
        """Initialize empty FIFO queue"""
        from collections import deque
        self.queue: deque[WaitingQueueNode] = deque()
    
    def __repr__(self) -> str:
        return f"WaitingQueueFIFO(size={len(self.queue)})"
    
    def __str__(self) -> str:
        return f"Waiting Queue: {len(self.queue)} patients waiting"


class AllocationLogList:

    def __init__(self):
        self.records: List[AllocationRecord] = []
        self.next_record_id = 1
    
    def __repr__(self) -> str:
        return f"AllocationLogList(records={len(self.records)})"
    
    def __str__(self) -> str:
        return f"Allocation Log: {len(self.records)} allocations recorded"

# SYSTEM CONTAINER
class ICUManagementSystem:
    def __init__(self, num_beds: int = 10, num_doctors: int = 5):
        # Core Data Structures
        self.patients = PatientLinkedList()
        self.beds = ICUBedArray(num_beds)
        self.doctors = DoctorMaxHeap()
        self.waiting_queue = WaitingQueueFIFO()
        self.allocation_log = AllocationLogList()
        
        # System Metadata
        self.total_patients_admitted = 0
    
    def __repr__(self) -> str:
        return (
            f"ICUManagementSystem("
            f"Patients={self.patients.size}, "
            f"Beds={self.beds.num_beds}, "
            f"Doctors={len(self.doctors.heap)}, "
            f"Waiting={len(self.waiting_queue.queue)})"
        )
    
    def __str__(self) -> str:
        return (
            f"ICU Management System\n"
            f"  Patients: {self.patients.size}\n"
            f"  Beds: {self.beds.num_beds}\n"
            f"  Doctors: {len(self.doctors.heap)}\n"
            f"  Waiting: {len(self.waiting_queue.queue)}\n"
            f"  Total Allocations: {len(self.allocation_log.records)}"
        )