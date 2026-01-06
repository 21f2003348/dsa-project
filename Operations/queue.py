import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from Prototype.structure import WaitingQueueNode, WaitingQueueFIFO
from typing import Optional


class WaitingQueueOperations:
    """
    Implements:
    - enqueue() : Add patient to waiting list
    - dequeue() : Remove next waiting patient
    - peek() : See who's next without removing
    - is_empty() : Check if queue has patients
    - size() : Get queue length
    """
    
    @staticmethod
    def enqueue(waiting_queue: WaitingQueueFIFO, patient_id: str, priority_snapshot: int) -> bool:
        """
        Algorithm:
        1. Create WaitingQueueNode with patient_id and priority
        2. Append to queue list
        
        Time: O(1) amortized
        Space: O(1)
        """
        waiting_node = WaitingQueueNode(patient_id, priority_snapshot)
        waiting_queue.queue.append(waiting_node)
        return True
    
    @staticmethod
    def dequeue(waiting_queue: WaitingQueueFIFO) -> Optional[str]:
        """
        Algorithm:
        1. If queue empty, return None
        2. Remove first element (index 0)
        3. Return patient_id from removed node
        
        Time: O(1) if using collections.deque, O(n) if using list.pop(0)
        Space: O(1)
        
        NOTE: Consider using collections.deque for true O(1) dequeue
        Or use list.pop(0) for simplicity (acceptable for small queues)
        """
        if waiting_queue.queue:
            # Support deque (popleft) or list (pop(0))
            waiting_node = waiting_queue.queue.popleft()
            return waiting_node.patient_id
        return None
    
    @staticmethod
    def peek(waiting_queue: WaitingQueueFIFO) -> Optional[str]:
        """
        Algorithm:
        1. If queue empty, return None
        2. Return patient_id of first element (don't remove)
        
        Time: O(1)
        Space: O(1)
        """
        if waiting_queue.queue:
            return waiting_queue.queue[0].patient_id
        return None
    
    @staticmethod
    def is_empty(waiting_queue: WaitingQueueFIFO) -> bool:
        return len(waiting_queue.queue) == 0
    
    @staticmethod
    def get_size(waiting_queue: WaitingQueueFIFO) -> int:
        return len(waiting_queue.queue)
    
    @staticmethod
    def get_all_waiting(waiting_queue: WaitingQueueFIFO) -> list:
        """
        Get all waiting patient IDs in order
        
        Time: O(n)
        Space: O(n)
        """
        patient_ids = [node.patient_id for node in waiting_queue.queue]
        return patient_ids

if __name__ == "__main__":
    # Test queue operations
    print("=== Testing Waiting Queue Operations ===\n")
    
    # Create waiting queue
    waiting_queue = WaitingQueueFIFO()
    print(f"Created waiting queue: {waiting_queue}\n")
    
    # Example:
    WaitingQueueOperations.enqueue(waiting_queue, "P001", 2)
    print(f"Queue size: {WaitingQueueOperations.get_size(waiting_queue)}")