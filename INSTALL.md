# Installation Guide - Missing Person Finder

## Prerequisites

### System Requirements
- **Python 3.8+** (Required)
- **Redis Server** (Required for background tasks)
- **Visual C++ Build Tools** (Windows only - for dlib compilation)
- **CMake** (Required for dlib)

### Hardware Requirements
- **RAM:** Minimum 4GB, Recommended 8GB+
- **Storage:** 2GB free space
- **CPU:** Multi-core recommended for video processing

## Quick Installation

### Option 1: Automated Setup (Recommended)
```bash
# Clone or download the project
cd missing_person_finder

# Run automated setup
python setup.py
```

### Option 2: Manual Installation

#### Step 1: Install System Dependencies

**Windows:**
1. Install [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
2. Install [CMake](https://cmake.org/download/) and add to PATH
3. Install [Redis for Windows](https://github.com/microsoftarchive/redis/releases)

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake libopenblas-dev liblapack-dev libx11-dev libgtk-3-dev redis-server
```

**macOS:**
```bash
brew install cmake redis
```

#### Step 2: Install Python Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

#### Step 3: Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
```

#### Step 4: Database Setup
```bash
# Initialize database
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

## Configuration

### Environment Variables (.env)
```env
# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-very-secure-secret-key-here

# Database
DATABASE_URL=sqlite:///app.db
# For PostgreSQL: postgresql://user:password@localhost/dbname

# Redis/Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# File Upload
MAX_CONTENT_LENGTH=16777216  # 16MB
UPLOAD_FOLDER=app/static/uploads

# Security Settings
WTF_CSRF_ENABLED=True
WTF_CSRF_TIME_LIMIT=3600
```

### Production Configuration
For production deployment, update:
- Use PostgreSQL instead of SQLite
- Set strong SECRET_KEY
- Configure proper Redis instance
- Set up SSL/HTTPS
- Configure file storage (AWS S3)

## Running the Application

### Development Mode
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Flask app
python run.py

# Terminal 3: Start Celery worker
python celery_worker.py
```

### Production Mode
```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:app

# With Celery
celery -A app.celery worker --loglevel=info
```

## Troubleshooting

### Common Issues

**1. dlib installation fails:**
```bash
# Windows: Install Visual C++ Build Tools first
# Linux: sudo apt-get install build-essential cmake
# macOS: xcode-select --install
```

**2. face_recognition installation fails:**
```bash
# Install dlib first
pip install dlib
pip install face_recognition
```

**3. Redis connection error:**
```bash
# Start Redis server
redis-server

# Check if Redis is running
redis-cli ping
```

**4. Database migration errors:**
```bash
# Reset migrations
rm -rf migrations/
flask db init
flask db migrate
flask db upgrade
```

**5. Permission errors on uploads:**
```bash
# Create upload directories
mkdir -p app/static/uploads
mkdir -p app/static/thumbnails
chmod 755 app/static/uploads
```

### Performance Optimization

**For better performance:**
1. Use PostgreSQL instead of SQLite
2. Configure Redis with persistence
3. Use SSD storage for video files
4. Increase worker processes for Celery
5. Configure proper logging levels

### Security Hardening

**Before production:**
1. Change default SECRET_KEY
2. Enable HTTPS/SSL
3. Configure firewall rules
4. Set up proper authentication
5. Regular security updates

## Verification

Test the installation:
```bash
# Check if all services are running
curl http://localhost:5000  # Flask app
redis-cli ping             # Redis
celery -A app.celery inspect active  # Celery workers
```

## Support

If you encounter issues:
1. Check the logs in `logs/` directory
2. Verify all dependencies are installed
3. Ensure Redis is running
4. Check file permissions
5. Review the error messages carefully

For additional help, check the project documentation or create an issue in the repository.