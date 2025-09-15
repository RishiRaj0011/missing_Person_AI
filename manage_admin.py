#!/usr/bin/env python3
"""
Admin Management Script for Missing Person Finder
Use this to create, update, or manage admin users
"""

from app import create_app, db
from app.models import User
import getpass

def create_admin():
    """Create a new admin user"""
    print("=== CREATE NEW ADMIN ===")
    username = input("Enter username: ")
    email = input("Enter email: ")
    password = getpass.getpass("Enter password: ")
    
    # Check if user exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        print(f"User '{username}' already exists!")
        return
    
    # Create admin user
    admin = User(username=username, email=email, is_admin=True)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    
    print(f"Admin user '{username}' created successfully!")

def update_admin():
    """Update existing admin credentials"""
    print("=== UPDATE ADMIN CREDENTIALS ===")
    current_username = input("Enter current username: ")
    
    user = User.query.filter_by(username=current_username).first()
    if not user:
        print(f"User '{current_username}' not found!")
        return
    
    print(f"Updating user: {user.username} ({user.email})")
    
    new_username = input(f"New username (current: {user.username}): ") or user.username
    new_email = input(f"New email (current: {user.email}): ") or user.email
    new_password = getpass.getpass("New password (leave blank to keep current): ")
    
    user.username = new_username
    user.email = new_email
    if new_password:
        user.set_password(new_password)
    
    db.session.commit()
    print("Admin credentials updated successfully!")

def list_admins():
    """List all admin users"""
    print("=== ALL ADMIN USERS ===")
    admins = User.query.filter_by(is_admin=True).all()
    
    if not admins:
        print("No admin users found!")
        return
    
    for admin in admins:
        print(f"ID: {admin.id} | Username: {admin.username} | Email: {admin.email} | Created: {admin.created_at}")

def promote_user():
    """Promote regular user to admin"""
    print("=== PROMOTE USER TO ADMIN ===")
    username = input("Enter username to promote: ")
    
    user = User.query.filter_by(username=username).first()
    if not user:
        print(f"User '{username}' not found!")
        return
    
    if user.is_admin:
        print(f"User '{username}' is already an admin!")
        return
    
    user.is_admin = True
    db.session.commit()
    print(f"User '{username}' promoted to admin!")

def main():
    app = create_app()
    with app.app_context():
        while True:
            print("\n" + "="*50)
            print("ADMIN MANAGEMENT SYSTEM")
            print("="*50)
            print("1. Create new admin")
            print("2. Update admin credentials")
            print("3. List all admins")
            print("4. Promote user to admin")
            print("5. Exit")
            
            choice = input("\nSelect option (1-5): ")
            
            if choice == "1":
                create_admin()
            elif choice == "2":
                update_admin()
            elif choice == "3":
                list_admins()
            elif choice == "4":
                promote_user()
            elif choice == "5":
                print("Goodbye!")
                break
            else:
                print("Invalid choice!")

if __name__ == "__main__":
    main()