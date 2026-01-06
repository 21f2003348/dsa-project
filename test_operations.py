from structure import ICUBedArray, PatientLinkedList
from Operations.bed import BedArrayOperations
from Operations.queue import WaitingQueueOperations
from Operations.log import AllocationLogOperations
from Operations.doctor import DoctorHeapOperations
from structure import AllocationLogList, WaitingQueueFIFO, Doctor, DoctorSpecialization

print('Running operations smoke tests...')

# Bed tests
beds = ICUBedArray(num_beds=3)
print('Initial free bed:', BedArrayOperations.find_free_bed(beds))
BedArrayOperations.allocate_bed(beds, 0, 'P001')
print('Free bed after one allocate:', BedArrayOperations.find_free_bed(beds))
print('Free count:', BedArrayOperations.count_free_beds(beds))
BedArrayOperations.release_bed(beds, 0)
print('Free count after release:', BedArrayOperations.count_free_beds(beds))

# Queue tests
wq = WaitingQueueFIFO()
WaitingQueueOperations.enqueue(wq, 'P002', 2)
WaitingQueueOperations.enqueue(wq, 'P003', 3)
print('Queue size after enqueue:', WaitingQueueOperations.get_size(wq))
print('Peek:', WaitingQueueOperations.peek(wq))
print('Dequeue:', WaitingQueueOperations.dequeue(wq))
print('Queue size after dequeue:', WaitingQueueOperations.get_size(wq))

# Log tests
log = AllocationLogList()
rec = AllocationLogOperations.append_record(log, 'P002', 1, 10, 2, 8)
print('Log total count:', AllocationLogOperations.get_total_count(log))
print('Query by patient:', AllocationLogOperations.query_by_patient(log, 'P002'))

# Doctor heap tests
heap = __import__('Prototype.Operations.doctor', fromlist=['DoctorMaxHeap']).DoctorMaxHeap()
# Create doctors
d1 = Doctor(1, 'Dr A', 10, DoctorSpecialization.GENERAL, 5)
d2 = Doctor(2, 'Dr B', 5, DoctorSpecialization.GENERAL, 5)
DoctorHeapOperations.insert_doctor(heap, d1)
DoctorHeapOperations.insert_doctor(heap, d2)
print('Peek max doctor ID:', DoctorHeapOperations.peek_max(heap).doctor_id)
# Update workload
DoctorHeapOperations.update_doctor_workload(heap, 1, 9)
print('Peek after workload update:', DoctorHeapOperations.peek_max(heap).doctor_id)

print('All tests completed.')
