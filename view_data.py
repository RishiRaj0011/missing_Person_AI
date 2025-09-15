#!/usr/bin/env python3
"""
Database Viewer Script for Missing Person Finder
Run this script to view all user data and system information
"""

from app import create_app, db
from app.models import User, Case, TargetImage, SearchVideo, Sighting, SystemLog
from datetime import datetime

def view_all_data():
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("MISSING PERSON FINDER - DATABASE VIEWER")
        print("=" * 60)
        
        # Users
        print("\n📋 USERS:")
        users = User.query.all()
        if users:
            for user in users:
                print(f"  ID: {user.id}")
                print(f"  Username: {user.username}")
                print(f"  Email: {user.email}")
                print(f"  Admin: {'Yes' if user.is_admin else 'No'}")
                print(f"  Created: {user.created_at}")
                print(f"  Cases Submitted: {len(user.cases)}")
                print("-" * 40)
        else:
            print("  No users found")
        
        # Cases
        print("\n📁 CASES:")
        cases = Case.query.all()
        if cases:
            for case in cases:
                print(f"  Case ID: {case.id}")
                print(f"  Person: {case.person_name}")
                print(f"  Age: {case.age}")
                print(f"  Status: {case.status}")
                print(f"  Priority: {case.priority}")
                print(f"  Created by: {case.creator.username}")
                print(f"  Created: {case.created_at}")
                print(f"  Target Images: {len(case.target_images)}")
                print(f"  Search Videos: {len(case.search_videos)}")
                print(f"  Sightings: {len(case.sightings)}")
                print("-" * 40)
        else:
            print("  No cases found")
        
        # System Logs
        print("\n📊 RECENT SYSTEM LOGS:")
        logs = SystemLog.query.order_by(SystemLog.timestamp.desc()).limit(10).all()
        if logs:
            for log in logs:
                print(f"  {log.timestamp} - {log.action}")
                if log.details:
                    print(f"    Details: {log.details[:100]}...")
        else:
            print("  No logs found")
        
        # Statistics
        print("\n📈 STATISTICS:")
        print(f"  Total Users: {User.query.count()}")
        print(f"  Total Cases: {Case.query.count()}")
        print(f"  Total Sightings: {Sighting.query.count()}")
        print(f"  Admin Users: {User.query.filter_by(is_admin=True).count()}")
        
        # Database file info
        import os
        db_path = "app/app.db"
        if os.path.exists(db_path):
            size = os.path.getsize(db_path)
            print(f"  Database Size: {size:,} bytes")
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    view_all_data()