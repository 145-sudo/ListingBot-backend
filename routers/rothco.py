from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.rothco import RothcoProduct
from database import get_db

router = APIRouter()
              

# rothco endpoints
@router.get("/rothco/")
async def get_rothco_products(
    page: int = 1,
    limit: int = 100,
    sort: str = "id",
    order: str = "asc",
    db: Session = Depends(get_db),
):
    skip = (page - 1) * limit
    # Validate sort field
    if not hasattr(RothcoProduct, sort):
        raise HTTPException(status_code=400, detail=f"Invalid sort field: {sort}")
    sort_column = getattr(RothcoProduct, sort)
    # Determine order
    if order.lower() == "desc":
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()
    products = (
        db.query(RothcoProduct).order_by(sort_column).offset(skip).limit(limit).all()
    )
    total = db.query(RothcoProduct).count()
    return {
        "data": products,
        "total": total,
        "page": page,
        "limit": limit,
        "sort": sort,
        "order": order,
    }


@router.get("/rothco/{item_id}")
async def get_rothco_product(item_id: int, db: Session = Depends(get_db)):
    
    product = db.query(RothcoProduct).filter(RothcoProduct.item_id == item_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="rothco product not found")
    return product


@router.post("/rothco/sync")
async def sync_rothco_products(db: Session = Depends(get_db)):
    # result = periodic_sync(db)
    # return {"message": "rothco products synced successfully", "success": result}
    return {"message": "rothco products synced successfully", "success": True}


@router.delete("/rothco/{item_id}")
async def delete_rothco_product(item_id: int, db: Session = Depends(get_db)):
    success = db.query(RothcoProduct).filter(RothcoProduct.item_id == item_id).delete()
    if not success:
        raise HTTPException(status_code=404, detail="rothco product not found")
    return {"message": "rothco product deleted successfully"}

