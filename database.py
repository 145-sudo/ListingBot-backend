from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os 

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    exit("Error: DATABASE_URL is not set in the environment variables.")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()


def create_tables():
    """Create all database tables."""
    # Import models here to avoid circular imports
    from models.user import User  # noqa: F401
    from models.products import Product  # noqa
    from models.wordpress import WordPressProduct  # noqa

    # Now create all tables
    Base.metadata.create_all(bind=engine)
    print("Tables created/updated")


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
