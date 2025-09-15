#!/usr/bin/env python3
"""
Database Migration Script
This script will update your database schema to match the current models
"""

from app import create_app, db
from app.models import User, AdminMessage, Announcement, BlogPost, FAQ, AISettings
from sqlalchemy import text

def migrate_database():
    app = create_app()
    with app.app_context():
        print("🔄 Starting database migration...")
        
        try:
            # Create all new tables
            db.create_all()
            print("✅ Created all new tables")
            
            # Check if new columns exist in User table, if not add them
            inspector = db.inspect(db.engine)
            user_columns = [col['name'] for col in inspector.get_columns('user')]
            
            # Add missing columns to User table
            missing_columns = []
            
            if 'last_login' not in user_columns:
                missing_columns.append('last_login DATETIME')
            
            if 'login_count' not in user_columns:
                missing_columns.append('login_count INTEGER DEFAULT 0')
            
            if 'is_active' not in user_columns:
                missing_columns.append('is_active BOOLEAN DEFAULT 1')
            
            if 'location' not in user_columns:
                missing_columns.append('location VARCHAR(200)')
            
            # Execute ALTER TABLE statements for missing columns
            for column in missing_columns:
                try:
                    db.engine.execute(text(f'ALTER TABLE user ADD COLUMN {column}'))
                    print(f"✅ Added column: {column}")
                except Exception as e:
                    print(f"⚠️  Column might already exist: {column}")
            
            # Update existing users to have default values
            db.engine.execute(text("""
                UPDATE user 
                SET login_count = 0 
                WHERE login_count IS NULL
            """))
            
            db.engine.execute(text("""
                UPDATE user 
                SET is_active = 1 
                WHERE is_active IS NULL
            """))
            
            print("✅ Updated existing user records with default values")
            
            # Commit all changes
            db.session.commit()
            
            print("\n" + "="*60)
            print("🎉 DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("✅ All tables created")
            print("✅ All columns added")
            print("✅ Default values set")
            print("="*60)
            print("\n📋 Next Steps:")
            print("1. Run: python setup_admin.py")
            print("2. Run: python run.py")
            print("3. Login at: http://localhost:5000/login")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    migrate_database()