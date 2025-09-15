from app import create_app, db
import os

app = create_app()

# Create upload directory if it doesn't exist
upload_dir = os.path.join(app.root_path, "static", "uploads")
os.makedirs(upload_dir, exist_ok=True)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    
    # Use environment variable to control debug mode
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)
