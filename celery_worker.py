import logging
from app import create_app
from app.tasks import celery

# Configure logging to show clear error messages
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    # We try to create the app
    app = create_app()
    app.app_context().push()

except Exception as e:
    # If creating the app fails for any reason, we log the error and stop.
    logging.error("CRITICAL: Failed to create the Flask application for the Celery worker.")
    logging.error(e, exc_info=True) # This logs the full traceback for debugging.
    raise e

# The 'if __name__ == "__main__"' block is not needed because we start the worker
# with the "celery -A ..." command.