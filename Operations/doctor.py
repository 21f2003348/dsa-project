import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from Prototype.structure import Doctor, DoctorMaxHeap, DoctorSpecialization
from typing import Optional


class DoctorHeapOperations:
    """
    Priority Formula: experience_years - current_workload
    
    Time Complexity Goals:
    - insert: O(log n)
    - extract_max: O(log n)
    - update: O(log n)
    """
    
    @staticmethod
    def get_priority(doctor: Doctor) -> int:
        return doctor.experience_years - doctor.current_workload
    
    @staticmethod
    def insert_doctor(doctor_heap: DoctorMaxHeap, doctor: Doctor) -> None:
        """
        Algorithm:
        1. Append doctor to end of heap list
        2. Update doctor_map: doctor_id -> index
        3. Heapify up from last position
        
        Time: O(log n)
        Space: O(1)
        
        Hint: Use heapify_up() helper
        """
        doctor_heap.heap.append(doctor)
        doctor_heap.doctor_map[doctor.doctor_id] = len(doctor_heap.heap) - 1
        DoctorHeapOperations.heapify_up(doctor_heap, len(doctor_heap.heap) - 1)
    
    @staticmethod
    def heapify_up(doctor_heap: DoctorMaxHeap, index: int) -> None:
        """
        Algorithm:
        1. While index > 0:
           - Calculate parent_index = (index - 1) // 2
           - Get priorities of current and parent
           - If current > parent (max heap property violated):
               * Swap current with parent
               * Update doctor_map for both
               * Move index to parent_index
           - Else break (heap property satisfied)
        
        Time: O(log n)
        Space: O(1)
        """
        while index > 0:
            parent_index = (index - 1) // 2
            current_priority = DoctorHeapOperations.get_priority(doctor_heap.heap[index])
            parent_priority = DoctorHeapOperations.get_priority(doctor_heap.heap[parent_index])
            
            if current_priority > parent_priority:
                # Swap
                doctor_heap.heap[index], doctor_heap.heap[parent_index] = (
                    doctor_heap.heap[parent_index],
                    doctor_heap.heap[index]
                )
                # Update map
                doctor_heap.doctor_map[doctor_heap.heap[index].doctor_id] = index
                doctor_heap.doctor_map[doctor_heap.heap[parent_index].doctor_id] = parent_index
                
                index = parent_index
            else:
                break
    
    @staticmethod
    def extract_max(doctor_heap: DoctorMaxHeap) -> Optional[Doctor]:
        """
        Algorithm:
        1. If heap empty, return None
        2. Store root (best doctor) to return
        3. Move last element to root
        4. Remove last element
        5. Update doctor_map
        6. Heapify down from root
        7. Return stored doctor
        
        Time: O(log n)
        Space: O(1)
        
        Hint: Use heapify_down() helper
        """
        if not doctor_heap.heap:
            return None
        
        max_doctor = doctor_heap.heap[0]
        last_doctor = doctor_heap.heap.pop()
        
        if doctor_heap.heap:
            doctor_heap.heap[0] = last_doctor
            doctor_heap.doctor_map[last_doctor.doctor_id] = 0
            DoctorHeapOperations.heapify_down(doctor_heap, 0)
        
        del doctor_heap.doctor_map[max_doctor.doctor_id]
        return max_doctor
    
    @staticmethod
    def heapify_down(doctor_heap: DoctorMaxHeap, index: int) -> None:
        """
        Algorithm:
        1. While has at least left child:
           - Calculate left_child = 2*index + 1
           - Calculate right_child = 2*index + 2
           - Find largest among current, left, right (by priority)
           - If largest is current, break (heap property satisfied)
           - Else:
               * Swap current with largest child
               * Update doctor_map
               * Move index to largest child position
        
        Time: O(log n)
        Space: O(1)
        """
        while 2 * index + 1 < len(doctor_heap.heap):
            left_child = 2 * index + 1
            right_child = 2 * index + 2
            largest = index

            if (left_child < len(doctor_heap.heap) and
                DoctorHeapOperations.get_priority(doctor_heap.heap[left_child]) >
                DoctorHeapOperations.get_priority(doctor_heap.heap[largest])):
                largest = left_child

            if (right_child < len(doctor_heap.heap) and
                DoctorHeapOperations.get_priority(doctor_heap.heap[right_child]) >
                DoctorHeapOperations.get_priority(doctor_heap.heap[largest])):
                largest = right_child

            if largest == index:
                break
            # Swap
            doctor_heap.heap[index], doctor_heap.heap[largest] = (
                doctor_heap.heap[largest],
                doctor_heap.heap[index]
            )
            # Update map
            doctor_heap.doctor_map[doctor_heap.heap[index].doctor_id] = index
            doctor_heap.doctor_map[doctor_heap.heap[largest].doctor_id] = largest
            index = largest
        

    
    @staticmethod
    def peek_max(doctor_heap: DoctorMaxHeap) -> Optional[Doctor]:
        """
        Algorithm:
        1. If heap empty, return None
        2. Return heap[0] (don't remove)
        
        Time: O(1)
        Space: O(1)
        """
        if not doctor_heap.heap:
            return None
        return doctor_heap.heap[0]
    
    @staticmethod
    def update_doctor_workload(heap: DoctorMaxHeap, doctor_id: int, new_workload: int) -> bool:
        """
        Update doctor's workload and reheapify
        
        Algorithm:
        1. Find doctor in heap using doctor_map
        2. Update workload
        3. Heapify (up or down depending on priority change)
        4. Return success status
        
        Time: O(log n)
        Space: O(1)
        """
        if doctor_id not in heap.doctor_map:
            return False
        
        index = heap.doctor_map[doctor_id]
        doctor = heap.heap[index]
        old_priority = DoctorHeapOperations.get_priority(doctor)
        
        doctor.current_workload = new_workload
        new_priority = DoctorHeapOperations.get_priority(doctor)
        
        if new_priority > old_priority:
            DoctorHeapOperations.heapify_up(heap, index)
        else:
            DoctorHeapOperations.heapify_down(heap, index)
        
        return True


if __name__ == "__main__":
    # Test doctor heap operations
    print("=== Testing Doctor Heap Operations ===\n")
    
    # Create doctor heap
    heap = DoctorMaxHeap()
    print(f"Created doctor heap: {heap}\n")
    
    # Example:
    # from Prototype.structure import DoctorSpecialization
    doc1 = Doctor(1, "Dr. Smith", 15, DoctorSpecialization.CARDIAC, 5)
    DoctorHeapOperations.insert_doctor(heap, doc1)
