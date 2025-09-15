from app import create_app, db
from app.models import User, Case, SystemLog

def show_all_users():
    app = create_app()
    with app.app_context():
        users = User.query.all()
        print("=== ALL REGISTERED USERS ===")
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Admin: {user.is_admin}")
            print(f"Created: {user.created_at}")
            print(f"Cases: {len(user.cases)}")
            print("-" * 30)
        print(f"Total Users: {len(users)}")

def show_user_details(username):
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if user:
            print(f"User Details for: {username}")
            print(f"ID: {user.id}")
            print(f"Email: {user.email}")
            print(f"Admin Status: {user.is_admin}")
            print(f"Registration Date: {user.created_at}")
            print(f"Cases Submitted: {len(user.cases)}")
        else:
            print(f"User '{username}' not found")

if __name__ == "__main__":
    show_all_users()