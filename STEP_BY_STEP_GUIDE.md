# Step-by-Step Guide to Run Missing Person Finder

## Prerequisites Check
✅ Python 3.11.9 is installed
✅ Project files are present

## Step 1: Install Dependencies
Open Command Prompt in the project folder and run:
```
pip install -r requirements.txt
```

## Step 2: Install Redis (Required for background tasks)
Download and install Redis for Windows:
- Go to: https://github.com/microsoftarchive/redis/releases
- Download Redis-x64-3.0.504.msi
- Install it
- Or use: `winget install Redis.Redis` (if you have winget)

## Step 3: Setup Database
Run the automated setup script:
```
python setup_database.py
```

## Step 4: Start the Application

### Terminal 1 - Start Redis Server
```
redis-server
```
(Keep this terminal open)

### Terminal 2 - Start Flask Application
```
python run.py
```
(Keep this terminal open)

### Terminal 3 - Start Background Worker
```
python celery_worker.py
```
(Keep this terminal open)

## Step 5: Access the Application
Open your web browser and go to:
```
http://127.0.0.1:5000
```

## Troubleshooting
- If Redis fails: Install Redis using the link above
- If database errors: Run `python setup_database.py` again
- If port 5000 is busy: The app will show an error, try closing other applications

## Default Admin Login
- Username: admin
- Email: admin@missingperson.com  
- Password: Admin123!