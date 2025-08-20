from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from database import Base
from datetime import datetime

class KrollProduct(Base):
    __tablename__ = "kroll_products"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, unique=True, index=True)
    item_list_id = Column(Integer, unique=True, index=True)
    item_name = Column(String, index=True)
    item_category = Column(String)
    item_category2 = Column(String)
    item_brand = Column(Float)
    price = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_synced = Column(DateTime, default=datetime.utcnow)
    is_synced = Column(Boolean, default=False)
