from sqlalchemy.orm import Session
from models.user import User
from database import engine, SessionLocal
from auth import get_password_hash
import sys

# Create database tables
from database import Base
Base.metadata.create_all(bind=engine)

def seed_user():
    db = SessionLocal()
    try:
        # Check if there are any existing users
        existing_user = db.query(User).first()
        if existing_user:
            print("Database already has users. Skipping seed.")
            return

        # Create initial user
        initial_user = User(
            email="admin@admin.com",
            hashed_password=get_password_hash("admin123"),
            is_active=True
        )

        db.add(initial_user)
        db.commit()
        print("Successfully seeded initial user")
    except Exception as e:
        db.rollback()
        print(f"Error seeding user: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_user()
