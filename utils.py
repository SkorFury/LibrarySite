"""Utility functions"""
import os
from werkzeug.utils import secure_filename
from config import ALLOWED_EXTENSIONS


def allowed_file(filename: str) -> bool:
    """Check if uploaded file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_upload_file(file, upload_folder: str, prefix: str = '') -> str:
    """
    Save uploaded file to folder with unique name.
    
    Args:
        file: FileStorage object from request.files
        upload_folder: Path to folder where file should be saved
        prefix: Prefix for filename (e.g., 'u' for user, 'b' for book)
    
    Returns:
        Filename if saved successfully, None otherwise
    """
    if not file or not file.filename:
        return None
    
    if not allowed_file(file.filename):
        return None
    
    from time import time
    filename = secure_filename(file.filename)
    filename = f"{prefix}{int(time())}_{filename}"
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    return filename


def delete_file(filepath: str) -> bool:
    """Delete a file if it exists"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception:
        pass
    return False
