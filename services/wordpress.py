import logging
from config import SheetColumns
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


print(f"WP KEY LOADED: {True if os.getenv('WP_CONSUMER_KEY') else False}")
print(f"WP SECRET LOADED: {True if os.getenv('WP_CONSUMER_KEY') else False}")
# Initialize the WooCommerce API client
wcapi = API(
    url="https://stltacticals.com",
    consumer_key=os.getenv("WP_CONSUMER_KEY"),
    consumer_secret=os.getenv("WP_CONSUMER_SECRET"),
    version="wc/v3",
)


# Create a background task for periodic sync
def get_wp_to_db(interval: int = 300):
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


def sync_to_woocommerce(data: KrollProduct | SsiProduct | RothcoProduct):
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
    # if len(products) > 0 and products[0].get("data", {}).get("status", None) != 401:
    #     logging.info("product already exists")
    #     product_id = products[0]["id"]
    #     # Check if it's a variation
    #     if row["Type"] == "variation":
    #         parent_id = row["Parent ID"]
    #         variations = wcapi.get(
    #             f"products/{parent_id}/variations?sku={sku}"
    #         ).json()
    #         if variations:
    #             variant_id = variations[0]["id"]
    #             update_data = {
    #                 "regular_price": str(price),
    #                 "stock_quantity": stock,
    #                 "status": status,
    #             }
    #             wcapi.put(
    #                 f"products/{parent_id}/variations/{variant_id}", update_data
    #             ).json()
    #     else:
    #         logging.info("product is updating")
    #         update_data = {
    #             "regular_price": str(price),
    #             "stock_quantity": stock,
    #             "status": status,
    #         }
    #         wcapi.put(f"products/{product_id}", update_data).json()
    #     logging.info(f"Updated {row['Type']} {sku}")
    # else:
    #     logging.info("product not found, adding as new.")
    #     # Handle new product/variation creation as needed
    #     if row.get("Type", "") == "variation":
    #         parent_id = row["Parent ID"]
    #         # Create new variation
    #         create_data = {
    #             "sku": f"demo-{sku}",
    #             "regular_price": str(price),
    #             "stock_quantity": stock,
    #             "status": status,
    #             "description": f"demo-{description}",
    #         }
    #         wcapi.post(f"products/{parent_id}/variations", create_data).json()
    #         logging.info(f"Created new variation {sku} under parent {parent_id}")
    #     else:
    
    # Above commented code is for variation handling
    # Create new product
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
