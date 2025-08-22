import logging
import asyncio
from datetime import datetime

from requests import Session
from config import SheetColumns
from database import get_db
from models.kroll import KrollProduct
from models.rothco import RothcoProduct
from models.ssi import SsiProduct
from models.wordpress import WordPressProduct
from fastapi import HTTPException
from legacy.util.wp import get_store_products
from dotenv import load_dotenv
import os
from woocommerce import API

from services.sheet import get_attribute

load_dotenv()


WP_CONSUMER_KEY = os.getenv("WP_CONSUMER_KEY")
WP_CONSUMER_SECRET = os.getenv("WP_CONSUMER_SECRET")
# WP_CONSUMER_KEY = os.getenv("WP_CONSUMER_KEY")
# WP_CONSUMER_SECRET = os.getenv("WP_CONSUMER_SECRET")


print(f"WP KEY LOADED: {True if os.getenv('WP_CONSUMER_KEY') else False}")
print(f"WP SECRET LOADED: {True if os.getenv('WP_CONSUMER_KEY') else False}")
# Initialize the WooCommerce API client

ENV = 'TEST not'

if ENV == "TEST":
    wcapi = API(
        url="http://listing-bot.test/",
        consumer_key="ck_f7c614f81a52cf9933d09245a373474a176aeb8e",
        consumer_secret="cs_3692035422f9e985dca09c3a17ac99b7680b690f",
        version="wc/v3",
        timeout=30,
    )
else:
        wcapi = API(
        url="https://stltacticals.com",
        consumer_key=os.getenv("WP_CONSUMER_KEY"),
        consumer_secret=os.getenv("WP_CONSUMER_SECRET"),
        version="wc/v3",
        timeout=30,
    )


# Create a background task for periodic sync
async def get_wp_to_db(interval: int = 300):
    try:
        import pandas as pd

        products = pd.read_csv("products.csv")
        print("loaded products file")

        # Get database session
        from database import get_db

        db_gen = get_db()
        db = next(db_gen)  # Get the actual session from the generator

        try:
            for _, product in products.iterrows():
                try:
                    # Map only available columns from CSV to WordPressProduct
                    wp_product = WordPressProduct(
                        wp_id=product["id"],
                        name=product["name"],
                        description=product["description"],
                        price=float(product["price"]),
                        sku=str(product["sku"]),
                        status=product["status"],
                        stock_status=product["stock_status"],
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
                        if "UNIQUE constraint failed: wordpress_products.sku" in str(
                            e
                        ):
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
                        status_code=500, detail=f"Error processing product: {str(e)}"
                    )
            print(f"Successfully synced {len(products)} products")
            return True

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error processing products: {str(e)}"
            )

        finally:
            try:
                next(db_gen)  # This will trigger the generator's cleanup
            except StopIteration:
                pass  # Generator is already exhausted
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error syncing WordPress products: {str(e)}"
        )
    # await asyncio.sleep(interval)


def supplier_product_to_wp_product(supplier_product: KrollProduct | SsiProduct | RothcoProduct) -> WordPressProduct:
    """ Convert a supplier product to a WordPressProduct instance """
    wp_product = WordPressProduct(
        name=supplier_product.name,
        description=supplier_product.description,
        price=float(supplier_product.price),    # TODO: sale price
        sku=str(supplier_product.sku),
        status="draft",  # Default status
        stock_status="instock" if supplier_product.stock > 0 else "outofstock",
        stock_quantity=supplier_product.stock,
        categories=str(
            [
                {"name": supplier_product.category},
                {"name": supplier_product.sub_category},
            ]
        ),
        images=str([{"src": img} for img in supplier_product.images.split(",")])
        if supplier_product.images
        else "[]",
        supplier=supplier_product.__tablename__.upper(),
        supplier_sku=supplier_product.sku,
    )

    # Get database session
    from database import get_db

    db_gen = get_db()
    db = next(db_gen)  # Get the actual session from the generator

    # Check for existing product by SKU
    existing_product = db.query(WordPressProduct).filter_by(sku=wp_product.sku).first()
    if existing_product:
        print(f"Product with SKU {wp_product.sku} already exists. Skipping.")
        return existing_product

    # Add to database
    db.add(wp_product)

    try:
        # Commit all changes
        db.commit()
    except Exception as e:
        logging.error(f"Error committing product {wp_product.sku}: {e}")
        db.rollback()

    return wp_product

def sync_to_woocommerce(data: KrollProduct | SsiProduct | RothcoProduct, db: Session):
    logging.info("Adding product to woocommerce")

    # for row in data[1:]:

    # SKU BY SUPPLIER
    sku = data.sku
    price = data.price
    name = data.name
    description = data.description
    category = data.category
    sub_category = data.sub_category
    stock = data.stock
    status = "draft"
    # status = (
    #     "publish"
    #     if row.get(get_attribute(supplier_name, SheetColumns.LIST_DELIST), "")
    #     == "List"
    #     else "draft"
    # )

    logging.info(f"Syncing product sku:{sku} name:{name}")
    products = wcapi.get(f"products?sku={sku}").json()
    logging.debug(f"WP product response: {products}")
    
    create_data = {
        "name": f"demo-{name}",
        "type": "simple",
        "sku": f"demo-{sku}",
        # "sku": sku,
        "regular_price": str(price),
        "stock_quantity": stock,
        "status": status,
        "description": description,
        "categories": (
            [{"name": category}, {"name": sub_category}]
            if category and sub_category
            else []
        ),
    }
    response = wcapi.post("products", create_data).json()
    logging.debug(f"WP product create response: {response}")
    logging.info(f"Created new product {sku}")

    try:
        data.is_synced = True
        data.last_synced = datetime.now()
        db.add(data)
        db.commit()
        db.refresh(data)
    except Exception as e:
        db.rollback()
        raise e


def update_product_in_woocommerce(product_id, data):
    """
    Updates a product in WooCommerce.
    """
    logging.info(f"Updating product {product_id} in WooCommerce.")
    try:
        response = wcapi.put(f"products/{product_id}", data).json()
        logging.debug(f"WP product update response: {response}")
        logging.info(f"Successfully updated product {product_id}")
        return response
    except Exception as e:
        logging.error(f"Error updating product {product_id} in WooCommerce: {e}")
        return None

async def sync_and_update_products(interval: int = 300):
    """
    Periodically syncs supplier products with WordPress products,
    updating stock if necessary.
    """
    while True:
        logging.info("Starting product sync and update process.")
        db_gen = get_db()
        db = next(db_gen)
        try:
            # Get all supplier products
            kroll_products = db.query(KrollProduct).all()
            ssi_products = db.query(SsiProduct).all()
            rothco_products = db.query(RothcoProduct).all()
            supplier_products = kroll_products + ssi_products + rothco_products
            logging.info(f"Found {len(supplier_products)} total supplier products.")
            logging.info(f"({len(kroll_products)} Kroll, {len(ssi_products)} SSI, {len(rothco_products)} Rothco)")


            # Get all WordPress products and create a SKU-based lookup
            wp_products_list = db.query(WordPressProduct).all()
            wp_products = {p.sku: p for p in wp_products_list}
            logging.info(f"Found {len(wp_products)} WordPress products.")

            for supplier_product in supplier_products:
                if supplier_product.sku in wp_products:
                    wp_product = wp_products[supplier_product.sku]
                    
                    logging.debug(f"Comparing SKU {supplier_product.sku}: "
                                 f"Supplier (Price: {supplier_product.price}, Stock: {supplier_product.stock}) vs "
                                 f"WP Stock: {wp_product.stock_status})")

                    # Check for price or stock changes
                    # price_changed = float(wp_product.price) != float(supplier_product.price)
                    stock_changed = wp_product.stock_status != supplier_product.stock # Assuming supplier_product.stock holds the stock quantity

                    if stock_changed:
                        logging.info(f"Changes detected for SKU {supplier_product.sku}. Updating.")

                        # Prepare update data for WooCommerce
                        update_data = {}
                        if stock_changed:
                            wp_product.stock_status = supplier_product.stock
                            update_data["stock_quantity"] = supplier_product.stock

                        # Update in database
                        db.add(wp_product)
                        db.commit()
                        db.refresh(wp_product)
                        logging.info(f"Updated SKU {supplier_product.sku} in the database.")

                        # Update in WooCommerce
                        update_product_in_woocommerce(wp_product.wp_id, update_data)
                else:
                    logging.debug(f"SKU {supplier_product.sku} from supplier not found in WordPress products.")


        except Exception as e:
            logging.error(f"An error occurred during the sync and update process: {e}")
            db.rollback()
        finally:
            try:
                next(db_gen)  # Close the session
            except StopIteration:
                pass
        
        logging.info(f"Sync and update process finished. Waiting for {interval} seconds.")
        await asyncio.sleep(interval)
