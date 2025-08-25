import logging
import asyncio
from datetime import datetime

from requests import Session
from config import SheetName
from database import get_db
from models.kroll import KrollProduct
from models.rothco import RothcoProduct
from models.ssi import SsiProduct
from models.wordpress import WordPressProduct
from fastapi import HTTPException
from dotenv import load_dotenv
from woocommerce import API
import pandas as pd
import numpy as np
import os


load_dotenv()


WP_CONSUMER_KEY = os.getenv("WP_CONSUMER_KEY")
WP_CONSUMER_SECRET = os.getenv("WP_CONSUMER_SECRET")


print(f"WP KEY LOADED: {True if os.getenv('WP_CONSUMER_KEY') else False}")
print(f"WP SECRET LOADED: {True if os.getenv('WP_CONSUMER_KEY') else False}")
# Initialize the WooCommerce API client

ENV = os.getenv("ENV", "PROD")

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


# Get total products count from woocommerce
def get_total_products_count(wcapi) -> int:
    # Fetch products (up to 100 per page)
    response = wcapi.get("products", params={"per_page": 10})

    # Get total products count from response headers
    total_products = int(response.headers.get("X-WP-Total", 0))

    logging.info(f"Total products count: {total_products}")
    return total_products


# Get products from woocommerce
def get_products(wcapi, page: int = 1, per_page: int = 100) -> list:
    products = []
    try:
        response = wcapi.get("products", params={"page": page, "per_page": per_page})
        products = response.json()
        return products
    except Exception as e:
        logging.error(f"Error fetching products on Page:{page}, Per_Page:{per_page}")
        logging.error(e)
        return []


# Get all products from woocommerce
def get_all_products(wcapi, total_products: int) -> list:
    """
    Fetch all products from WooCommerce, handling pagination and retries.

    Args:
        wcapi: WooCommerce API client.
        total_products: Total number of products to fetch.

    Returns:
        List of all product dicts.
    """
    products = []
    page = 1
    per_page = 100
    max_tries = 3
    fetched = 0
    total_pages = (total_products // per_page) + (1 if total_products % per_page else 0)
    for _ in range(total_pages + 1):  # +1 to ensure all pages are covered
        tries = 0
        p = []
        while tries < max_tries:
            try:
                p = get_products(wcapi, page, per_page)
                break
            except Exception as e:
                tries += 1
                logging.error(
                    f"Attempt {tries} failed to fetch products on Page:{page}, Per_Page:{per_page}: {e}"
                )
                if tries == max_tries:
                    logging.error(
                        f"Max retries reached for Page:{page}, Per_Page:{per_page}"
                    )
        if not p:
            logging.warning(f"No products fetched for Page:{page}")
            break
        products.extend(p)
        fetched += len(p)
        logging.info(
            f"Fetched {fetched} products so far, Page:{page}, Per_Page:{per_page}"
        )
        if fetched >= total_products:
            break
        page += 1
    return products


# Clean products list to dataframe
def clean_products(products: list) -> pd.DataFrame:
    # converting to dataframe
    df = pd.DataFrame(products)

    remove_columns = [
        "meta_data",
        "_links",
        "related_ids",
        "grouped_products",
        "variations",
        "default_attributes",
        "attributes",
        "tags",
        "categories",
        "images",
        "upsell_ids",
        "downloads",
        "dimensions",
        "cross_sell_ids",
    ]

    for column in remove_columns:
        if column in df.columns:
            df = df.drop(columns=[column])

    # p = df.iloc[0].to_dict()
    # for col in p:
    #     if type(p[col]) not in [str, int, bool]:
    #         logging.info(col)
    #         logging.info(type(p[col]))
    #         # break

    # replace nan with None
    df = df.replace({np.nan: None})

    return df


# Get store products from woocommerce
def get_store_products() -> pd.DataFrame:
    total_products = get_total_products_count(wcapi)
    products = get_all_products(wcapi, total_products)
    df = clean_products(products)
    return df


# Create a background task for periodic sync
async def get_wp_to_db(interval: int = 300):
    while True:
        try:
            # import pandas as pd

            # # Keep NaN values as NaN, don't convert them to a default string
            # products_df = pd.read_csv("products.csv")
            # # products_df = pd.read_csv("products.csv", keep_default_na=False, na_values=[''])
            # print("loaded products file")

            products_df = get_store_products()

            # Get database session
            from database import get_db

            db_gen = get_db()
            db = next(db_gen)

            try:
                # Get all WordPress products and create a wp_id-based lookup
                wp_products_list = db.query(WordPressProduct).all()
                wp_products = {p.wp_id: p for p in wp_products_list}
                logging.info(f"Found {len(wp_products)} WordPress products.")

                for _, product_data in products_df.iterrows():
                    # # Skip rows where SKU is NaN or empty
                    # if pd.isna(product_data["sku"]) or product_data["sku"] == '':
                    #     logging.warning(f"Skipping product with empty SKU. WP_ID: {product_data.get('id')}, Name: {product_data.get('name')}")
                    #     continue

                    wp_id = product_data["id"]

                    # Check if product exists
                    if wp_id in wp_products:
                        wp_product = wp_products[wp_id]

                        # Check for changes in price and stock
                        price_changed = wp_product.price != product_data["price"]
                        stock_changed = (
                            wp_product.stock_status != product_data["stock_status"]
                        )

                        if price_changed or stock_changed:
                            logging.info(f"Changes detected for wp_id {wp_id}. Updating.")
                            if price_changed:
                                wp_product.price = float(product_data["price"])
                            if stock_changed:
                                wp_product.stock_status = product_data["stock_status"]

                            db.add(wp_product)
                            db.commit()
                        else:
                            pass
                    else:
                        # Product not found, create a new one
                        try:
                            new_wp_product = WordPressProduct(
                                wp_id=product_data["id"],
                                name=product_data["name"],
                                description=product_data["description"],
                                price=product_data["price"],
                                sku=str(product_data["sku"]),
                                status=product_data["status"],
                                stock_status=product_data["stock_status"],
                            )
                            db.add(new_wp_product)
                            db.commit()
                        except Exception as e:
                            db.rollback()
                            if "UNIQUE constraint failed: wordpress_products.sku" in str(e):
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
        await asyncio.sleep(interval)


def supplier_product_to_wp_product(
    db: Session,
    supplier_product: KrollProduct | SsiProduct | RothcoProduct,
    saleprice: float,
    supplier_name: SheetName = None,
) -> WordPressProduct:
    """Convert a supplier product to a WordPressProduct instance"""
    print("supplier name", supplier_name)
    print("supplier name", supplier_name.value if supplier_name else None)
    wp_product = WordPressProduct(
        name=supplier_product.name,
        description=supplier_product.description,
        price=float(saleprice),  # TODO: sale price
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
        # images=str([{"src": img} for img in supplier_product.images.split(",")])
        # if supplier_product.images
        # else "[]",
        # supplier=supplier_product.__tablename__.upper(),
        supplier=supplier_name,
        supplier_sku=supplier_product.sku,
    )

    # Get database session
    # from database import get_db

    # db_gen = get_db()
    # db = next(db_gen)  # Get the actual session from the generator

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


def sync_to_woocommerce(
    data: KrollProduct | SsiProduct | RothcoProduct | WordPressProduct, db: Session
):
    logging.info("Adding product to woocommerce")

    # for row in data[1:]:
    if isinstance(data, WordPressProduct):
        category = data.categories
        stock = data.stock_quantity
    else:
        category = data.category
        stock = data.stock
    # SKU BY SUPPLIER
    sku = data.sku
    price = data.price
    name = data.name
    description = data.description
    # category = data.categories
    # sub_category = data.sub_category
    # stock = data.stock
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
        # "categories": (
        # [{"name": category}, {"name": sub_category}]
        # if category and sub_category
        # else []
        # ),
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


def process_updates(db, supplier_products, wp_products, supplier_name):
    for supplier_product in supplier_products:
        if supplier_product.sku in wp_products:
            wp_product = wp_products[supplier_product.sku]
            # Compare updated_at timestamps
            if supplier_product.updated_at > wp_product.updated_at:
                logging.info(
                    f"Supplier product {supplier_product.sku} from {supplier_name} is newer. Updating stock."
                )

                update_data = {"stock_quantity": supplier_product.stock}

                # Update in WooCommerce
                update_product_in_woocommerce(wp_product.wp_id, update_data)

                # Update in database
                wp_product.stock_quantity = supplier_product.stock
                wp_product.stock_status = (
                    "instock" if supplier_product.stock > 0 else "outofstock"
                )
                db.add(wp_product)
                db.commit()
                db.refresh(wp_product)
                logging.info(f"Updated SKU {supplier_product.sku} in the database.")
            else:
                logging.debug(
                    f"SKU {supplier_product.sku} from {supplier_name} is not newer than WordPress product. Skipping."
                )
        else:
            logging.debug(
                f"SKU {supplier_product.sku} from {supplier_name} not found in WordPress products."
            )


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
            # Define suppliers and their corresponding models and filter values
            suppliers = [
                ("Kroll", KrollProduct, SheetName.KROLL.value),
                ("SSI", SsiProduct, SheetName.SSI.value),
                ("Rothco", RothcoProduct, "Rothco"),
            ]

            for name, model, filter_val in suppliers:
                # Query supplier products
                supplier_products = db.query(model).all()
                all_wp_products = db.query(WordPressProduct).all()
                wp_products_list = [
                    p
                    for p in all_wp_products
                    if p.supplier is not None and p.supplier.value == filter_val
                ]

                # if none , then move to next loop
                if not wp_products_list:
                    logging.info(
                        f"No {name} WordPress products found to sync. Skipping."
                    )
                    continue
                # Map WordPress products by SKU
                wp_products = {p.sku: p for p in wp_products_list}

                logging.info(
                    f"Found {len(supplier_products)} {name} supplier products."
                )
                logging.info(
                    f"Found {len(wp_products)} {name} WordPress products to sync."
                )

                process_updates(db, supplier_products, wp_products, name)

        except Exception as e:
            logging.error(f"An error occurred during the sync and update process: {e}")
            db.rollback()
        finally:
            try:
                next(db_gen)  # Close the session
            except StopIteration:
                pass

        logging.info(
            f"Sync and update process finished. Waiting for {interval} seconds."
        )
        await asyncio.sleep(interval)
