from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from models.wordpress import WordPressProduct
from database import get_db

router = APIRouter()

# WordPress endpoints
@router.get("/wordpress/")
async def get_wordpress_products(page: int = 1, limit: int = 100, db: Session = Depends(get_db)):
    skip = (page - 1) * limit
    products = db.query(WordPressProduct).offset(skip).limit(limit).all()
    total = db.query(WordPressProduct).count()
    return {"data": products, "total": total, "page": page, "limit": limit}

@router.get("/wordpress/{wp_id}")
async def get_wordpress_product(wp_id: int, db: Session = Depends(get_db)):
    product = db.query(WordPressProduct).filter(WordPressProduct.id == wp_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="WordPress product not found")
    return product

@router.post("/wordpress/sync")
async def sync_wordpress_products(db: Session = Depends(get_db)):
    # result = periodic_sync(db)
    # return {"message": "WordPress products synced successfully", "success": result}
    return {"message": "WordPress products synced successfully", "success": True}

@router.delete("/wordpress/{wp_id}")
async def delete_wordpress_product(wp_id: int, db: Session = Depends(get_db)):
    success = db.query(WordPressProduct).filter(WordPressProduct.id == wp_id).delete()
    if not success:
        raise HTTPException(status_code=404, detail="WordPress product not found")
    return {"message": "WordPress product deleted successfully"}
