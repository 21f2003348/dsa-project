import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from Prototype.structure import ICUBed, ICUBedArray
from typing import Optional
from datetime import datetime


class BedArrayOperations:
    """
    Operations for ICUBedArray
    
    Implements:
    - find_free_bed() : Get first available bed
    - allocate_bed() : Mark bed as occupied
    - release_bed() : Mark bed as free
    - count_free_beds() : Get availability count
    - get_bed_status() : Get all bed states
    
    Time Complexity Goals:
    - find_free_bed: O(n) where n is small (~10-30)
    - allocate/release: O(1)
    - count_free: O(n)
    """
    
    @staticmethod
    def find_free_bed(bed_array: ICUBedArray) -> Optional[int]:
        """
        Algorithm:
        1. Loop through all beds (0 to num_beds-1)
        2. For each bed:
           - Check if is_occupied == False
           - If free, return bed_id
        3. If no free bed found, return None
        
        Time: O(n) - acceptable for n <= 30
        Space: O(1)
        """
        
        if bed_array.num_beds == 0:
            return None

        for bed in bed_array.beds:
            if not bed.is_occupied:
                return bed.bed_id
        
        return None
    
    @staticmethod
    def allocate_bed(bed_array: ICUBedArray, bed_id: int, patient_id: str) -> bool:
        """
        Algorithm:
        1. Validate: bed_id in range [0, num_beds-1]
        2. Get bed object from array
        3. Check if already occupied (should not happen, but safety check)
        4. Mark bed as occupied
        5. Set assigned_patient_id
        6. Update last_occupied_time
        7. Return True if successful
        
        Time: O(1)
        Space: O(1)
        """
        if bed_id < 0 or bed_id >= bed_array.num_beds:
            return False

        bed = bed_array.beds[bed_id]
        if bed.is_occupied:
            return False  # Bed already occupied
        
        bed.is_occupied = True
        bed.assigned_patient_id = patient_id
        bed.last_occupied_time = datetime.now()
        return True
        
    @staticmethod
    def release_bed(bed_array: ICUBedArray, bed_id: int) -> bool:
        """
        Algorithm:
        1. Validate: bed_id in range
        2. Get bed object
        3. Mark is_occupied = False
        4. Set assigned_patient_id = None
        5. Update last_freed_time
        6. Return True if successful
        
        Time: O(1)
        Space: O(1)
        """
        if bed_id < 0 or bed_id >= bed_array.num_beds:
            return False
    
        bed = bed_array.beds[bed_id]
        bed.is_occupied = False
        bed.assigned_patient_id = None
        bed.last_freed_time = datetime.now()
        return True
    
    @staticmethod
    def count_free_beds(bed_array: ICUBedArray) -> int:
        """
        Algorithm:
        1. Initialize counter = 0
        2. Loop through all beds
        3. If bed.is_occupied == False, increment counter
        4. Return counter
        
        Time: O(n)
        Space: O(1)
        """
        count = 0

        for bed in bed_array.beds:
            if bed.is_occupied == False:
                count += 1
        
        return count
    
    @staticmethod
    def get_all_beds_status(bed_array: ICUBedArray) -> list:
        """
        Get status of all beds
        
        Time: O(n)
        Space: O(n)
        """
        status_list = []

        for bed in bed_array.beds:
            status_list.append({
                "Bed no.": bed.bed_id,
                "Occupied": bed.is_occupied,            
            })
        
        return status_list


if __name__ == "__main__":
    # Test bed operations
    print("=== Testing Bed Array Operations ===\n")
    
    # Create bed array with 5 beds
    bed_array = ICUBedArray(num_beds=5)
    print(f"Created bed array: {bed_array}\n")
    
    # Example:

    free_bed = BedArrayOperations.find_free_bed(bed_array)
    print(f"First free bed: {free_bed}")

    BedArrayOperations.allocate_bed(bed_array, free_bed, "P001")
    print(f"Allocated bed {free_bed} to patient P001\n")

    free_bed = BedArrayOperations.find_free_bed(bed_array)
    print(f"Next free bed: {free_bed}")

    success = BedArrayOperations.allocate_bed(bed_array, free_bed, "P001")
    print(f"Allocated bed {free_bed} to patient P001: {success}\n")

    BedArrayOperations.release_bed(bed_array, free_bed)
    print(f"Released bed {free_bed}\n")

    bed_status = BedArrayOperations.get_all_beds_status(bed_array)
    print(f"All bed statuses: {bed_status}\n")

    free_bed_count = BedArrayOperations.count_free_beds(bed_array)
    print(f"Free bed count: {free_bed_count}\n")

