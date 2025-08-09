from models.wordpress import WordPressProduct
from fastapi import HTTPException
from legacy.util.wp import get_store_products
from dotenv import load_dotenv
import os
load_dotenv()

WP_CONSUMER_KEY = os.getenv("WP_CONSUMER_KEY")
WP_CONSUMER_SECRET = os.getenv("WP_CONSUMER_SECRET")

# Create a background task for periodic sync
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