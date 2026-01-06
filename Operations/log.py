import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from Prototype.structure import AllocationRecord, AllocationLogList, AllocationReason, Doctor
from typing import List
from datetime import datetime


class AllocationLogOperations:
    """
    Operations for AllocationLogList
    
    Implements:
    - append_record() : Add new allocation record
    - query_by_patient() : Find all allocations for a patient
    - query_by_date_range() : Get allocations in time period
    - export_to_file() : Save log to file
    - get_total_count() : Get number of allocations
    
    Time Complexity:
    - append: O(1)
    - query: O(n) - acceptable for audit operations
    """
    
    @staticmethod
    def append_record(
        log: AllocationLogList,
        patient_id: str,
        bed_id: int,
        doctor_id: int,
        patient_severity: int,
        doctor_priority_score: int,
        reason: AllocationReason = AllocationReason.AUTOMATIC
    ) -> AllocationRecord:
        """
        Algorithm:
        1. Get next record_id from log.next_record_id
        2. Create AllocationRecord with all parameters
        3. Append record to log.records list
        4. Increment log.next_record_id
        5. Return created record
        
        Time: O(1) amortized
        Space: O(1)
        """
        new_record = AllocationRecord(
            record_id = log.next_record_id,
            patient_id = patient_id,
            bed_id = bed_id,
            doctor_id = doctor_id,
            patient_severity = patient_severity,
            doctor_priority_score = doctor_priority_score,
            decision_reason = reason
        )
        log.records.append(new_record)
        log.next_record_id += 1

        return new_record
    
    @staticmethod
    def query_by_patient(log: AllocationLogList, patient_id: str) -> List[AllocationRecord]:
        """
        Algorithm:
        1. Create empty result list
        2. Loop through all records in log.records
        3. If record.patient_id matches, add to result
        4. Return result list
        
        Time: O(n)
        Space: O(k) where k = number of matching records
        """
        result = []

        for record in log.records:
            if record.patient_id == patient_id:
                result.append(record)

        return result
    
    @staticmethod
    def query_by_date_range(
        log: AllocationLogList,
        start_date: datetime,
        end_date: datetime
    ) -> List[AllocationRecord]:
        """
        Get all allocations within date range
        
        Algorithm:
        1. Create empty result list
        2. Loop through all records
        3. If allocation_time between start_date and end_date, add to result
        4. Return result list
        
        Time: O(n)
        Space: O(k) where k = number of matching records
        """
        result = []

        for record in log.records:
            if start_date <= record.allocation_time <= end_date:
                result.append(record)
            
        return result
    
    @staticmethod
    def get_all_records(log: AllocationLogList) -> List[AllocationRecord]:
        return log.records.copy()
    
    @staticmethod
    def get_total_count(log: AllocationLogList) -> int:
        return len(log.records)
    
    @staticmethod
    def export_to_file(log: AllocationLogList, filename: str) -> bool:
        """
        Export allocation log to text file
        
        Algorithm:
        1. Open file for writing
        2. Write header
        3. Loop through all records
        4. Write each record in formatted way
        5. Close file
        6. Return success status
        
        Time: O(n)
        Space: O(1)
        """
        try:
            with open(filename, 'w') as file:
                file.write("Allocation Log\n")
                file.write("===============\n\n")
                for record in log.records:
                    file.write(f"{record}\n")
            return True
        except Exception as e:
            print(f"Error exporting log to file: {e}")
            return False


if __name__ == "__main__":
    # Test log operations
    print("=== Testing Allocation Log Operations ===\n")
    
    # Create allocation log
    log = AllocationLogList()
    print(f"Created allocation log: {log}\n")
    
    # Example:
    record = AllocationLogOperations.append_record(
        log, "P001", 3, 7, 2, 12, AllocationReason.AUTOMATIC
    )
    print(f"Appended record: {record}")

    AllocationLogOperations.export_to_file(log, "allocation_log.txt")
