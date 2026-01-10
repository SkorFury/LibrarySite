from flask import Flask, render_template, url_for, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Disable default SQLite file DB; we only use the bound users DB.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'


app.config['SQLALCHEMY_BINDS'] = {
    'users': 'sqlite:///users.db'
}
db = SQLAlchemy(app)

# sessions (simple dev secret - replace with secure env var for production)
app.secret_key = 'dev-secret-change-me'
# profile uploads
app.config['PROFILE_UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'images', 'profiles')
os.makedirs(app.config['PROFILE_UPLOAD_FOLDER'], exist_ok=True)

# news uploads folder and model
app.config['NEWS_UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'images', 'jaunumi')
os.makedirs(app.config['NEWS_UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# expose frequently used helpers to all templates (avoids UndefinedError for datetime)
@app.context_processor
def inject_globals():
    return {'datetime': datetime}

# --- User model stored in a separate users.db file ---
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='user', nullable=False)  # 'user' or 'administrator'

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f'<User {self.username}>'
    # optional path to profile picture file stored under static/images/profiles
    profile_pic = db.Column(db.String(255), nullable=True)
    # optional email
    email = db.Column(db.String(255), nullable=True)


# News model for storing posts on /jaunumi
class News(db.Model):
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationship to User
    author = db.relationship('User', backref='news_posts', foreign_keys=[user_id])

    def __repr__(self):
        return f'<News {self.title}>'
    

@app.route('/', methods=['POST', 'GET'])
def index():
    news = News.query.order_by(News.date_created.desc()).all()
    return render_template('index.html', news=news)


@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to next page or home
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
            # set session values (simpler than using full Flask-Login for now)
            session['user_id'] = user.id
            session['username'] = user.username
            session['profile_pic'] = user.profile_pic
            session['role'] = user.role
            # Redirect back to the page they came from, or home
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect('/')
        else:
            error = 'Invalid username or password'

    return render_template('profile/login.html', error=error, username=username)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('profile_pic', None)
    session.pop('role', None)
    return redirect('/')


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    # Simple session guarded settings page
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        # session invalid
        session.pop('user_id', None)
        session.pop('username', None)
        return redirect(url_for('login'))

    error = None
    success = None
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        new_email = request.form.get('email', '').strip()
        new_password = request.form.get('password', '')
        password_confirm = request.form.get('password_confirm', '')

        # basic validation
        if not new_username:
            error = 'Username cannot be empty'
        else:
            # if username changed, ensure it's unique
            if new_username != user.username:
                existing = User.query.filter_by(username=new_username).first()
                if existing:
                    error = 'That username is already taken'

        if not error and new_password:
            if new_password != password_confirm:
                error = 'Passwords do not match'

        # handle profile picture upload
        pic_file = request.files.get('profile_pic')
        if pic_file and pic_file.filename:
            if allowed_file(pic_file.filename):
                filename = secure_filename(pic_file.filename)
                # ensure unique filename by prefixing with user id
                filename = f'u{user.id}_' + filename
                dst = os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], filename)
                pic_file.save(dst)
                # delete previous file if present and different
                if user.profile_pic and user.profile_pic != filename:
                    try:
                        old = os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], user.profile_pic)
                        if os.path.exists(old):
                            os.remove(old)
                    except Exception:
                        pass
                user.profile_pic = filename

        if not error:
            # apply changes
            user.username = new_username
            user.email = new_email or None
            if new_password:
                user.set_password(new_password)
            try:
                db.session.commit()
                session['username'] = user.username
                session['profile_pic'] = user.profile_pic
                success = 'Account updated'
            except Exception as e:
                db.session.rollback()
                error = 'Could not save changes'

    return render_template('profile/settings.html', user=user, error=error, success=success)

@app.route('/jaunumi', methods=['GET', 'POST'])
def jaunumi():
    if request.method == 'POST':
        # Debug: print session contents
        print(f"DEBUG: Session contents: {dict(session)}")
        print(f"DEBUG: user_id in session: {'user_id' in session}")
        
        # Must be logged in to create news
        if 'user_id' not in session:
            print("DEBUG: Redirecting to login - no user_id in session")
            return redirect(url_for('login', next=request.url))
        
        # Ensure session has role key (for backward compatibility with old sessions)
        if 'role' not in session:
            user = User.query.get(session['user_id'])
            if user:
                session['role'] = user.role
                print(f"DEBUG: Added role to session: {user.role}")
            else:
                print("DEBUG: User not found, redirecting to login")
                return redirect(url_for('login', next=request.url))

        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        image_file = request.files.get('image')
        image_filename = None

        if image_file and image_file.filename:
            if allowed_file(image_file.filename):
                from time import time
                fname = secure_filename(image_file.filename)
                fname = f"n{int(time())}_{fname}"
                dst = os.path.join(app.config['NEWS_UPLOAD_FOLDER'], fname)
                image_file.save(dst)
                image_filename = fname

        if not title:
            return 'Title is required', 400

        new_item = News(title=title, content=content or None, image=image_filename, user_id=session.get('user_id'))
        try:
            db.session.add(new_item)
            db.session.commit()
            return redirect(url_for('jaunumi'))
        except Exception as e:
            db.session.rollback()
            return f'Problem saving news: {e}', 500

    news = News.query.order_by(News.date_created.desc()).all()
    return render_template('jaunumi.html', news=news)


@app.route('/news/<int:id>/delete')
def delete_news(id):
    # Must be logged in
    if 'user_id' not in session:
        return redirect(url_for('login', next=request.url))

    news = News.query.get_or_404(id)
    
    # Check if user is admin or owns this news item
    if session.get('role') != 'administrator' and news.user_id != session.get('user_id'):
        return 'Unauthorized', 403

    # Delete image file if exists
    if news.image:
        image_path = os.path.join(app.config['NEWS_UPLOAD_FOLDER'], news.image)
        if os.path.exists(image_path):
            os.remove(image_path)

    try:
        db.session.delete(news)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f'Problem deleting news: {e}', 500

    return redirect(url_for('jaunumi'))


@app.route('/news/<int:id>/edit', methods=['GET', 'POST'])
def edit_news(id):
    # Must be logged in
    if 'user_id' not in session:
        return redirect(url_for('login', next=request.url))

    news = News.query.get_or_404(id)
    
    # Check if user is admin or owns this news item
    if session.get('role') != 'administrator' and news.user_id != session.get('user_id'):
        return 'Unauthorized', 403

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        image_file = request.files.get('image')

        if not title:
            return 'Title is required', 400

        news.title = title
        news.content = content or None

        # Handle image upload
        if image_file and image_file.filename:
            if allowed_file(image_file.filename):
                # Delete old image if exists
                if news.image:
                    old_image_path = os.path.join(app.config['NEWS_UPLOAD_FOLDER'], news.image)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)

                # Save new image
                from time import time
                fname = secure_filename(image_file.filename)
                fname = f"n{int(time())}_{fname}"
                dst = os.path.join(app.config['NEWS_UPLOAD_FOLDER'], fname)
                image_file.save(dst)
                news.image = fname

        try:
            db.session.commit()
            return redirect(url_for('jaunumi'))
        except Exception as e:
            db.session.rollback()
            return f'Problem updating news: {e}', 500

    return render_template('jaunumi/edit_news.html', news=news)


@app.route('/news/<int:id>')
def view_news(id):
    news = News.query.get_or_404(id)
    return render_template('jaunumi/view_news.html', news=news)


@app.route('/admin/users', methods=['GET', 'POST'])
def admin_users():
    # Admin only
    if session.get('role') != 'administrator':
        return redirect(url_for('login', next=request.url))

    error = None
    success = None
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create':
            # Create new user
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '').strip()
            role = request.form.get('role', 'user').strip()
            
            if not username:
                error = 'Username is required'
            elif not password:
                error = 'Password is required'
            else:
                # Check if username already exists
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
                    except Exception as e:
                        db.session.rollback()
                        error = f'Error creating user: {str(e)}'
        
        elif action == 'edit':
            # Edit existing user
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
                    # Check username uniqueness if changed
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
            except Exception as e:
                db.session.rollback()
                error = f'Error updating user: {str(e)}'
        
        elif action == 'delete':
            # Delete user (except administrators)
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
                        # Delete profile picture if exists
                        if user.profile_pic:
                            try:
                                pic_path = os.path.join(app.config['PROFILE_UPLOAD_FOLDER'], user.profile_pic)
                                if os.path.exists(pic_path):
                                    os.remove(pic_path)
                            except Exception:
                                pass
                        
                        db.session.delete(user)
                        db.session.commit()
                        success = f'User "{username}" deleted successfully'
                except Exception as e:
                    db.session.rollback()
                    error = f'Error deleting user: {str(e)}'
    
    # Get all users
    users = User.query.all()
    return render_template('profile/admin_users.html', users=users, error=error, success=success)


if __name__ == '__main__':
    # ensure DBs exist and the users table has an admin user seeded
    with app.app_context():
        # create all tables (including binds) if they don't exist
        db.create_all()

        # ensure users table has profile_pic column — add column if missing (simple sqlite migration)
        try:
            # check columns
            conn = db.get_engine(app, bind='users').raw_connection()
            cur = conn.cursor()
            cur.execute("PRAGMA table_info('user');")
            cols = [r[1] for r in cur.fetchall()]
            if 'profile_pic' not in cols:
                cur.execute("ALTER TABLE user ADD COLUMN profile_pic TEXT;")
                conn.commit()
        except Exception:
            # ignore if bind/table doesn't exist yet
            pass

        # ensure news table has user_id column — add column if missing
        try:
            conn = db.get_engine(app, bind='users').raw_connection()
            cur = conn.cursor()
            cur.execute("PRAGMA table_info('news');")
            cols = [r[1] for r in cur.fetchall()]
            if 'user_id' not in cols:
                cur.execute("ALTER TABLE news ADD COLUMN user_id INTEGER;")
                conn.commit()
                print('Added user_id column to news table')
        except Exception as e:
            # ignore if bind/table doesn't exist yet
            pass

        # ensure user table has email column — add column if missing
        try:
            conn = db.get_engine(app, bind='users').raw_connection()
            cur = conn.cursor()
            cur.execute("PRAGMA table_info('user');")
            cols = [r[1] for r in cur.fetchall()]
            if 'email' not in cols:
                cur.execute("ALTER TABLE user ADD COLUMN email TEXT;")
                conn.commit()
                print('Added email column to user table')
        except Exception as e:
            # ignore if bind/table doesn't exist yet
            pass

        # ensure user table has role column — add column if missing
        try:
            conn = db.get_engine(app, bind='users').raw_connection()
            cur = conn.cursor()
            cur.execute("PRAGMA table_info('user');")
            cols = [r[1] for r in cur.fetchall()]
            if 'role' not in cols:
                cur.execute("ALTER TABLE user ADD COLUMN role TEXT DEFAULT 'user';")
                conn.commit()
                print('Added role column to user table')
        except Exception as e:
            # ignore if bind/table doesn't exist yet
            pass

        # seed admin user in users.db (separate bind) -- disabled per request to avoid auto-creation
        # try:
        #     admin = User.query.filter_by(username='admin').first()
        #     if not admin:
        #         admin = User(username='admin', role='administrator')
        #         admin.set_password('admin')
        #         db.session.add(admin)
        #         db.session.commit()
        #         print('Seeded users.db with admin/admin')
        #     elif admin.role != 'administrator':
        #         # Ensure admin has administrator role
        #         admin.role = 'administrator'
        #         db.session.commit()
        #         print('Updated admin user role to administrator')
        # except Exception as e:
        #     # if the users bind/table doesn't exist, create_all should have created it above
        #     print('Create/seed user failed:', e)

    app.run(debug=True)