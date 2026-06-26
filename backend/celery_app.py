"""
Celery application configuration for the compliance auditor.
Handles background task queue setup and async processing.
"""

import os
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Celery configuration from environment variables
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")
CELERY_TASK_TIMEOUT = int(os.getenv("CELERY_TASK_TIMEOUT", "300"))  # 5 minutes
CELERY_TASK_MAX_RETRIES = int(os.getenv("CELERY_TASK_MAX_RETRIES", "3"))

# Create Celery app
celery_app = Celery(
    "compliance_auditor",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

# Configure Celery settings
celery_app.conf.update(
    # Broker and backend
    broker_url=CELERY_BROKER_URL,
    result_backend=CELERY_RESULT_BACKEND,
    
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=CELERY_TASK_TIMEOUT * 2,  # Hard limit
    task_soft_time_limit=CELERY_TASK_TIMEOUT,  # Soft limit
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "retry_on_timeout": True,
    },
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Task routing (if needed in future)
    task_routes={
        "background_tasks.scan_repository_async": {"queue": "scans"},
        "background_tasks.webhook_event_handler": {"queue": "webhooks"},
    },
    
    # Beat schedule (periodic tasks) - to be extended
    beat_schedule={
        # Periodic task examples can be added here
    },
)


# Optional: Define a task class for common settings
class CallbackTask(celery_app.Task):
    """Custom task class with error handling and callbacks."""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Success callback - runs after task completes successfully."""
        print(f"✓ Task {task_id} succeeded with result: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Failure callback - runs after task fails."""
        print(f"✗ Task {task_id} failed with exception: {exc}")


celery_app.Task = CallbackTask

if __name__ == "__main__":
    celery_app.start()
