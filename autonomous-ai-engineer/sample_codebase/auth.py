# sample_codebase/auth.py

class Authenticator:
    def __init__(self, user_db):
        self.user_db = user_db

    def login(self, username, password):
        """
        Logs a user in by checking their username and password.
        Returns a success message or raises an error.
        """
        if not self.user_db.user_exists(username):
            raise ValueError("User not found.")
        
        stored_password = self.user_db.get_password(username)
        if stored_password != password:
            raise ValueError("Invalid password.")
            
        return f"Welcome, {username}! Login successful."

    def register(self, username, password):
        """
        Registers a new user if they don't already exist.
        """
        if self.user_db.user_exists(username):
            raise ValueError("Username already taken.")
        
        self.user_db.add_user(username, password)
        return "User registered successfully."