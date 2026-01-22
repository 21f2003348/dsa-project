"""
Main Flask Application for ICU Management System

This is the entry point for the web application.
Handles initialization, database setup, and route registration.
"""

from flask import Flask, render_template
from config import config
from models import db
from database import init_database, check_database_exists, seed_default_data
from structure import ICUManagementSystem
from sync import load_system_from_db
from Operations.allocator import ICUAllocator
import os
import threading
import time


# Global system instance
icu_system = None
allocator = None


def create_app(config_name='development'):
    """
    Application factory pattern
    
    Args:
        config_name: Configuration to use (development, production, testing)
        
    Returns:
        Flask app instance
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize database
    db.init_app(app)
    
    # Register routes
    from routes import main_bp
    app.register_blueprint(main_bp)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    return app


def initialize_system(app):
    """
    Initialize ICU system with database data
    
    Args:
        app: Flask application instance
    """
    global icu_system, allocator
    
    with app.app_context():
        # Check if database exists
        db_exists = check_database_exists(app)
        
        if not db_exists:
            print("🔧 First run detected - Initializing database...")
            init_database(app)
            seed_default_data(app)
        else:
            print("✅ Database found")
        
        # Create ICU system with default configuration
        num_beds = app.config.get('DEFAULT_NUM_BEDS', 10)
        icu_system = ICUManagementSystem(num_beds=num_beds)
        
        # Load data from database into DSA structures
        icu_system = load_system_from_db(app, icu_system)
        
        # Create allocator
        allocator = ICUAllocator(icu_system)
        
        print("✅ ICU Management System initialized successfully")
        print(f"   • {len(icu_system.beds.beds)} beds")
        print(f"   • {len(icu_system.doctors.heap)} doctors")
        print(f"   • {icu_system.patients.size} patients")
        print(f"   • {len(icu_system.waiting_queue.queue)} in waiting queue")
        
        # Start periodic bed allocation checker
        start_periodic_allocation_checker(app, allocator)


def start_periodic_allocation_checker(app, allocator_instance):
    """
    Start background thread to periodically check if beds can be allocated
    to waiting patients.
    
    Checks every 30 seconds by default.
    """
    def check_and_allocate():
        """Periodically check waiting queue and allocate beds if available"""
        while True:
            try:
                time.sleep(30)  # Check every 30 seconds
                
                with app.app_context():
                    if allocator_instance and allocator_instance.system:
                        # Check if there are waiting patients and free beds
                        from Operations.queue import WaitingQueueOperations
                        from Operations.bed import BedArrayOperations
                        from Operations.patient import PatientListOperations
                        from structure import PatientStatus
                        
                        if not WaitingQueueOperations.is_empty(allocator_instance.system.waiting_queue):
                            # Get all waiting patients (sorted by severity)
                            waiting_ids = WaitingQueueOperations.get_all_waiting(
                                allocator_instance.system.waiting_queue
                            )
                            
                            for patient_id in waiting_ids:
                                patient = PatientListOperations.search_by_id(
                                    allocator_instance.system.patients,
                                    patient_id
                                )
                                
                                if patient and patient.status == PatientStatus.WAITING:
                                    # Get requested bed type
                                    requested_bed_type = getattr(patient, 'requested_bed_type', 'GENERAL')
                                    
                                    # Check if bed of this type is available
                                    free_bed_id = BedArrayOperations.find_free_bed(
                                        allocator_instance.system.beds,
                                        requested_bed_type.upper()
                                    )
                                    
                                    if free_bed_id is not None:
                                        # Try to allocate
                                        success, msg = allocator_instance._allocate_to_icu(
                                            patient, 
                                            requested_bed_type
                                        )
                                        
                                        if success:
                                            # Remove from queue
                                            for idx, node in enumerate(allocator_instance.system.waiting_queue.queue):
                                                if node.patient_id == patient_id:
                                                    allocator_instance.system.waiting_queue.queue.remove(node)
                                                    from sync import remove_from_waiting_queue_db
                                                    remove_from_waiting_queue_db(patient_id)
                                                    break
                                            print(f"✓ Periodic check: Allocated {requested_bed_type} bed to waiting patient {patient_id}")
                                            break  # Allocated one, check again next cycle
            except Exception as e:
                print(f"⚠ Error in periodic allocation checker: {e}")
                time.sleep(60)  # Wait longer on error
    
    # Start background thread
    checker_thread = threading.Thread(target=check_and_allocate, daemon=True)
    checker_thread.start()
    print("✅ Periodic bed allocation checker started (checks every 30 seconds)")


if __name__ == '__main__':
    # Create app
    app = create_app('development')
    
    # Initialize system
    initialize_system(app)
    
    # Run app
    print("\n" + "="*70)
    print(" "*15 + "🏥 ICU MANAGEMENT SYSTEM 🏥")
    print(" "*10 + "Web Application - Flask + SQLAlchemy + DSA")
    print("="*70)
    print(f"\n🌐 Server running at: http://localhost:5000")
    print("📊 Access the dashboard to manage ICU operations")
    print("\nPress CTRL+C to stop the server\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
