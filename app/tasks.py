import logging
import traceback
from datetime import datetime

from celery import Celery

from app import create_app, db
from app.models import Case, SystemLog
from app.vision_engine import VisionProcessor

# We don't create the app here anymore to prevent circular imports.
# The app context is handled by the worker.
celery = Celery(__name__)


@celery.task
def process_case(case_id):
    # Create a new app instance for this task to ensure a clean context.
    app = create_app()
    with app.app_context():
        case = Case.query.get(case_id)
        if not case:
            from app.utils import sanitize_log_input
            safe_case_id = sanitize_log_input(str(case_id))
            logging.error(f"Task failed: Case with ID {safe_case_id} not found.")
            return

        try:
            # Update case status to 'Processing'
            case.status = "Processing"
            db.session.commit()

            # Log the start of processing
            log_start = SystemLog(
                case_id=case_id,
                action="case_processing_started",
                details=f"Started processing case for {case.person_name}",
            )
            db.session.add(log_start)
            db.session.commit()

            # Run the main AI analysis
            processor = VisionProcessor(case_id)
            processor.run_analysis()

            # Update case status to 'Completed'
            case.status = "Completed"
            case.completed_at = datetime.utcnow()
            db.session.commit()

            # Log successful completion
            log_complete = SystemLog(
                case_id=case_id,
                action="case_processing_completed",
                details=f"Successfully completed processing. Found {len(case.sightings)} sightings.",
            )
            db.session.add(log_complete)
            db.session.commit()

        except Exception as e:
            # FIX 1: Roll back the failed transaction first. This is critical.
            db.session.rollback()
            
            # Now, safely update the database with the error status
            try:
                case.status = "Error"
                
                error_details = f"Error processing case {case_id}: {str(e)}\n{traceback.format_exc()}"
                log_error = SystemLog(
                    case_id=case_id,
                    action="case_processing_failed",
                    details=error_details,
                )
                db.session.add(log_error)
                db.session.commit()

            except Exception as db_error:
                # FIX 2: Use proper logging instead of print().
                from app.utils import sanitize_log_input
                safe_case_id = sanitize_log_input(str(case_id))
                safe_error = sanitize_log_input(str(e))
                safe_db_error = sanitize_log_input(str(db_error))
                logging.critical(f"CRITICAL: Failed to update database with error status for case {safe_case_id}.")
                logging.critical(f"Original Error: {safe_error}")
                logging.critical(f"DB Error: {safe_db_error}")

            # Re-raise the original exception so Celery knows the task failed
            raise e


@celery.task
def cleanup_files():
    """Periodic task to clean up orphaned files and enforce storage limits"""
    app = create_app()
    with app.app_context():
        try:
            from app.file_manager import cleanup_orphaned_files, enforce_storage_limits
            
            # Clean up orphaned files
            orphaned_count = cleanup_orphaned_files()
            logging.info(f"Cleaned up {orphaned_count} orphaned files")
            
            # Enforce storage limits
            removed_count = enforce_storage_limits()
            if removed_count > 0:
                logging.info(f"Removed {removed_count} old files to enforce storage limits")
            
            return f"Cleanup completed: {orphaned_count} orphaned, {removed_count} for storage"
            
        except Exception as e:
            logging.error(f"File cleanup failed: {e}")
            raise e