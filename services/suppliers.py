import asyncio
import logging
from config import SheetName
from legacy.util.file import load_json_from_dir
from scraper.kroll import scrape_kroll_categories
from scraper.rothco import scrape_rothco_categories
from scraper.ssi import scrape_ssi_categories
from services.db import insert_update_KROLL, insert_update_SSI

async def scrape_save_supplier_products(supplier_name: str, interval: int = 300):
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
            # Update the table with this data of suuplier
            pass
        
        logging.info(f"Saving {supplier_name} products to database")
        # Save the data to the database
        save_supplier_data_to_db(supplier_name, df)
    except Exception as e:
        logging.error(f"Error fetching Kroll products: {e}")
        raise
    await asyncio.sleep(interval)



def save_supplier_data_to_db(supplier_name: str, data):
    """This function would save the fetched data to the database"""
    logging.info(f"Saving {supplier_name} products to database")
    # Here you would implement the logic to insert or update supplier data in your database
    if supplier_name == SheetName.KROLL.value:
        insert_update_KROLL(data)
    elif supplier_name == SheetName.SSI.value:
        insert_update_SSI(data)