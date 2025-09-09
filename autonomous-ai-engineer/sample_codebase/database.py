# sample_codebase/database.py

class UserDatabase:
    def __init__(self):
        self._users = {} # In-memory storage for simplicity

    def user_exists(self, username):
        """Checks if a user is in the database."""
        return username in self._users

    def get_password(self, username):
        """Retrieves a user's password."""
        return self._users.get(username)

    def add_user(self, username, password):
        """Adds a new user and their password."""
        if self.user_exists(username):
            return False
        self._users[username] = password
        return True