"""Application configuration"""
import os

# Database
SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
SQLALCHEMY_BINDS = {
    'users': 'sqlite:///users.db'
}

# Session
SECRET_KEY = 'dev-secret-change-me'

# Upload folders
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
PROFILE_UPLOAD_FOLDER = os.path.join(BASE_PATH, 'static', 'images', 'profiles')
BOOK_UPLOAD_FOLDER = os.path.join(BASE_PATH, 'static', 'images', 'books')

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}

# Ensure upload directories exist
os.makedirs(PROFILE_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BOOK_UPLOAD_FOLDER, exist_ok=True)
