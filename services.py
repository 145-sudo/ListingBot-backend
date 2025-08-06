from datetime import datetime
from sqlalchemy.orm import Session
from models.products import Product
from typing import List, Optional

class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def get_products(self, skip: int = 0, limit: int = 10) -> List[Product]:
        return self.db.query(Product).offset(skip).limit(limit).all()

    def get_product(self, product_id: int) -> Optional[Product]:
        return self.db.query(Product).filter(Product.id == product_id).first()

    def create_product(self, product: Product) -> Product:
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_product(self, product_id: int, product_data: dict) -> Optional[Product]:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if product:
            for key, value in product_data.items():
                setattr(product, key, value)
            product.last_scraped = datetime.utcnow()
            self.db.commit()
            self.db.refresh(product)
        return product

    def delete_product(self, product_id: int) -> bool:
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if product:
            self.db.delete(product)
            self.db.commit()
            return True
        return False
