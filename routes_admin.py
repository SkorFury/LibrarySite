"""Admin routes for user and system management"""
from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, User
from utils import delete_file
from config import PROFILE_UPLOAD_FOLDER
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/users', methods=['GET', 'POST'])
def users():
    """Manage users (admin only)"""
    if session.get('role') != 'administrator':
        return redirect(url_for('auth.login', next=request.url))

    error = None
    success = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            role = request.form.get('role', 'user').strip()
            
            if not username:
                error = 'Username is required'
            elif not password:
                error = 'Password is required'
            else:
                existing = User.query.filter_by(username=username).first()
                if existing:
                    error = f'Username "{username}" already exists'
                else:
                    try:
                        new_user = User(username=username, email=email or None, role=role)
                        new_user.set_password(password)
                        db.session.add(new_user)
                        db.session.commit()
                        success = f'User "{username}" created successfully'
                    except Exception:
                        db.session.rollback()
                        error = f'Error creating user'
        
        elif action == 'edit':
            user_id = request.form.get('user_id')
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            role = request.form.get('role', 'user').strip()
            
            try:
                user = User.query.get(user_id)
                if not user:
                    error = 'User not found'
                else:
                    if username != user.username:
                        existing = User.query.filter_by(username=username).first()
                        if existing:
                            error = f'Username "{username}" is already taken'
                    
                    if not error:
                        user.username = username
                        user.email = email or None
                        user.role = role
                        if password:
                            user.set_password(password)
                        db.session.commit()
                        success = f'User "{username}" updated successfully'
            except Exception:
                db.session.rollback()
                error = f'Error updating user'
        
        elif action == 'delete':
            user_id = request.form.get('user_id')
            user_to_delete = User.query.get(user_id)
            
            if user_to_delete and user_to_delete.role == 'administrator':
                error = 'Cannot delete administrator user'
            else:
                try:
                    user = User.query.get(user_id)
                    if not user:
                        error = 'User not found'
                    else:
                        username = user.username
                        if user.profile_pic:
                            delete_file(os.path.join(PROFILE_UPLOAD_FOLDER, user.profile_pic))
                        
                        db.session.delete(user)
                        db.session.commit()
                        success = f'User "{username}" deleted successfully'
                except Exception:
                    db.session.rollback()
                    error = f'Error deleting user'
    
    users_list = User.query.all()
    return render_template('profile/admin_users.html', users=users_list, error=error, success=success)
