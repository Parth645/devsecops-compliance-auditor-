
# Sample application with compliance issues
import os
import hashlib
import sqlite3
import requests

# ISSUE: Hardcoded password
DATABASE_PASSWORD = "admin123"  
API_KEY = "sk-1234567890abcdef"

class UserManager:
    def __init__(self):
        # ISSUE: Hardcoded database connection
        self.db_conn = sqlite3.connect("users.db")
        
    def authenticate_user(self, username, password):
        # ISSUE: Plain text password comparison
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        return self.db_conn.execute(query).fetchone()
    
    def store_personal_data(self, user_data):
        # ISSUE: No encryption for personal data
        personal_info = {
            'ssn': user_data['ssn'],
            'email': user_data['email'],
            'phone': user_data['phone']
        }
        # Store without encryption
        with open('user_data.txt', 'a') as f:
            f.write(str(personal_info) + '\n')
    
    def log_access(self, user_id, action):
        # GOOD: Audit logging implemented
        log_entry = f"{user_id}: {action} at {os.getenv('TIMESTAMP')}"
        with open('audit.log', 'a') as f:
            f.write(log_entry + '\n')

def make_api_call(endpoint):
    # ISSUE: No proper authentication
    headers = {'Authorization': f'Bearer {API_KEY}'}
    response = requests.get(endpoint, headers=headers, verify=False)  # ISSUE: SSL verification disabled
    return response.json()

if __name__ == "__main__":
    manager = UserManager()
    # Process users without proper validation
