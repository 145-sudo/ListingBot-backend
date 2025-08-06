import logging

from config import SheetName, SheetColumns
from util.sheet import get_attribute
from scraper.ssi import scrape_ssi_categories
from scraper.kroll import scrape_kroll_categories
from scraper.rothco import scrape_rothco_categories
from util.gsheet import add_dropdown, update_sheet
from util.wp import wcapi, get_store_products
from util.file import load_json_from_dir


def normalize_name(name):
    return str(name).strip().lower()


def fetch_woocommerce_products(spreadsheet):
    try:
        df = get_store_products()
        update_sheet(spreadsheet, df, sheet_name=SheetName.STORE_PRODUCTS.value)
        logging.info(f"Fetched {len(df)} products from WooCommerce")
    except Exception as e:
        logging.error(f"Error fetching WooCommerce products: {e}")
        raise


def fetch_supplier_products(spreadsheet, supplier_name: str):
    try:
        categories = load_json_from_dir(f"{supplier_name}.json")
        logging.info(f"Fetched {len(categories)} categories of {supplier_name.title()}")

        df = None
        if supplier_name == SheetName.KROLL.value:
            df = scrape_kroll_categories(categories)
        elif supplier_name == SheetName.SSI.value:
            df = scrape_ssi_categories(categories)
        elif supplier_name == SheetName.ROTCHCO.value:
            df = scrape_rothco_categories(categories)
        else:
            logging.error(f"Unknown supplier: {supplier_name}")

        if df is not None:
            update_sheet(spreadsheet, df, sheet_name=supplier_name)
            add_dropdown(supplier_name, "StoreStatus", "-")
            logging.info(
                f"Updated {len(df)} products of {supplier_name.title()} to spreadsheet"
            )
    except Exception as e:
        logging.error(f"Error fetching Kroll products: {e}")
        raise



def sync_to_woocommerce(spreadsheet, supplier_name: str):
    logging.info("Syncing sheet to woocommerce")
    sheet = spreadsheet.worksheet(supplier_name)
    data = sheet.get_all_records()

    if not data:
        return
    if type(data) is not list:
        return
    if len(data) < 2:
        return
    
    print()
    for row in data[1:]:
        print(".", end='')
        # print()
        if row.get(get_attribute(supplier_name, SheetColumns.LIST_DELIST), "").lower() not in ["list", "delist"]:
            continue
        print("O", end='')
        sku = row.get(get_attribute(supplier_name, SheetColumns.SKU), "")
        price = row.get(get_attribute(supplier_name, SheetColumns.PRICE), "")
        name = row.get(get_attribute(supplier_name, SheetColumns.NAME), "")
        description = row.get(get_attribute(supplier_name, SheetColumns.DESCRIPTION), "")
        category = row.get(get_attribute(supplier_name, SheetColumns.CATEGORY), "")
        sub_category = row.get(get_attribute(supplier_name, SheetColumns.SUBCATEGORY), "")
        stock = row.get(get_attribute(supplier_name, SheetColumns.STOCK), "")
        status = (
            "publish"
            if row.get(get_attribute(supplier_name, SheetColumns.LIST_DELIST), "") == "List"
            else "draft"
        )
        
        logging.info(f"Syncing product sku:{sku} name:{name}")
        products = wcapi.get(f"products?sku={sku}").json()
        logging.debug(f"WP product response: {products}")
        if len(products) > 0 and products[0].get('data', {}).get('status', None) != 401:
            logging.info("product already exists")
            product_id = products[0]["id"]
            # Check if it's a variation
            if row["Type"] == "variation":
                parent_id = row["Parent ID"]
                variations = wcapi.get(
                    f"products/{parent_id}/variations?sku={sku}"
                ).json()
                if variations:
                    variant_id = variations[0]["id"]
                    update_data = {
                        "regular_price": str(price),
                        "stock_quantity": stock,
                        "status": status,
                    }
                    wcapi.put(
                        f"products/{parent_id}/variations/{variant_id}", update_data
                    ).json()
            else:
                logging.info("product is updating")
                update_data = {
                    "regular_price": str(price),
                    "stock_quantity": stock,
                    "status": status,
                }
                wcapi.put(f"products/{product_id}", update_data).json()
            logging.info(f"Updated {row['Type']} {sku}")
        else:
            logging.info("product not found, adding as new.")
            # Handle new product/variation creation as needed
            if row.get("Type", "") == "variation":
                parent_id = row["Parent ID"]
                # Create new variation
                create_data = {
                    "sku": f"demo-{sku}",
                    "regular_price": str(price),
                    "stock_quantity": stock,
                    "status": status,
                    "description": f"demo-{description}",
                }
                wcapi.post(f"products/{parent_id}/variations", create_data).json()
                logging.info(f"Created new variation {sku} under parent {parent_id}")
            else:
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
                    "categories": [{"name": category}, {"name": sub_category}]
                    if category and sub_category
                    else [],
                }
                response = wcapi.post("products", create_data).json()
                logging.debug(f"WP product create response: {response}")
                logging.info(f"Created new product {sku}")


# Monitor sheet changes
def monitor_sheet_changes(spreadsheet):
    try:
        supplier_sheets = [sheet.value for sheet in SheetName][1:]
        for supplier in supplier_sheets:
            logging.info(f"Syncing sheet: {supplier}")
            sync_to_woocommerce(spreadsheet, supplier)
        logging.info("Checked for sheet changes")
    except Exception as e:
        logging.error(f"Error monitoring sheet changes: {e}")
        raise
