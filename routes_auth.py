"""Authentication and user profile routes"""
from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, User
from utils import save_upload_file, delete_file
from config import PROFILE_UPLOAD_FOLDER
import os

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/', methods=['POST', 'GET'])
def index():
    """Home page"""
    return render_template('index.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if 'user_id' in session:
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect('/')
    
    error = None
    username = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = None
        try:
            user = User.query.filter_by(username=username).first()
        except Exception:
            user = None

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['profile_pic'] = user.profile_pic
            session['role'] = user.role
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect('/')
        else:
            error = 'Invalid username or password'

    return render_template('profile/login.html', error=error, username=username)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if 'user_id' in session:
        return redirect('/')
    
    error = None
    success = None
    username = ''
    email = ''
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')
        
        # Validation
        if not username:
            error = 'Username is required'
        elif len(username) < 3:
            error = 'Username must be at least 3 characters'
        elif not password:
            error = 'Password is required'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters'
        elif password != password_confirm:
            error = 'Passwords do not match'
        else:
            # Check if username already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                error = 'Username already taken'
        
        if not error:
            try:
                new_user = User(
                    username=username,
                    email=email or None,
                    role='user'
                )
                new_user.set_password(password)
                db.session.add(new_user)
                db.session.commit()
                success = 'Account created successfully! You can now log in.'
                username = ''
                email = ''
            except Exception:
                db.session.rollback()
                error = 'Error creating account. Please try again.'
    
    return render_template('profile/register.html', error=error, success=success, 
                         username=username, email=email)


@auth_bp.route('/logout')
def logout():
    """User logout"""
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('profile_pic', None)
    session.pop('role', None)
    return redirect('/')


@auth_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    """User profile settings"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        session.pop('username', None)
        return redirect(url_for('auth.login'))

    error = None
    success = None
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        new_email = request.form.get('email', '').strip()
        new_password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        # Validation
        if not new_username:
            error = 'Username cannot be empty'
        else:
            if new_username != user.username:
                existing = User.query.filter_by(username=new_username).first()
                if existing:
                    error = 'That username is already taken'

        if not error and new_password:
            if new_password != password_confirm:
                error = 'Passwords do not match'

        # Handle profile picture upload
        pic_file = request.files.get('profile_pic')
        if pic_file and pic_file.filename:
            pic_filename = save_upload_file(pic_file, PROFILE_UPLOAD_FOLDER, prefix=f'u{user.id}_')
            if pic_filename:
                # Delete previous file if different
                if user.profile_pic and user.profile_pic != pic_filename:
                    delete_file(os.path.join(PROFILE_UPLOAD_FOLDER, user.profile_pic))
                user.profile_pic = pic_filename

        if not error:
            try:
                user.username = new_username
                user.email = new_email or None
                if new_password:
                    user.set_password(new_password)
                db.session.commit()
                session['username'] = user.username
                session['profile_pic'] = user.profile_pic
                success = 'Account updated'
            except Exception:
                db.session.rollback()
                error = 'Could not save changes'

    return render_template('profile/settings.html', user=user, error=error, success=success)
