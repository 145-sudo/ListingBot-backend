import logging
from time import sleep

import schedule

from config import ENVIRONMENT, SHEET_ID, SheetName
from util.func import (
    fetch_supplier_products,
    fetch_woocommerce_products,
    monitor_sheet_changes,
)
from util.gsheet import get_spreadsheet

# Configure logging to file
logging.basicConfig(
    filename="inventory_sync.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Add logging to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)


# Main function
def main():
    try:
        logging.info("🚀 Launching Inventory Sync - Let the magic begin! 🌟")
        logging.info(f"Environment: {ENVIRONMENT}")

        logging.info(f"Getting spreadsheet: {SHEET_ID}")
        spreadsheet = get_spreadsheet(SHEET_ID)

        # Initial fetch
        logging.info("Fetching WooCommerce products...")
        fetch_woocommerce_products(spreadsheet)
        logging.info("🎉 WooCommerce products fetched and updated successfully!")

        # Fetching suppliers products
        fetch_supplier_products(spreadsheet, SheetName.SSI.value)
        fetch_supplier_products(spreadsheet, SheetName.KROLL.value)
        # fetch_supplier_products(spreadsheet, SheetName.ROTCHCO.value)

        # Schedule periodic sync
        logging.info("Scheduling periodic sync...")
        schedule.every(5).minutes.do(monitor_sheet_changes, spreadsheet)

        while True:
            schedule.run_pending()
            sleep(60)
            logging.info("🔄 Next sync in 60 seconds...")
    except Exception as e:
        logging.error(f"Main loop error: {e}")
        raise


if __name__ == "__main__":
    main()
