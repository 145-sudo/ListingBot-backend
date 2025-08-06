import httpx
from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from models.wordpress import WordPressProduct
import asyncio
import json
from fastapi import HTTPException
from legacy.util.wp import get_store_products
from dotenv import load_dotenv
import os
load_dotenv()

WP_CONSUMER_KEY = os.getenv("WP_CONSUMER_KEY")
WP_CONSUMER_SECRET = os.getenv("WP_CONSUMER_SECRET")


class WordPressService:
    def __init__(self, db: Session):
        self.db = db
        self.base_url = "https://your-wordpress-site.com/wp-json/wc/v3"
        self.headers = {
            "Authorization": f"Basic {WP_CONSUMER_KEY}:{WP_CONSUMER_SECRET}"
        }

    async def fetch_products(self) -> List[Dict]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/products",
                    headers=self.headers,
                    params={"per_page": 100, "page": 1}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error fetching WordPress products: {str(e)}"
            )

    def create_product(self, product_data: Dict) -> WordPressProduct:
        product = WordPressProduct(
            wp_id=product_data.get("id"),
            name=product_data.get("name"),
            description=product_data.get("description"),
            price=product_data.get("price"),
            sku=product_data.get("sku"),
            status=product_data.get("status"),
            stock_status=product_data.get("stock_status"),
            stock_quantity=product_data.get("stock_quantity"),
            categories=json.dumps(product_data.get("categories", [])),
            images=json.dumps(product_data.get("images", [])),
            is_synced=True
        )
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update_product(self, wp_id: int, product_data: Dict) -> Optional[WordPressProduct]:
        product = self.db.query(WordPressProduct).filter(
            WordPressProduct.wp_id == wp_id
        ).first()
        if product:
            for key, value in product_data.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            product.updated_at = datetime.utcnow()
            product.last_synced = datetime.utcnow()
            product.is_synced = True
            self.db.commit()
            self.db.refresh(product)
        return product

    def sync_products(self):
        try:
            products = asyncio.run(self.fetch_products())
            for product_data in products:
                existing_product = self.db.query(WordPressProduct).filter(
                    WordPressProduct.wp_id == product_data["id"]
                ).first()
                if existing_product:
                    self.update_product(product_data["id"], product_data)
                else:
                    self.create_product(product_data)
            return True
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error syncing WordPress products: {str(e)}"
            )

    def get_products(self, skip: int = 0, limit: int = 100) -> List[WordPressProduct]:
        return self.db.query(WordPressProduct).offset(skip).limit(limit).all()

    def get_product(self, wp_id: int) -> Optional[WordPressProduct]:
        return self.db.query(WordPressProduct).filter(
            WordPressProduct.wp_id == wp_id
        ).first()

    def delete_product(self, wp_id: int) -> bool:
        product = self.db.query(WordPressProduct).filter(
            WordPressProduct.wp_id == wp_id
        ).first()
        if product:
            self.db.delete(product)
            self.db.commit()
            return True
        return False

# Create a background task for periodic sync
async def periodic_sync(db: Session, interval: int = 300):  # 5 minutes by default
    service = WordPressService(db)
    while True:
        try:
            await service.sync_products()
            print(f"WordPress products synced at {datetime.utcnow()}")
        except Exception as e:
            print(f"Error syncing WordPress products: {str(e)}")
        await asyncio.sleep(interval)


def get_wp_to_db(interval: int = 300):
    try:
        import pandas as pd
        products = pd.read_csv("products.csv")
        print('loaded products file')
        
        # Get database session
        from database import get_db
        db_gen = get_db()
        db = next(db_gen)  # Get the actual session from the generator
        
        try:
            for _, product in products.iterrows():
                try:
                    # Map only available columns from CSV to WordPressProduct
                    wp_product = WordPressProduct(
                        wp_id=product['id'],
                        name=product['name'],
                        description=product['description'],
                        price=float(product['price']),
                        sku=str(product['sku']),
                        status=product['status'],
                        stock_status=product['stock_status'],
                        # created_at=product['date_created'],
                        # updated_at=product['date_modified']
                    )
                    
                    # Add to database
                    db.add(wp_product)
                    
                    try:
                        # Commit all changes
                        db.commit()
                    except Exception as e:
                        db.rollback()
                        if 'UNIQUE constraint failed: wordpress_products.sku' in str(e):
                            print(f"Skipping duplicate product: {wp_product.sku}")
                            continue
                        else:
                            print("skip product already exists")
                            # raise HTTPException(
                            #     status_code=500,
                            #     detail=f"Error processing product: {str(e)}"
                            # )
                except Exception as e:
                    db.rollback()
                    raise HTTPException(
                        status_code=500,
                        detail=f"Error processing product: {str(e)}"
                    )
            print(f"Successfully synced {len(products)} products")
            return True
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error processing products: {str(e)}"
            )
            
        finally:
            try:
                next(db_gen)  # This will trigger the generator's cleanup
            except StopIteration:
                pass  # Generator is already exhausted
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error syncing WordPress products: {str(e)}"
        )
        # await asyncio.sleep(interval)