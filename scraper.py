import httpx
from datetime import datetime
from typing import List, Dict, Optional
from database import SessionLocal
from models import Product
import asyncio
import json

class ProductScraper:
    def __init__(self):
        self.suppliers = {
            "supplier1": "https://supplier1.com/api/products",
            "supplier2": "https://supplier2.com/api/products"
        }
        self.headers = {
            "User-Agent": "ListingBot/1.0"
        }

    async def fetch_products(self, supplier_url: str) -> List[Dict]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(supplier_url, headers=self.headers)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Error fetching products from {supplier_url}: {str(e)}")
            return []

    async def scrape_and_save(self, user_id: int):
        db = SessionLocal()
        try:
            tasks = []
            for supplier, url in self.suppliers.items():
                tasks.append(self.fetch_products(url))
            
            all_products = await asyncio.gather(*tasks)
            
            for supplier_products in all_products:
                for product in supplier_products:
                    # Create or update product
                    existing_product = db.query(Product).filter(
                        Product.name == product.get("name"),
                        Product.supplier == supplier
                    ).first()
                    
                    if existing_product:
                        # Update existing product
                        existing_product.price = product.get("price")
                        existing_product.description = product.get("description")
                        existing_product.last_scraped = datetime.utcnow()
                    else:
                        # Create new product
                        new_product = Product(
                            name=product.get("name"),
                            description=product.get("description"),
                            price=product.get("price"),
                            supplier=supplier,
                            user_id=user_id
                        )
                        db.add(new_product)
            
            db.commit()
            print(f"Successfully scraped and saved products at {datetime.utcnow()}")
            
        except Exception as e:
            db.rollback()
            print(f"Error scraping products: {str(e)}")
        finally:
            db.close()

async def periodic_scraper(user_id: int, interval: int = 3600):  # Default interval is 1 hour
    scraper = ProductScraper()
    while True:
        await scraper.scrape_and_save(user_id)
        await asyncio.sleep(interval)

# Example usage
if __name__ == "__main__":
    # Get user ID from database
    db = SessionLocal()
    user = db.query(User).first()
    if user:
        asyncio.run(periodic_scraper(user.id))
    db.close()
