from pandas import DataFrame
from models.kroll import KrollProduct
from database import SessionLocal
from models.ssi import SsiProduct
from services.sheet import get_attribute
from config import SheetName, SheetColumns
import logging

def insert_update_KROLL(data: DataFrame):
    logging.info("Inserting or updating Kroll products in the database")

    # DF columns
    logging.info(f"DataFrame columns: {data.columns.tolist()}")

    session = SessionLocal()
    try:
        updated = 0
        new = 0
        for index, row in data.iterrows():
            sku = row[get_attribute(SheetName.KROLL.value, SheetColumns.SKU)]
            existing_product = session.query(KrollProduct).filter_by(sku=sku).first()

            if existing_product:
                updated += 1 
                existing_product.price = row.get(get_attribute(SheetName.KROLL.value, SheetColumns.PRICE))
                existing_product.stock = row.get(get_attribute(SheetName.KROLL.value, SheetColumns.STOCK))
            else:
                new += 1 
                product = KrollProduct(
                    sku=sku,
                    name=row.get(get_attribute(SheetName.KROLL.value, SheetColumns.NAME), None),
                    description=row.get(get_attribute(SheetName.KROLL.value, SheetColumns.DESCRIPTION), None),
                    price=row.get(get_attribute(SheetName.KROLL.value, SheetColumns.PRICE), None),
                    category=row.get(get_attribute(SheetName.KROLL.value, SheetColumns.CATEGORY), None),
                    sub_category=row.get(get_attribute(SheetName.KROLL.value, SheetColumns.SUBCATEGORY), None),
                )
                session.add(product)
        logging.info(f"Updated {updated} products, added {new} new products.")
        logging.info(f"Total products processed: {updated + new}")
        session.commit()
    except Exception as e:
        session.rollback()
        print(e)
        logging.error(f"Error inserting or updating Kroll products: {e}", exc_info=True)
    finally:
        session.close()


def insert_update_SSI(data: DataFrame):
    pass
    
