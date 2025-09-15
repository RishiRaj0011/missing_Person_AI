# Missing Person Finder

A scalable Flask web application for finding missing persons using AI-powered face recognition.

## Setup Instructions

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up Redis (required for Celery):
   - Install Redis server
   - Start Redis: `redis-server`

3. Initialize database:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

4. Start the application:
   ```
   python run.py
   ```

5. Start Celery worker (in separate terminal):
   ```
   python celery_worker.py
   ```

## Features

- Register missing persons with photos and details
- AI-powered face recognition search
- Background processing with Celery
- Responsive web interface
- Database migration support

## Environment Variables

Update `.env` file with your configuration:
- SECRET_KEY: Flask secret key
- DATABASE_URL: Database connection string
- CELERY_BROKER_URL: Redis URL for Celery
- CELERY_RESULT_BACKEND: Redis URL for results