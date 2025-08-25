from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from config import SheetName
from models.ssi import SsiProduct
from database import get_db
from services.wordpress import supplier_product_to_wp_product, sync_to_woocommerce

router = APIRouter()
              

# ssi endpoints
@router.get("/ssi/")
async def get_ssi_products(
    page: int = 1,
    limit: int = 100,
    sort: str = "id",
    order: str = "asc",
    db: Session = Depends(get_db),
):
    skip = (page - 1) * limit
    # Validate sort field
    if not hasattr(SsiProduct, sort):
        raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort}")
    sort_column = getattr(SsiProduct, sort)
    # Determine order
    if order.lower() == "desc":
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()
    products = (
        db.query(SsiProduct).order_by(sort_column).offset(skip).limit(limit).all()
    )
    total = db.query(SsiProduct).count()
    return {
        "data": products,
        "total": total,
        "page": page,
        "limit": limit,
        "sort": sort,
        "order": order,
    }


@router.get("/ssi/{id}")
async def get_ssi_product(id: int, db: Session = Depends(get_db)):
    
    product = db.query(SsiProduct).filter(SsiProduct.id == id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="ssi product not found")
    return product

@router.post("/ssi/{id}/{price}")
async def upload_kroll_product(id: int, price: float, db: Session = Depends(get_db)):
    product = db.query(SsiProduct).filter(SsiProduct.id == id).first()
    """ Upload a specific kroll product to WooCommerce """
    product = db.query(SsiProduct).filter(SsiProduct.id == id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="kroll product not found")
    # Saving supplier product in DB
    wp_product = supplier_product_to_wp_product(db, product, price, SheetName.KROLL)
    # Syncing to WooCommerce Store
    if wp_product:
        sync_to_woocommerce(wp_product, db)
        try:
            product.is_synced = True
            product.last_synced = datetime.now()
            db.add(product)
            db.commit()
            db.refresh(product)
        except Exception as e:
            db.rollback()
    return {"message": "kroll product uploaded successfully", "product": product}



@router.post("/ssi/sync")
async def sync_ssi_products(db: Session = Depends(get_db)):
    # result = periodic_sync(db)
    # return {"message": "ssi products synced successfully", "success": result}
    return {"message": "ssi products synced successfully", "success": True}


@router.delete("/ssi/{id}")
async def delete_ssi_product(id: int, db: Session = Depends(get_db)):
    success = db.query(SsiProduct).filter(SsiProduct.id == id).delete()
    if not success:
        raise HTTPException(status_code=404, detail="ssi product not found")
    return {"message": "ssi product deleted successfully"}

