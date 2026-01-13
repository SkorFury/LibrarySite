"""
Script to create an administrator user for the library system
Run this script once to create your first admin account
"""
from app import app, db, User

def create_admin():
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            print("Admin user already exists!")
            print("Username: admin")
            return
        
        # Create new admin user
        print("Creating administrator account...")
        admin = User(
            username='admin',
            email='admin@library.local',
            role='administrator'
        )
        admin.set_password('admin123')  # Change this password after first login!
        
        db.session.add(admin)
        db.session.commit()
        
        print("\n✅ Administrator account created successfully!")
        print("=" * 50)
        print("Username: admin")
        print("Password: admin123")
        print("=" * 50)
        print("\n⚠️  IMPORTANT: Change this password after first login!")
        print("Go to Settings > Change Password")
        print("\nYou can now:")
        print("1. Add books to the library")
        print("2. Create user accounts")
        print("3. Manage loans and reservations")

if __name__ == '__main__':
    create_admin()
