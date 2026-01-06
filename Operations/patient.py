import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from Prototype.structure import Patient, PatientLinkedList, PatientStatus, PatientLinkedListNode
from typing import Optional, List

class PatientListOperations:
    """
    Implements:
    - insert() : Add new patient
    - delete() : Remove patient (discharge)
    - search() : Find patient by ID
    - traverse() : Visit all patients
    - count() : Get total patients
    """
    
    @staticmethod
    def insert_at_tail(patient_list: PatientLinkedList, patient: Patient) -> None:
        """
        Algorithm:
        1. Create new node with patient data
        2. If list empty:
           - Set head and tail to new node
        3. Else:
           - Link current tail.next to new node
           - Update tail to new node
        4. Increment size

        Time: O(1)
        Space: O(1)
        """
        new_patient = PatientLinkedListNode(patient)
        
        if not patient_list.head:
            patient_list.head = new_patient
            patient_list.tail = new_patient
        else:
            patient_list.tail.next = new_patient
            patient_list.tail = new_patient
        
        patient_list.size += 1
        
    @staticmethod
    def insert_at_head(patient_list: PatientLinkedList, patient: Patient) -> None:
        """
        Algorithm:
        1. Create new node with patient data
        2. If list empty:
           - Set head and tail to new node
        3. Else:
           - Link new node.next to current head
           - Update head to new node
        4. Increment size
        
        Time: O(1)
        Space: O(1)
        """
        new_patient = PatientLinkedListNode(patient)

        if not patient_list.head:
            patient_list.head = new_patient
            patient_list.tail = new_patient
        else:
            new_patient.next = patient_list.head
            patient_list.head = new_patient
        
        patient_list.size += 1
    
    @staticmethod
    def search_by_id(linked_list: PatientLinkedList, patient_id: str) -> Optional[Patient]:
        """
        Algorithm:
        1. Start from head
        2. Traverse each node:
           - If patient_id matches, return patient
           - Move to next node
        3. If not found, return None

        Time: O(n)
        Space: O(1)
        """
        if linked_list.head is None:
            return None

        curr = linked_list.head
        while curr:
            if curr.patient.patient_id == patient_id:
                print(f"Patient {patient_id} found.")
                return curr.patient
            curr = curr.next
        
        return None
    
    @staticmethod
    def delete_by_id(linked_list: PatientLinkedList, patient_id: str) -> bool:
        """
        Algorithm:
        1. Handle edge case: empty list
        2. Handle special case: deleting head
        3. General case: 
           - Traverse with two pointers (prev, current)
           - When found, link prev.next to current.next
           - Update tail if deleting last node
        4. Decrement size
        5. Return True if deleted, False if not found

        Time: O(n)
        Space: O(1)
        """
        if linked_list.head == None:
            return False

        curr = linked_list.head
        prev = None

        while curr:
            if curr.patient.patient_id == patient_id:
                if prev:
                    prev.next = curr.next

                    if curr == linked_list.tail:
                        linked_list.tail = prev
                else:
                    if linked_list.head == linked_list.tail:
                        linked_list.head = None
                        linked_list.tail = None
                    else:
                        linked_list.head = curr.next
                linked_list.size -= 1
                return True
            prev = curr
            curr =curr.next
        return False     
    
    @staticmethod
    def traverse_all(linked_list: PatientLinkedList) -> List[Patient]:
        """
        Algorithm:
        1. Create empty result list
        2. Start from head
        3. While current node exists:
           - Add patient to result list
           - Move to next node
        4. Return result list
        
        Time: O(n)
        Space: O(n) for result list
        """
        curr = linked_list.head
        patients = []

        while curr:
            patients.append(curr.patient)
            curr = curr.next
        
        return patients

if __name__ == "__main__":
    # Test patient linked list operations
    print("=== Testing Patient Linked List Operations ===\n")

    # Create patient linked list
    patient_list = PatientLinkedList()
    print(f"Created patient linked list: {patient_list}\n")

    # Example:
    patient1 = Patient("P001", "John Doe", 45, PatientStatus.IN_ICU)
    patient2 = Patient("P002", "Jane Smith", 30, PatientStatus.WAITING)
    patient3 = Patient("P003", "Bob Johnson", 55, PatientStatus.DISCHARGED)


    PatientListOperations.insert_at_head(patient_list, patient1)
    print(f"Inserted patient {patient1.patient_id} at head.\n")
    PatientListOperations.insert_at_tail(patient_list, patient2)
    print(f"Inserted patient {patient2.patient_id} at tail.\n")

    status = PatientListOperations.search_by_id(patient_list, "P001")
    if status:
        print(f"Search result: {status}\n")
    else:
        print("Patient P001 not found.\n")

    status = PatientListOperations.delete_by_id(patient_list, "P002")
    if status:
        print(f"Deleted patient P002.\n")
    else:
        print("Patient P002 not found. Deletion failed.\n")

    all_patients = PatientListOperations.traverse_all(patient_list)
    print(f"All patients in list: {[p.patient_id for p in all_patients]}\n")