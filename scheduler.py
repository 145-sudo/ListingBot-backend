import asyncio
# from rocketry import Rocketry
# from rocketry.conds import every

from services.wordpress import get_wp_to_db, sync_and_update_products
from services.suppliers import scrape_save_supplier_products
from config import SheetName

# app = Rocketry(execution="async")


# WordPress sync tasks (every 15 minutes)
# @app.task(every("15 minutes"))
async def wordpress_sync():
    await get_wp_to_db()


# @app.task(every("15 minutes"))
async def wordpress_update():
    await sync_and_update_products()


# Supplier scraping tasks (every 30 minutes)
# @app.task(every("30 minutes"))
async def kroll_sync():
    await scrape_save_supplier_products(SheetName.KROLL.value)


# @app.task(every("30 minutes"))
async def ssi_sync():
    await scrape_save_supplier_products(SheetName.SSI.value)


async def tasks():
    await asyncio.gather(
        wordpress_sync(),
        wordpress_update(),
        kroll_sync(),
        ssi_sync(),
    )


def run_tasks():
    asyncio.run(tasks())
