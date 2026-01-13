# Library Management System

This is a comprehensive library management system built with Flask and SQLAlchemy that implements all required functionalities for managing a library's book collection and user loans.

## Features

### 1. Book Management (Grāmatu reģistrācija)
- **Add Books**: Administrators can add new books with details:
  - Title (Nosaukums)
  - Author (Autors)
  - ISBN
  - Publisher (Izdevējs)
  - Year (Gads)
  - Category (Kategorija)
  - Number of copies (Kopiju skaits)
  - Description (Apraksts)

- **Search Books**: Search by title, author, or ISBN
- **Filter by Category**: Browse books by category
- **Edit/Delete Books**: Administrators can update or remove books

### 2. User Management (Lietotāju reģistrācija)
- User registration and login system
- User profiles with customizable settings
- Two user roles:
  - Regular users (can borrow and reserve books)
  - Administrators (can manage books, users, loans, and reservations)

### 3. Loan System (Aizņemšanas sistēma)
- **Borrow Books**: Users can borrow available books
- **Loan Period**: 14-day loan period
- **Return Books**: Mark books as returned
- **Track Status**: Active, returned, and overdue loans
- **My Loans**: Users can view their current and past loans
- **Admin Loan Management**: Administrators can view and manage all loans

### 4. Reservation System (Rezervācijas sistēma)
- **Reserve Books**: Users can reserve books when all copies are borrowed
- **Reservation Expiry**: Reservations expire after 7 days
- **Auto-fulfillment**: Reservations are automatically marked as fulfilled when user borrows the book
- **My Reservations**: Users can view and cancel their reservations
- **Admin Reservation Management**: Administrators can view all pending reservations

## Data Structure and Models

### Database Schema

#### Book Model
```python
- id (Primary Key)
- title (String, required)
- author (String, required)
- isbn (String, unique, required)
- publisher (String, optional)
- year (Integer, optional)
- copies_total (Integer, default: 1)
- copies_available (Integer, default: 1)
- category (String, optional)
- description (Text, optional)
- date_added (DateTime, default: now)
```

#### User Model
```python
- id (Primary Key)
- username (String, unique, required)
- password_hash (String, required)
- email (String, optional)
- role (String, default: 'user')
- profile_pic (String, optional)
```

#### Loan Model
```python
- id (Primary Key)
- book_id (Foreign Key -> Book)
- user_id (Foreign Key -> User)
- loan_date (DateTime, default: now)
- due_date (DateTime, required)
- return_date (DateTime, nullable)
- status (String: 'active', 'returned', 'overdue')
```

#### Reservation Model
```python
- id (Primary Key)
- book_id (Foreign Key -> Book)
- user_id (Foreign Key -> User)
- reservation_date (DateTime, default: now)
- expiry_date (DateTime, nullable)
- status (String: 'pending', 'fulfilled', 'cancelled')
```

### Relationships
- Book ↔ Loan (One-to-Many)
- User ↔ Loan (One-to-Many)
- Book ↔ Reservation (One-to-Many)
- User ↔ Reservation (One-to-Many)

## Data Storage System

### Technology Choice: SQL Database (SQLite)

**Chosen System**: SQLite database with SQLAlchemy ORM

**Reasons for choosing SQL over alternatives**:

1. **Data Consistency**: 
   - ACID properties ensure data integrity
   - Foreign key constraints maintain referential integrity
   - Transactions prevent data corruption

2. **Relationship Management**:
   - Natural support for complex relationships (users, books, loans, reservations)
   - Efficient JOIN operations for querying related data
   - Easy to maintain data consistency across tables

3. **Scalability**:
   - Can easily migrate to larger SQL databases (PostgreSQL, MySQL) as the library grows
   - Indexed queries provide fast search performance
   - Support for concurrent users

4. **Query Flexibility**:
   - Complex queries with filtering, sorting, and aggregation
   - Full-text search capabilities
   - Easy to generate reports and statistics

**Comparison with alternatives**:

| Feature | SQL (SQLite) | Text Files | NoSQL |
|---------|-------------|------------|-------|
| Data Integrity | ✅ Strong | ❌ Weak | ⚠️ Moderate |
| Relationships | ✅ Native | ❌ Manual | ⚠️ Complex |
| Query Performance | ✅ Fast | ❌ Slow | ✅ Fast |
| Consistency | ✅ ACID | ❌ None | ⚠️ Eventually |
| Schema Enforcement | ✅ Yes | ❌ No | ❌ No |
| Learning Curve | ⚠️ Moderate | ✅ Easy | ⚠️ Moderate |

## Data Structure Implementation

### Programming Language: Python

**Key data structures used**:

1. **Classes (OOP)**:
   - Book, User, Loan, Reservation classes using SQLAlchemy ORM
   - Encapsulation of data and behavior
   - Inheritance from `db.Model` base class

2. **Dictionary/Hash Table**:
   - Session management uses dictionaries
   - Fast O(1) lookup for user data
   - Form data handling with request.form dictionary

3. **Lists/Arrays**:
   - Query results returned as lists
   - Efficient iteration for displaying collections
   - Support for filtering and sorting

### Key Functions

**Book Management**:
```python
def add_book()        # Add new book to library
def edit_book(id)     # Update book information
def delete_book(id)   # Remove book from catalog
def view_book(id)     # Display book details
def library()         # Search and browse books
```

**Loan Management**:
```python
def borrow_book(id)   # Create new loan
def return_book(id)   # Mark book as returned
def my_loans()        # View user's loans
def admin_loans()     # Admin view of all loans
```

**Reservation Management**:
```python
def reserve_book(id)         # Create reservation
def cancel_reservation(id)   # Cancel reservation
def my_reservations()        # View user's reservations
def admin_reservations()     # Admin view of all reservations
```

## Search and Performance

### Search Implementation
- **Text Search**: Using SQL LIKE operator for flexible matching
- **Filter by Category**: Exact match on category field
- **Combined Search**: Search across multiple fields (title, author, ISBN)
- **Performance**: Indexed columns for fast lookups

### Data Access Patterns
- **O(1)** - User session lookup (dictionary)
- **O(log n)** - Book search by ISBN (indexed)
- **O(n)** - Category filtering (table scan)
- **O(n log n)** - Sorted book listings

## Installation and Setup

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run the Application**:
```bash
python app.py
```

3. **Access the Site**:
   - Open browser to `http://127.0.0.1:5000`
   - Default port: 5000

4. **Create Admin User**:
   - First user should be created with administrator role
   - Use the admin panel to create additional users

## Usage

### For Users:
1. Register/Login to your account
2. Browse the library catalog
3. Borrow available books (14-day loan period)
4. Reserve books when unavailable
5. View your active loans and reservations
6. Return books when finished

### For Administrators:
1. Add new books to the library
2. Edit book information
3. Manage user accounts
4. Monitor all loans and overdue items
5. View all reservations
6. Delete books (only if no active loans)

## Technical Details

### Session Management
- Flask sessions store user authentication state
- Secure password hashing with Werkzeug
- Role-based access control

### Database Persistence
- SQLite database file: `instance/users.db`
- Data persists between sessions
- Automatic table creation on first run
- Migration support for schema changes

### Error Handling
- Input validation on all forms
- Duplicate ISBN prevention
- Active loan checks before deletion
- Overdue loan detection and marking

## Future Enhancements

Possible improvements:
- Email notifications for due dates
- Barcode scanning for ISBN
- Book cover images
- Reading recommendations
- Statistics dashboard
- Export functionality
- Mobile app integration

## Author
Developed as part of a library management system project demonstrating data structures, database management, and web application development.
