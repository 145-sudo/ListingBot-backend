from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./listingbot.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()

def create_tables():
    """Create all database tables."""
    # Import models here to avoid circular imports
    from models.user import User
    from models.products import Product
    from models.wordpress import WordPressProduct
    
    # Now create all tables
    Base.metadata.create_all(bind=engine)
    print("Tables created")

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
