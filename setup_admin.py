#!/usr/bin/env python3
"""
Complete Admin Setup Script
This script will migrate the database and create your admin account
"""

import os
from app import create_app, db
from app.models import User
from sqlalchemy import text

def setup_admin():
    app = create_app()
    with app.app_context():
        print("🔄 Setting up database and admin account...")
        
        try:
            # Step 1: Create all tables and migrate database
            print("📊 Creating/updating database schema...")
            db.create_all()
            
            # Step 2: Add missing columns to User table if they don't exist
            try:
                inspector = db.inspect(db.engine)
                user_columns = [col['name'] for col in inspector.get_columns('user')]
                
                missing_columns = []
                if 'last_login' not in user_columns:
                    missing_columns.append('last_login DATETIME')
                if 'login_count' not in user_columns:
                    missing_columns.append('login_count INTEGER DEFAULT 0')
                if 'is_active' not in user_columns:
                    missing_columns.append('is_active BOOLEAN DEFAULT 1')
                if 'location' not in user_columns:
                    missing_columns.append('location VARCHAR(200)')
                
                for column in missing_columns:
                    try:
                        db.session.execute(text(f'ALTER TABLE user ADD COLUMN {column}'))
                        print(f"✅ Added column: {column}")
                    except:
                        pass  # Column might already exist
                        
                # Update existing users with default values
                db.session.execute(text("UPDATE user SET login_count = 0 WHERE login_count IS NULL"))
                db.session.execute(text("UPDATE user SET is_active = 1 WHERE is_active IS NULL"))
                db.session.commit()
                
            except Exception as e:
                print(f"⚠️  Database migration note: {str(e)}")
            
            # Step 3: Create admin account from environment variables
            admin_username = os.environ.get("ADMIN_USERNAME", "admin")
            admin_email = os.environ.get("ADMIN_EMAIL", "admin@example.com")
            admin_password = os.environ.get("ADMIN_PASSWORD", "ChangeThisPassword123!")
            
            if admin_password == "ChangeThisPassword123!":
                print("⚠️  WARNING: Using default admin password! Change ADMIN_PASSWORD in .env file")
            
            # Check if admin already exists
            admin = User.query.filter_by(username=admin_username).first()
            
            if admin:
                # Update existing user to admin
                admin.is_admin = True
                admin.email = admin_email
                admin.set_password(admin_password)
                admin.is_active = True
                admin.login_count = admin.login_count or 0
                print(f"✅ Updated existing user '{admin_username}' to admin")
            else:
                # Create new admin
                admin = User(
                    username=admin_username,
                    email=admin_email,
                    is_admin=True,
                    is_active=True,
                    login_count=0
                )
                admin.set_password(admin_password)
                db.session.add(admin)
                print(f"✅ Created new admin user '{admin_username}'")
            
            db.session.commit()
            
            print("\n" + "="*60)
            print("🎉 SETUP COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"🌐 Login URL: http://localhost:5000/login")
            print(f"👤 Username: {admin_username}")
            print(f"📧 Email: {admin_email}")
            print(f"🔑 Password: {admin_password}")
            print(f"🛡️  Admin Dashboard: http://localhost:5000/admin/dashboard")
            print("="*60)
            print("\n📋 Next Steps:")
            print("1. Run: python run.py")
            print("2. Go to: http://localhost:5000/login")
            print("3. Login with the credentials above")
            print("4. Click 'Admin' in the navigation bar")
            
        except Exception as e:
            print(f"❌ Setup failed: {str(e)}")
            print("\n🔧 Try running these commands manually:")
            print("1. python migrate_database.py")
            print("2. python setup_admin.py")
            db.session.rollback()
            raise

if __name__ == "__main__":
    setup_admin()