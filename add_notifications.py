#!/usr/bin/env python3
"""
Database migration script to add Notification table
Run this script to add the notification system to your existing database
"""

import os
import sys
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import Notification, User

def add_notifications_table():
    """Add the Notification table to the database"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create the notifications table
            db.create_all()
            
            # Create a welcome notification for all existing users
            users = User.query.all()
            for user in users:
                welcome_notification = Notification(
                    user_id=user.id,
                    sender_id=None,  # System message
                    title="Welcome to the Enhanced Platform!",
                    message="We've added a new notification system to keep you updated on important messages and system updates. You'll receive notifications here when admins send you messages.",
                    type="success"
                )
                db.session.add(welcome_notification)
            
            db.session.commit()
            print("✅ Successfully added Notification table and welcome messages!")
            print(f"📊 Created welcome notifications for {len(users)} users")
            
        except Exception as e:
            print(f"❌ Error adding notifications table: {e}")
            db.session.rollback()

if __name__ == "__main__":
    print("🔄 Adding Notification table to database...")
    add_notifications_table()