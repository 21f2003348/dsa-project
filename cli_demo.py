import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from Prototype.structure import DoctorSpecialization, AllocationReason
from Prototype.Operations.allocator import ICUAllocator, initialize_icu_system
from Prototype.Operations.patient import PatientListOperations
from Prototype.Operations.log import AllocationLogOperations
from datetime import datetime
import os


class ICUCliDemo:
    def __init__(self):
        self.system = None
        self.allocator = None
        self.running = True
        self.patient_counter = 1
    
    def clear_screen(self):
        # Clear terminal screen
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        # Headers
        print("\n" + "="*70)
        print(" "*20 + "ICU MANAGEMENT SYSTEM")
        print(" "*10 + "Intelligent Bed Allocation & Resource Management")
        print("="*70 + "\n")
    
    def print_menu(self):
        # Display main menu
        print("╔" + "═"*68 + "╗")
        print("║" + " "*25 + "MAIN MENU" + " "*34 + "║")
        print("╠" + "═"*68 + "╣")
        print("║  1. 🏥 Initialize ICU System                                       ║")
        print("║  2. ➕ Admit New Patient                                           ║")
        print("║  3. ➖ Discharge Patient                                           ║")
        print("║  4. 📊 View System Status                                          ║")
        print("║  5. 🛏️  View Bed Status                                             ║")
        print("║  6. ⏳ View Waiting Queue                                          ║")
        print("║  7. 👨‍⚕️  View Doctor Workload                                      ║")
        print("║  8. 📝 View Allocation Log                                         ║")
        print("║  9. 💾 Export Reports                                              ║")
        print("║  10. 🔍 Search Patient                                             ║")
        print("║  11. ℹ️  About System                                               ║")
        print("║  0. 🚪 Exit                                                        ║")
        print("╚" + "═"*68 + "╝\n")
    
    def wait_for_enter(self):
        # Pause and wait for user input
        input("\n⏸️  Press Enter to continue...")
    
    def initialize_system(self):
        # Initialize ICU system with configuration
        self.clear_screen()
        self.print_header()
        print("🔧 SYSTEM INITIALIZATION\n")
        
        try:
            num_beds = int(input("Enter number of ICU beds (default 10): ") or "10")
            
            print("\n👨‍⚕️ Configure Doctors:")
            print("1. Use default configuration (5 doctors)")
            print("2. Custom configuration")
            choice = input("Choose option (1/2): ").strip()
            
            if choice == "2":
                num_doctors = int(input("Number of doctors: "))
                doctors_config = []
                
                specializations = {
                    "1": DoctorSpecialization.GENERAL,
                    "2": DoctorSpecialization.CARDIAC,
                    "3": DoctorSpecialization.NEURO,
                    "4": DoctorSpecialization.PULMONARY
                }
                
                for i in range(num_doctors):
                    print(f"\n--- Doctor {i+1} ---")
                    name = input("Name: ")
                    exp = int(input("Years of experience: "))
                    print("Specialization: 1-General, 2-Cardiac, 3-Neuro, 4-Pulmonary")
                    spec_choice = input("Choose (1-4): ").strip()
                    while spec_choice not in {"1", "2", "3", "4"}:
                        print("Invalid choice. Please choose again.")
                        spec_choice = input("Choose (1-4): ").strip()
                    spec = specializations.get(spec_choice, DoctorSpecialization.GENERAL)
                    doctors_config.append((name, exp, spec))
                
                self.system = initialize_icu_system(num_beds, doctors_config)
            else:
                self.system = initialize_icu_system(num_beds)
            
            self.allocator = ICUAllocator(self.system)
            print(f"\n✅ System initialized successfully!")
            print(f"   • {num_beds} ICU beds")
            print(f"   • {len(self.system.doctors.heap)} doctors")
            
        except ValueError as e:
            print(f"❌ Invalid input: {e}")
        except Exception as e:
            print(f"❌ Error initializing system: {e}")
        
        self.wait_for_enter()
    
    def admit_patient(self):
        # Admit new patient with interactive form
        if not self.system:
            print("❌ System not initialized. Please initialize first.")
            self.wait_for_enter()
            return
        
        self.clear_screen()
        self.print_header()
        print("➕ ADMIT NEW PATIENT\n")
        
        try:
            # Auto-generate ID or manual
            print("Patient ID:")
            print(f"1. Auto-generate (P{self.patient_counter:03d})")
            print("2. Manual entry")
            id_choice = input("Choose option (1/2): ").strip()
            
            if id_choice == "2":
                patient_id = input("Enter Patient ID: ").strip()
            else:
                patient_id = f"P{self.patient_counter:03d}"
                self.patient_counter += 1
                print(f"Generated ID: {patient_id}")
            
            name = input("\nPatient Name: ").strip()
            age = int(input("Age: "))
            
            print("\nSeverity Level (1=Critical, 5=Stable):")
            print("  1 - Critical (Life-threatening)")
            print("  2 - Severe (Urgent care needed)")
            print("  3 - Moderate (Stable but needs monitoring)")
            print("  4 - Mild (Minor issues)")
            print("  5 - Stable (Observation only)")
            severity = int(input("Enter severity (1-5): "))
            
            if severity < 1 or severity > 5:
                print("❌ Invalid severity level. Must be 1-5.")
                self.wait_for_enter()
                return
            
            medical_notes = input("\nMedical Notes (optional): ").strip()
            
            print("\n" + "-"*70)
            print("📋 PATIENT SUMMARY:")
            print(f"  ID: {patient_id}")
            print(f"  Name: {name}")
            print(f"  Age: {age}")
            print(f"  Severity: {severity}")
            print(f"  Notes: {medical_notes or 'None'}")
            print("-"*70)
            
            confirm = input("\nConfirm admission? (y/n): ").strip().lower()
            
            if confirm == 'y':
                success, message = self.allocator.admit_patient(
                    patient_id, name, age, severity, medical_notes
                )
                
                if success:
                    print(f"\n✅ SUCCESS: {message}")
                else:
                    print(f"\n❌ FAILED: {message}")
            else:
                print("\n❌ Admission cancelled.")
        
        except ValueError as e:
            print(f"\n❌ Invalid input: {e}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        self.wait_for_enter()
    
    def discharge_patient(self):
        # Discharge patient
        if not self.system:
            print("❌ System not initialized. Please initialize first.")
            self.wait_for_enter()
            return
        
        self.clear_screen()
        self.print_header()
        print("➖ DISCHARGE PATIENT\n")
        
        # Show current ICU patients
        print("Current ICU Patients:")
        print("-"*70)
        icu_patients = []
        for bed in self.system.beds.beds:
            if bed.is_occupied:
                patient = PatientListOperations.search_by_id(
                    self.system.patients, bed.assigned_patient_id
                )
                if patient:
                    icu_patients.append(patient)
                    print(f"  • {patient.patient_id}: {patient.name} (Bed {bed.bed_id})")
        
        if not icu_patients:
            print("  (No patients in ICU)")
            self.wait_for_enter()
            return
        
        print("-"*70)
        
        try:
            patient_id = input("\nEnter Patient ID to discharge: ").strip()
            
            confirm = input(f"Confirm discharge of {patient_id}? (y/n): ").strip().lower()
            
            if confirm == 'y':
                success, message = self.allocator.discharge_patient(patient_id)
                
                if success:
                    print(f"\n✅ SUCCESS: {message}")
                else:
                    print(f"\n❌ FAILED: {message}")
            else:
                print("\n❌ Discharge cancelled.")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        self.wait_for_enter()
    
    def view_system_status(self):
        # Display system status
        if not self.system:
            print("❌ System not initialized. Please initialize first.")
            self.wait_for_enter()
            return
        
        self.clear_screen()
        self.print_header()
        self.allocator.print_system_status()
        self.wait_for_enter()
    
    def view_bed_status(self):
        # Display bed status
        if not self.system:
            print("❌ System not initialized. Please initialize first.")
            self.wait_for_enter()
            return
        
        self.clear_screen()
        self.print_header()
        self.allocator.print_bed_status()
        self.wait_for_enter()
    
    def view_waiting_queue(self):
        """Display waiting queue"""
        if not self.system:
            print("❌ System not initialized. Please initialize first.")
            self.wait_for_enter()
            return
        
        self.clear_screen()
        self.print_header()
        self.allocator.print_waiting_queue()
        self.wait_for_enter()
    
    def view_doctor_workload(self):
        """Display doctor workload"""
        if not self.system:
            print("❌ System not initialized. Please initialize first.")
            self.wait_for_enter()
            return
        
        self.clear_screen()
        self.print_header()
        print("👨‍⚕️ DOCTOR WORKLOAD REPORT\n")
        print("-"*70)
        
        from Prototype.Operations.doctor import DoctorHeapOperations
        
        # Get all doctors and sort by priority
        doctors = sorted(
            self.system.doctors.heap,
            key=lambda d: DoctorHeapOperations.get_priority(d),
            reverse=True
        )
        
        if not doctors:
            print("  (No doctors in system)")
        else:
            for doc in doctors:
                priority = DoctorHeapOperations.get_priority(doc)
                utilization = (doc.current_workload / doc.max_capacity) * 100
                
                print(f"\n📌 {doc.name} (ID: {doc.doctor_id})")
                print(f"   Specialization: {doc.specialization.value}")
                print(f"   Experience: {doc.experience_years} years")
                print(f"   Workload: {doc.current_workload}/{doc.max_capacity} patients")
                print(f"   Utilization: {utilization:.1f}%")
                print(f"   Priority Score: {priority}")
                print(f"   Status: {'Available' if doc.is_available else 'Unavailable'}")
                
                if doc.assigned_patients:
                    print(f"   Assigned Patients: {', '.join(doc.assigned_patients)}")
        
        print("-"*70)
        self.wait_for_enter()
    
    def view_allocation_log(self):
        """Display allocation log"""
        if not self.system:
            print("❌ System not initialized. Please initialize first.")
            self.wait_for_enter()
            return
        
        self.clear_screen()
        self.print_header()
        print("📝 ALLOCATION LOG\n")
        print("-"*70)
        
        records = AllocationLogOperations.get_all_records(self.system.allocation_log)
        
        if not records:
            print("  (No allocations recorded)")
        else:
            for record in records:
                print(f"\n[{record.record_id}] {record.allocation_time.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"    Patient: {record.patient_id} (Severity: {record.patient_severity})")
                print(f"    Bed: {record.bed_id}")
                print(f"    Doctor: {record.doctor_id} (Priority: {record.doctor_priority_score})")
                print(f"    Reason: {record.decision_reason.value}")
        
        print("-"*70)
        print(f"\nTotal Allocations: {len(records)}")
        self.wait_for_enter()
    
    def export_reports(self):
        """Export reports to file"""
        if not self.system:
            print("❌ System not initialized. Please initialize first.")
            self.wait_for_enter()
            return
        
        self.clear_screen()
        self.print_header()
        print("💾 EXPORT REPORTS\n")
        
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Export allocation log
            log_filename = f"allocation_log_{timestamp}.txt"
            success = AllocationLogOperations.export_to_file(
                self.system.allocation_log, 
                log_filename
            )
            
            if success:
                print(f"✅ Allocation log exported to: {log_filename}")
            
            # Export system status
            status_filename = f"system_status_{timestamp}.txt"
            with open(status_filename, 'w') as f:
                status = self.allocator.get_system_status()
                f.write("ICU MANAGEMENT SYSTEM - STATUS REPORT\n")
                f.write("="*70 + "\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                f.write("PATIENTS:\n")
                f.write(f"  Total Admitted: {status['total_patients']}\n")
                f.write(f"  In ICU: {status['patients_in_icu']}\n")
                f.write(f"  Waiting: {status['patients_waiting']}\n")
                f.write(f"  Discharged: {status['patients_discharged']}\n\n")
                
                f.write("BEDS:\n")
                f.write(f"  Occupied: {status['beds_occupied']}/{status['beds_total']}\n")
                f.write(f"  Free: {status['beds_free']}/{status['beds_total']}\n\n")
                
                f.write("DOCTORS:\n")
                f.write(f"  Active: {status['doctors_active']}\n\n")
                
                f.write("ALLOCATIONS:\n")
                f.write(f"  Total Logged: {status['total_allocations']}\n")
            
            print(f"✅ System status exported to: {status_filename}")
            print(f"\n📁 Files saved in: {Path.cwd()}")
        
        except Exception as e:
            print(f"❌ Error exporting reports: {e}")
        
        self.wait_for_enter()
    
    def search_patient(self):
        """Search for patient"""
        if not self.system:
            print("❌ System not initialized. Please initialize first.")
            self.wait_for_enter()
            return
        
        self.clear_screen()
        self.print_header()
        print("🔍 SEARCH PATIENT\n")
        
        try:
            patient_id = input("Enter Patient ID: ").strip()
            
            patient = PatientListOperations.search_by_id(
                self.system.patients, 
                patient_id
            )
            
            if patient:
                print("\n" + "="*70)
                print("📋 PATIENT DETAILS")
                print("="*70)
                print(f"ID: {patient.patient_id}")
                print(f"Name: {patient.name}")
                print(f"Age: {patient.age}")
                print(f"Severity Level: {patient.severity_level}")
                print(f"Status: {patient.status.value}")
                print(f"Arrival Time: {patient.arrival_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if patient.status.value == "IN_ICU":
                    print(f"Assigned Bed: {patient.assigned_bed_id}")
                    print(f"Assigned Doctor: {patient.assigned_doctor_id}")
                    if patient.assignment_time:
                        print(f"Assignment Time: {patient.assignment_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if patient.status.value == "DISCHARGED" and patient.discharge_time:
                    print(f"Discharge Time: {patient.discharge_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                if patient.medical_notes:
                    print(f"Medical Notes: {patient.medical_notes}")
                
                print("="*70)
            else:
                print(f"\n❌ Patient {patient_id} not found.")
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        self.wait_for_enter()
    
    def show_about(self):
        """Show about information"""
        self.clear_screen()
        self.print_header()
        print("ℹ️  ABOUT ICU MANAGEMENT SYSTEM\n")
        print("="*70)
        print("\n📌 Project Information:")
        print("   Name: Intelligent ICU Bed Allocation System")
        print("   Version: 1.0.0")
        print("   Course: Data Structures & Algorithms")
        print("\n📚 Data Structures Used:")
        print("   • Linked List - Patient record management")
        print("   • Array - ICU bed tracking")
        print("   • Max Heap - Doctor prioritization")
        print("   • FIFO Queue - Waiting patient management")
        print("   • List - Allocation audit log")
        print("\n⚙️  Features:")
        print("   ✓ Automated bed allocation")
        print("   ✓ Doctor workload balancing")
        print("   ✓ Fair waiting queue (FIFO)")
        print("   ✓ Complete audit trail")
        print("   ✓ Real-time status monitoring")
        print("\n👥 Team: [Your Name/Team]")
        print("📅 Date: January 2026")
        print("="*70)
        self.wait_for_enter()
    
    def run(self):
        """Main application loop"""
        self.clear_screen()
        self.print_header()
        print("Welcome to the ICU Management System!")
        print("\nThis is an interactive demonstration of intelligent")
        print("resource allocation using data structures.\n")
        self.wait_for_enter()
        
        while self.running:
            self.clear_screen()
            self.print_header()
            self.print_menu()
            
            try:
                choice = input("Enter your choice (0-11): ").strip()
                
                if choice == "1":
                    self.initialize_system()
                elif choice == "2":
                    self.admit_patient()
                elif choice == "3":
                    self.discharge_patient()
                elif choice == "4":
                    self.view_system_status()
                elif choice == "5":
                    self.view_bed_status()
                elif choice == "6":
                    self.view_waiting_queue()
                elif choice == "7":
                    self.view_doctor_workload()
                elif choice == "8":
                    self.view_allocation_log()
                elif choice == "9":
                    self.export_reports()
                elif choice == "10":
                    self.search_patient()
                elif choice == "11":
                    self.show_about()
                elif choice == "0":
                    self.clear_screen()
                    self.print_header()
                    print("Thank you for using ICU Management System!")
                    print("\n👋 Goodbye!\n")
                    self.running = False
                else:
                    print("\n❌ Invalid choice. Please enter 0-11.")
                    self.wait_for_enter()
            
            except KeyboardInterrupt:
                print("\n\n⚠️  Interrupted by user.")
                self.running = False
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                self.wait_for_enter()


if __name__ == "__main__":
    demo = ICUCliDemo()
    demo.run()
