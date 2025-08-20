import asyncio
import logging
from legacy.config import SheetName
from legacy.util.file import load_json_from_dir
from scraper.kroll import scrape_kroll_categories
from scraper.rothco import scrape_rothco_categories
from scraper.ssi import scrape_ssi_categories


async def fetch_only_supplier_products(supplier_name: str, interval: int = 300):
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

    except Exception as e:
        logging.error(f"Error fetching Kroll products: {e}")
        raise
    await asyncio.sleep(interval)

