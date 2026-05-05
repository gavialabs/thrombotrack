"""
Seed script to populate the database with demo data
"""
from . import db, create_app
from .models import User

def seed_database():
    """Add demo users to the database"""
    app = create_app()
    
    with app.app_context():
        # Check if users already exist
        if User.query.first():
            print("Database already contains data. Skipping seed.")
            return
        
        # Demo users
        demo_users = [
            User(username='alice', email='alice@example.com'),
            User(username='bob', email='bob@example.com'),
            User(username='charlie', email='charlie@example.com'),
            User(username='diana', email='diana@example.com'),
            User(username='eve', email='eve@example.com'),
        ]
        
        # Add all users
        for user in demo_users:
            db.session.add(user)
        
        # Commit to database
        db.session.commit()
        
        print(f"✓ Successfully seeded database with {len(demo_users)} demo users")

if __name__ == '__main__':
    seed_database()