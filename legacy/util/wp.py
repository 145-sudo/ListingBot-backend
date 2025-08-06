import logging
import os

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from woocommerce import API

load_dotenv()

print(f"WP KEY LOADED: {True if os.getenv('WP_CONSUMER_KEY') else False}")
print(f"WP SECRET LOADED: {True if os.getenv('WP_CONSUMER_KEY') else False}")
# Initialize the WooCommerce API client
wcapi = API(
    url="https://stltacticals.com",
    consumer_key=os.getenv("WP_CONSUMER_KEY"),
    consumer_secret=os.getenv("WP_CONSUMER_SECRET"),
    version="wc/v3",
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
