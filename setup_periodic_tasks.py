#!/usr/bin/env python3
"""
Setup script for periodic file cleanup tasks
Run this once to schedule automatic file cleanup
"""

from celery import Celery
from celery.schedules import crontab
from app import create_app

def setup_periodic_tasks():
    """Setup periodic tasks for file cleanup"""
    app = create_app()
    
    # Configure Celery with periodic tasks
    celery = Celery(app.import_name)
    celery.config_from_object(app.config)
    
    # Schedule file cleanup to run daily at 2 AM
    celery.conf.beat_schedule = {
        'cleanup-files': {
            'task': 'app.tasks.cleanup_files',
            'schedule': crontab(hour=2, minute=0),  # Run daily at 2:00 AM
        },
    }
    celery.conf.timezone = 'UTC'
    
    print("✅ Periodic file cleanup task scheduled for 2:00 AM daily")
    print("📋 To start the scheduler, run: celery -A app.tasks beat")
    print("📋 To start the worker, run: python celery_worker.py")

if __name__ == "__main__":
    setup_periodic_tasks()