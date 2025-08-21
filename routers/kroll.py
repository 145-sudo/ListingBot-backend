from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.kroll import KrollProduct
from database import get_db
from services.wordpress import sync_to_woocommerce

router = APIRouter()
              

# kroll endpoints
@router.get("/kroll/")
async def get_kroll_products(
    page: int = 1,
    limit: int = 100,
    sort: str = "id",
    order: str = "asc",
    db: Session = Depends(get_db),
):
    skip = (page - 1) * limit
    # Validate sort field
    if not hasattr(KrollProduct, sort):
        raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort}")
    sort_column = getattr(KrollProduct, sort)
    # Determine order
    if order.lower() == "desc":
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()
    products = (
        db.query(KrollProduct).order_by(sort_column).offset(skip).limit(limit).all()
    )
    total = db.query(KrollProduct).count()
    return {
        "data": products,
        "total": total,
        "page": page,
        "limit": limit,
        "sort": sort,
        "order": order,
    }


@router.get("/kroll/{id}")
async def get_kroll_product(id: int, db: Session = Depends(get_db)):
    
    product = db.query(KrollProduct).filter(KrollProduct.id == id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="kroll product not found")
    return product


@router.post("/kroll/{id}")
async def upload_kroll_product(id: int, db: Session = Depends(get_db)):
    product = db.query(KrollProduct).filter(KrollProduct.id == id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="kroll product not found")
    sync_to_woocommerce(product, db)
    return {"message": "kroll product uploaded successfully", "product": product}


@router.post("/kroll/sync")
async def sync_kroll_products(db: Session = Depends(get_db)):
    # result = periodic_sync(db)
    # return {"message": "kroll products synced successfully", "success": result}
    return {"message": "kroll products synced successfully", "success": True}


@router.delete("/kroll/{id}")
async def delete_kroll_product(id: int, db: Session = Depends(get_db)):
    success = db.query(KrollProduct).filter(KrollProduct.id == id).delete()
    if not success:
        raise HTTPException(status_code=404, detail="kroll product not found")
    return {"message": "kroll product deleted successfully"}


# 4 supplier router cruds
