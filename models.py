"""Database models"""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """User model stored in a separate users.db file"""
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(50), default='user', nullable=False)  # 'user' or 'administrator'
    profile_pic = db.Column(db.String(255), nullable=True)  # Path to profile picture
    email = db.Column(db.String(255), nullable=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f'<User {self.username}>'


class Book(db.Model):
    """Book model - represents books in the library"""
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    publisher = db.Column(db.String(255), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    copies_total = db.Column(db.Integer, default=1, nullable=False)  # Total copies in library
    copies_available = db.Column(db.Integer, default=1, nullable=False)  # Available for loan
    category = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    cover_image = db.Column(db.String(255), nullable=True)  # Path to book cover image
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'


class Loan(db.Model):
    """Loan model - tracks book borrowing/lending"""
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    loan_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=True)  # NULL means still borrowed
    status = db.Column(db.String(20), default='active', nullable=False)  # active, returned, overdue

    # Relationships
    book = db.relationship('Book', backref='loans')
    user = db.relationship('User', backref='loans')

    def __repr__(self):
        return f'<Loan {self.book_id} to User {self.user_id}>'


class Reservation(db.Model):
    """Reservation model - allows users to reserve books"""
    __bind_key__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reservation_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, fulfilled, cancelled
    expiry_date = db.Column(db.DateTime, nullable=True)  # When reservation expires

    # Relationships
    book = db.relationship('Book', backref='reservations')
    user = db.relationship('User', backref='reservations')

    def __repr__(self):
        return f'<Reservation {self.book_id} by User {self.user_id}>'
