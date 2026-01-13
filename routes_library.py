"""Library routes for books, loans, and reservations"""
from flask import Blueprint, render_template, request, redirect, url_for, session
from models import db, Book, Loan, Reservation
from datetime import datetime, timedelta
from utils import save_upload_file, delete_file
from config import BOOK_UPLOAD_FOLDER
import os

library_bp = Blueprint('library', __name__, url_prefix='/library')


@library_bp.route('/')
def index():
    """Main library page with search and filter"""
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    
    query = Book.query
    
    if search:
        search_filter = f'%{search}%'
        query = query.filter(
            db.or_(
                Book.title.like(search_filter),
                Book.author.like(search_filter),
                Book.isbn.like(search_filter)
            )
        )
    
    if category:
        query = query.filter(Book.category == category)
    
    books = query.order_by(Book.title).all()
    categories = db.session.query(Book.category).distinct().filter(Book.category.isnot(None)).all()
    categories = [c[0] for c in categories]
    
    return render_template('library/books.html', books=books, categories=categories, 
                         search=search, selected_category=category)


@library_bp.route('/book/<int:id>')
def view_book(id):
    """View book details"""
    book = Book.query.get_or_404(id)
    
    user_loan = None
    user_reservation = None
    if 'user_id' in session:
        user_loan = Loan.query.filter_by(
            book_id=id, 
            user_id=session['user_id'],
            status='active'
        ).first()
        user_reservation = Reservation.query.filter_by(
            book_id=id,
            user_id=session['user_id'],
            status='pending'
        ).first()
    
    return render_template('library/view_book.html', book=book, 
                         user_loan=user_loan, user_reservation=user_reservation)


# ===== BOOK MANAGEMENT (Admin) =====

@library_bp.route('/book/add', methods=['GET', 'POST'])
def add_book():
    """Add new book (admin only)"""
    if session.get('role') != 'administrator':
        return redirect(url_for('auth.login', next=request.url))
    
    error = None
    success = None
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        isbn = request.form.get('isbn', '').strip()
        publisher = request.form.get('publisher', '').strip()
        year = request.form.get('year', '').strip()
        copies = request.form.get('copies', '1').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        cover_file = request.files.get('cover_image')
        
        if not title:
            error = 'Title is required'
        elif not author:
            error = 'Author is required'
        elif not isbn:
            error = 'ISBN is required'
        else:
            existing = Book.query.filter_by(isbn=isbn).first()
            if existing:
                error = f'Book with ISBN {isbn} already exists'
            else:
                cover_filename = None
                if cover_file and cover_file.filename:
                    cover_filename = save_upload_file(cover_file, BOOK_UPLOAD_FOLDER, prefix='b')
                
                if not error:
                    try:
                        year_int = int(year) if year else None
                        copies_int = int(copies) if copies else 1
                        
                        new_book = Book(
                            title=title,
                            author=author,
                            isbn=isbn,
                            publisher=publisher or None,
                            year=year_int,
                            copies_total=copies_int,
                            copies_available=copies_int,
                            category=category or None,
                            description=description or None,
                            cover_image=cover_filename
                        )
                        db.session.add(new_book)
                        db.session.commit()
                        success = f'Book "{title}" added successfully'
                    except ValueError:
                        error = 'Invalid year or copies value'
                    except Exception:
                        db.session.rollback()
                        error = f'Error adding book'
    
    return render_template('library/add_book.html', error=error, success=success)


@library_bp.route('/book/<int:id>/edit', methods=['GET', 'POST'])
def edit_book(id):
    """Edit book (admin only)"""
    if session.get('role') != 'administrator':
        return redirect(url_for('auth.login', next=request.url))
    
    book = Book.query.get_or_404(id)
    error = None
    success = None
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        isbn = request.form.get('isbn', '').strip()
        publisher = request.form.get('publisher', '').strip()
        year = request.form.get('year', '').strip()
        copies = request.form.get('copies', '1').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        cover_file = request.files.get('cover_image')
        
        if not title:
            error = 'Title is required'
        elif not author:
            error = 'Author is required'
        elif not isbn:
            error = 'ISBN is required'
        else:
            existing = Book.query.filter(Book.isbn == isbn, Book.id != id).first()
            if existing:
                error = f'Book with ISBN {isbn} already exists'
            else:
                try:
                    year_int = int(year) if year else None
                    copies_int = int(copies) if copies else 1
                    
                    # Handle cover image upload
                    if cover_file and cover_file.filename:
                        cover_filename = save_upload_file(cover_file, BOOK_UPLOAD_FOLDER, prefix='b')
                        if cover_filename:
                            if book.cover_image:
                                delete_file(os.path.join(BOOK_UPLOAD_FOLDER, book.cover_image))
                            book.cover_image = cover_filename
                    
                    book.title = title
                    book.author = author
                    book.isbn = isbn
                    book.publisher = publisher or None
                    book.year = year_int
                    book.category = category or None
                    book.description = description or None
                    
                    borrowed = book.copies_total - book.copies_available
                    book.copies_total = copies_int
                    book.copies_available = max(0, copies_int - borrowed)
                    
                    db.session.commit()
                    success = f'Book "{title}" updated successfully'
                except ValueError:
                    error = 'Invalid year or copies value'
                except Exception:
                    db.session.rollback()
                    error = f'Error updating book'
    
    return render_template('library/edit_book.html', book=book, error=error, success=success)


@library_bp.route('/book/<int:id>/delete')
def delete_book(id):
    """Delete book (admin only)"""
    if session.get('role') != 'administrator':
        return redirect(url_for('auth.login', next=request.url))
    
    book = Book.query.get_or_404(id)
    
    active_loans = Loan.query.filter_by(book_id=id, status='active').count()
    if active_loans > 0:
        return f'Cannot delete book with active loans', 400
    
    try:
        Reservation.query.filter_by(book_id=id).delete()
        Loan.query.filter_by(book_id=id).delete()
        
        if book.cover_image:
            delete_file(os.path.join(BOOK_UPLOAD_FOLDER, book.cover_image))
        
        db.session.delete(book)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return f'Error deleting book', 500
    
    return redirect(url_for('library.index'))


# ===== BORROWING =====

@library_bp.route('/book/<int:id>/borrow', methods=['POST'])
def borrow_book(id):
    """Borrow a book"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login', next=request.url))
    
    book = Book.query.get_or_404(id)
    
    if book.copies_available <= 0:
        return 'No copies available', 400
    
    existing_loan = Loan.query.filter_by(
        book_id=id,
        user_id=session['user_id'],
        status='active'
    ).first()
    
    if existing_loan:
        return 'You already have this book on loan', 400
    
    try:
        loan = Loan(
            book_id=id,
            user_id=session['user_id'],
            due_date=datetime.utcnow() + timedelta(days=14)
        )
        
        book.copies_available -= 1
        
        db.session.add(loan)
        db.session.commit()
        
        reservation = Reservation.query.filter_by(
            book_id=id,
            user_id=session['user_id'],
            status='pending'
        ).first()
        if reservation:
            reservation.status = 'fulfilled'
            db.session.commit()
        
    except Exception:
        db.session.rollback()
        return f'Error borrowing book', 500
    
    return redirect(url_for('library.view_book', id=id))


@library_bp.route('/loan/<int:id>/return', methods=['POST'])
def return_book(id):
    """Return a borrowed book"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login', next=request.url))
    
    loan = Loan.query.get_or_404(id)
    
    if loan.user_id != session['user_id'] and session.get('role') != 'administrator':
        return 'Unauthorized', 403
    
    if loan.status == 'returned':
        return 'Book already returned', 400
    
    try:
        loan.return_date = datetime.utcnow()
        loan.status = 'returned'
        
        book = Book.query.get(loan.book_id)
        book.copies_available += 1
        
        db.session.commit()
    except Exception:
        db.session.rollback()
        return f'Error returning book', 500
    
    return redirect(url_for('library.my_loans'))


@library_bp.route('/loans')
def my_loans():
    """View user's loans"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login', next=request.url))
    
    active_loans = Loan.query.filter_by(
        user_id=session['user_id'],
        status='active'
    ).order_by(Loan.due_date).all()
    
    past_loans = Loan.query.filter_by(
        user_id=session['user_id'],
        status='returned'
    ).order_by(Loan.return_date.desc()).limit(10).all()
    
    for loan in active_loans:
        if loan.due_date < datetime.utcnow() and loan.status == 'active':
            loan.status = 'overdue'
    db.session.commit()
    
    return render_template('library/my_loans.html', active_loans=active_loans, past_loans=past_loans)


@library_bp.route('/admin/loans')
def admin_loans():
    """View all loans (admin only)"""
    if session.get('role') != 'administrator':
        return redirect(url_for('auth.login', next=request.url))
    
    active_loans = Loan.query.filter_by(status='active').order_by(Loan.due_date).all()
    
    for loan in active_loans:
        if loan.due_date < datetime.utcnow():
            loan.status = 'overdue'
    db.session.commit()
    
    active_loans = Loan.query.filter_by(status='active').order_by(Loan.due_date).all()
    overdue_loans = Loan.query.filter_by(status='overdue').order_by(Loan.due_date).all()
    
    return render_template('library/admin_loans.html', 
                         active_loans=active_loans, 
                         overdue_loans=overdue_loans)


# ===== RESERVATIONS =====

@library_bp.route('/book/<int:id>/reserve', methods=['POST'])
def reserve_book(id):
    """Reserve a book"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login', next=request.url))
    
    book = Book.query.get_or_404(id)
    
    existing_reservation = Reservation.query.filter_by(
        book_id=id,
        user_id=session['user_id'],
        status='pending'
    ).first()
    
    if existing_reservation:
        return 'You already have a reservation for this book', 400
    
    existing_loan = Loan.query.filter_by(
        book_id=id,
        user_id=session['user_id'],
        status='active'
    ).first()
    
    if existing_loan:
        return 'You already have this book on loan', 400
    
    try:
        reservation = Reservation(
            book_id=id,
            user_id=session['user_id'],
            expiry_date=datetime.utcnow() + timedelta(days=7)
        )
        
        db.session.add(reservation)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return f'Error creating reservation', 500
    
    return redirect(url_for('library.view_book', id=id))


@library_bp.route('/reservation/<int:id>/cancel', methods=['POST'])
def cancel_reservation(id):
    """Cancel a reservation"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login', next=request.url))
    
    reservation = Reservation.query.get_or_404(id)
    
    if reservation.user_id != session['user_id'] and session.get('role') != 'administrator':
        return 'Unauthorized', 403
    
    try:
        reservation.status = 'cancelled'
        db.session.commit()
    except Exception:
        db.session.rollback()
        return f'Error cancelling reservation', 500
    
    return redirect(url_for('library.my_reservations'))


@library_bp.route('/reservations')
def my_reservations():
    """View user's reservations"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login', next=request.url))
    
    pending_reservations = Reservation.query.filter_by(
        user_id=session['user_id'],
        status='pending'
    ).order_by(Reservation.reservation_date).all()
    
    past_reservations = Reservation.query.filter(
        Reservation.user_id == session['user_id'],
        Reservation.status.in_(['fulfilled', 'cancelled'])
    ).order_by(Reservation.reservation_date.desc()).limit(10).all()
    
    for reservation in pending_reservations:
        if reservation.expiry_date and reservation.expiry_date < datetime.utcnow():
            reservation.status = 'cancelled'
    db.session.commit()
    
    pending_reservations = Reservation.query.filter_by(
        user_id=session['user_id'],
        status='pending'
    ).order_by(Reservation.reservation_date).all()
    
    return render_template('library/my_reservations.html', 
                         pending_reservations=pending_reservations,
                         past_reservations=past_reservations)


@library_bp.route('/admin/reservations')
def admin_reservations():
    """View all reservations (admin only)"""
    if session.get('role') != 'administrator':
        return redirect(url_for('auth.login', next=request.url))
    
    pending_reservations = Reservation.query.filter_by(
        status='pending'
    ).order_by(Reservation.reservation_date).all()
    
    return render_template('library/admin_reservations.html', 
                         pending_reservations=pending_reservations)
