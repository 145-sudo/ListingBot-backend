from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from database import Base
from datetime import datetime

class WordPressProduct(Base):
    __tablename__ = "wordpress_products"

    id = Column(Integer, primary_key=True, index=True)
    wp_id = Column(Integer, unique=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Float)
    sku = Column(String, unique=True, index=True)
    status = Column(String)
    stock_status = Column(String)
    stock_quantity = Column(Integer)
    categories = Column(String)  # JSON string of categories
    images = Column(String)     # JSON string of image URLs
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced = Column(DateTime, default=datetime.utcnow)
    is_synced = Column(Boolean, default=False)
