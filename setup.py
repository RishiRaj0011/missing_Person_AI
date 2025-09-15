#!/usr/bin/env python3
"""
Setup script for Missing Person Finder
Handles installation of dependencies and system requirements
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def install_system_dependencies():
    """Install system-level dependencies based on OS"""
    system = platform.system().lower()
    
    if system == "windows":
        print("Windows detected - Please ensure you have:")
        print("1. Microsoft Visual C++ Build Tools")
        print("2. CMake (for dlib compilation)")
        print("3. Redis for Windows")
        
    elif system == "linux":
        try:
            subprocess.run(["sudo", "apt-get", "update"], check=True)
            subprocess.run([
                "sudo", "apt-get", "install", "-y",
                "build-essential", "cmake", "libopenblas-dev",
                "liblapack-dev", "libx11-dev", "libgtk-3-dev",
                "redis-server"
            ], check=True)
            print("✓ System dependencies installed")
        except subprocess.CalledProcessError:
            print("Warning: Could not install system dependencies automatically")
            
    elif system == "darwin":  # macOS
        try:
            subprocess.run(["brew", "install", "cmake", "redis"], check=True)
            print("✓ System dependencies installed via Homebrew")
        except subprocess.CalledProcessError:
            print("Warning: Please install cmake and redis via Homebrew manually")

def install_python_dependencies():
    """Install Python packages from requirements.txt"""
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ], check=True)
        
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✓ Python dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"Error installing Python dependencies: {e}")
        sys.exit(1)

def setup_environment():
    """Create .env file if it doesn't exist"""
    if not os.path.exists('.env'):
        env_content = """# Flask Configuration
SECRET_KEY=your-secret-key-change-this-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///app.db

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Upload Configuration
UPLOAD_FOLDER=app/static/uploads
MAX_CONTENT_LENGTH=16777216

# Security Settings
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=3600
"""
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✓ Environment file created")
    else:
        print("✓ Environment file already exists")

def create_directories():
    """Create necessary directories"""
    directories = [
        'app/static/uploads',
        'app/static/thumbnails',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("✓ Required directories created")

def main():
    """Main setup function"""
    print("Setting up Missing Person Finder...")
    print("=" * 50)
    
    check_python_version()
    install_system_dependencies()
    install_python_dependencies()
    setup_environment()
    create_directories()
    
    print("\n" + "=" * 50)
    print("Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start Redis server: redis-server")
    print("2. Initialize database: flask db init && flask db migrate && flask db upgrade")
    print("3. Run the application: python run.py")
    print("4. Start Celery worker: python celery_worker.py")

if __name__ == "__main__":
    main()