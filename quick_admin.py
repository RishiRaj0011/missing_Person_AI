#!/usr/bin/env python3
"""
Quick Admin Credential Changer
Usage: python quick_admin.py [username] [password]
"""

import sys
from app import create_app, db
from app.models import User

def change_admin_credentials(new_username, new_password):
    app = create_app()
    with app.app_context():
        # Find first admin user or create one
        admin = User.query.filter_by(is_admin=True).first()
        
        if not admin:
            # Create new admin if none exists
            admin = User(username=new_username, email=f"{new_username}@admin.com", is_admin=True)
            admin.set_password(new_password)
            db.session.add(admin)
            print(f"Created new admin: {new_username}")
        else:
            # Update existing admin
            old_username = admin.username
            admin.username = new_username
            admin.set_password(new_password)
            print(f"Updated admin: {old_username} -> {new_username}")
        
        db.session.commit()
        print(f"Admin credentials: username={new_username}, password={new_password}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python quick_admin.py [username] [password]")
        print("Example: python quick_admin.py myusername mypassword")
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    change_admin_credentials(username, password)