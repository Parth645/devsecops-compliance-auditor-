
# Configuration with security issues
import os

# ISSUE: Hardcoded credentials
DATABASE_URL = "postgresql://admin:password123@localhost/myapp"
SECRET_KEY = "super-secret-key-that-should-not-be-hardcoded"

# ISSUE: Debug mode enabled in production
DEBUG = True

# Some good practices
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# ISSUE: Weak encryption
ENCRYPTION_KEY = "12345678"  # Too short for proper encryption
