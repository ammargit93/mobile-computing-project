import json
import os
from datetime import datetime, timedelta

class SessionManager:
    def __init__(self, session_file='session.json'):
        self.session_file = session_file

    def create_session(self, username, user_type):
        session_data = {
            'username': username,
            'user_type': user_type,
            'expires_at': (datetime.now() + timedelta(days=1)).isoformat()  # Session expires in 1 day
        }
        with open(self.session_file, 'w') as f:
            json.dump(session_data, f)

    def get_session(self):
        """Retrieve the current session data."""
        if not os.path.exists(self.session_file):
            return None
        with open(self.session_file, 'r') as f:
            session_data = json.load(f)
        if datetime.fromisoformat(session_data['expires_at']) < datetime.now():
            self.clear_session()  # Clear expired session
            return None
        return session_data

    def clear_session(self):
        """Clear the current session."""
        if os.path.exists(self.session_file):
            os.remove(self.session_file)