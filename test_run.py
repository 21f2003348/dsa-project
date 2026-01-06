from structure import Patient, PatientLinkedList
from Operations.patient import PatientListOperations

print('Starting quick import test...')

# Create patient and list
p = Patient('P001', 'Alice', 30, 2)
pl = PatientLinkedList()

# Insert at tail
PatientListOperations.insert_at_tail(pl, p)

print('Patient list size after insert:', pl.size)
print('Head patient:', pl.head.patient)

print('Quick import test completed successfully.')
