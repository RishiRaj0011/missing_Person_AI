#!/usr/bin/env python3
"""
Initialize Admin from Environment Variables
This creates your admin user from the .env file settings
"""

import os
from app import create_app, db
from app.models import User

def init_admin_from_env():
    app = create_app()
    with app.app_context():
        # Get admin credentials from environment
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
        
        # Remove all existing admins
        existing_admins = User.query.filter_by(is_admin=True).all()
        for admin in existing_admins:
            print(f"Removing existing admin: {admin.username}")
            db.session.delete(admin)
        
        # Check if user with this username already exists
        existing_user = User.query.filter_by(username=admin_username).first()
        if existing_user and not existing_user.is_admin:
            # Promote existing user to admin
            existing_user.is_admin = True
            existing_user.email = admin_email
            existing_user.set_password(admin_password)
            db.session.commit()
            print(f"Promoted existing user '{admin_username}' to admin")
        elif not existing_user:
            # Create new admin user
            admin = User(
                username=admin_username,
                email=admin_email,
                is_admin=True
            )
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()
            print(f"Created new admin user: {admin_username}")
        
        # Verify single admin
        admin_count = User.query.filter_by(is_admin=True).count()
        admin_user = User.query.filter_by(is_admin=True).first()
        
        print("\n" + "="*50)
        print("✅ ADMIN SETUP COMPLETE")
        print("="*50)
        print(f"Total Admins: {admin_count}")
        print(f"Username: {admin_user.username}")
        print(f"Email: {admin_user.email}")
        print("Password: [Set from .env file]")
        print("="*50)

if __name__ == "__main__":
    init_admin_from_env()