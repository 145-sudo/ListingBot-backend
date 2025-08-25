import asyncio
import logging
from config import SheetName
from legacy.util.file import load_json_from_dir
from scraper.kroll import scrape_kroll_categories
from scraper.rothco import scrape_rothco_categories
from scraper.ssi import scrape_ssi_categories
from services.db import insert_update_KROLL, insert_update_SSI

async def scrape_save_supplier_products(supplier_name: str):
    """Scrape and save supplier products without blocking"""
    try:
        categories = load_json_from_dir(f"{supplier_name}.json")
        logging.info(f"Fetched {len(categories)} categories of {supplier_name.title()}")

        df = None
        if supplier_name == SheetName.KROLL.value:
            df = await asyncio.to_thread(scrape_kroll_categories, categories)
        elif supplier_name == SheetName.SSI.value:
            df = await asyncio.to_thread(scrape_ssi_categories, categories)
        elif supplier_name == SheetName.ROTCHCO.value:
            df = await asyncio.to_thread(scrape_rothco_categories, categories)
        else:
            logging.error(f"Unknown supplier: {supplier_name}")
            return
            
        if df is not None:
            logging.info(f"Saving {supplier_name} products to database")
            await asyncio.to_thread(save_supplier_data_to_db, supplier_name, df)
            logging.info(f"Finished processing {supplier_name} products")
    except Exception as e:
        logging.error(f"Error processing {supplier_name} products: {e}")
        raise



def save_supplier_data_to_db(supplier_name: str, data):
    """This function would save the fetched data to the database"""
    logging.info(f"Saving {supplier_name} products to database")
    # Here you would implement the logic to insert or update supplier data in your database
    if supplier_name == SheetName.KROLL.value:
        insert_update_KROLL(data)
    elif supplier_name == SheetName.SSI.value:
        insert_update_SSI(data)