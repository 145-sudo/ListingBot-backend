from database import SessionLocal
from models.kroll import KrollProduct

def update_kroll_stock():
    db = SessionLocal()
    try:
        products_to_update = db.query(KrollProduct).all()
        if not products_to_update:
            print("No Kroll products found to update.")
            return

        for product in products_to_update:
            product.stock += 500
        
        db.commit()
        print(f"Successfully updated stock for {len(products_to_update)} Kroll products.")

    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_kroll_stock()
