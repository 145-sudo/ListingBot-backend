from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.ssi import SsiProduct
from database import get_db

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


@router.get("/ssi/{item_id}")
async def get_ssi_product(item_id: int, db: Session = Depends(get_db)):
    
    product = db.query(SsiProduct).filter(SsiProduct.item_id == item_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="ssi product not found")
    return product


@router.post("/ssi/sync")
async def sync_ssi_products(db: Session = Depends(get_db)):
    # result = periodic_sync(db)
    # return {"message": "ssi products synced successfully", "success": result}
    return {"message": "ssi products synced successfully", "success": True}


@router.delete("/ssi/{item_id}")
async def delete_ssi_product(item_id: int, db: Session = Depends(get_db)):
    success = db.query(SsiProduct).filter(SsiProduct.item_id == item_id).delete()
    if not success:
        raise HTTPException(status_code=404, detail="ssi product not found")
    return {"message": "ssi product deleted successfully"}

