from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from database import Base
from datetime import datetime

class SsiProduct(Base):
    __tablename__ = "ssi_products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String, index=True)
    name = Column(String)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    link = Column(String, nullable=True)
    category = Column(String, nullable=True)
    sub_category = Column(String, nullable=True)
    image1 = Column(String, nullable=True)
    image2 = Column(String, nullable=True)
    image3 = Column(String, nullable=True)
    image4 = Column(String, nullable=True)
    image5 = Column(String, nullable=True)
    image6 = Column(String, nullable=True)
    image7 = Column(String, nullable=True)
    image8 = Column(String, nullable=True)
    image9 = Column(String, nullable=True)
    image10 = Column(String, nullable=True)

    # Standard
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced = Column(DateTime, default=datetime.utcnow)
    is_synced = Column(Boolean, default=False)
