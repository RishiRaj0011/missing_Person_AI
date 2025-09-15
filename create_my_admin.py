#!/usr/bin/env python3
"""
Create Your Personal Admin Account
Run this script to set up your single admin account with custom credentials
"""

from app import create_app, db
from app.models import User

def create_single_admin():
    app = create_app()
    with app.app_context():
        # Delete any existing admins first
        existing_admins = User.query.filter_by(is_admin=True).all()
        for admin in existing_admins:
            db.session.delete(admin)
        
        print("=== CREATE YOUR ADMIN ACCOUNT ===")
        print("Enter your desired admin credentials:")
        
        username = input("Admin Username: ")
        email = input("Admin Email: ")
        password = input("Admin Password: ")
        
        # Validate inputs
        if not username or not email or not password:
            print("Error: All fields are required!")
            return
        
        # Check if username already exists (for regular users)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"Error: Username '{username}' already exists!")
            return
        
        # Create the single admin user
        admin = User(
            username=username,
            email=email,
            is_admin=True
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        print("\n" + "="*50)
        print("✅ SUCCESS! Your admin account has been created:")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print("="*50)
        print("\nYou can now login at: http://localhost:5000/login")
        print("Admin Dashboard: http://localhost:5000/admin/dashboard")

if __name__ == "__main__":
    create_single_admin()