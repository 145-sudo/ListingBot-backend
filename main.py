from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
import models
from database import engine, get_db, create_tables
from sqlalchemy.orm import Session
from auth import create_access_token, get_current_active_user
from services import ProductService
from auth import authenticate_user
from models.wordpress import WordPressProduct
from models.user import User
from models.products import Product
from fastapi.middleware.cors import CORSMiddleware
from wordpress import WordPressService
from database import Base

# Create database tables
create_tables()

ACCESS_TOKEN_EXPIRE_MINUTES = 1000

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)


# Start WordPress sync in background
from wordpress import get_wp_to_db
# import asyncio
print('get_wp_to_db')
# get_wp_to_db()
# asyncio.create_task(get_wp_to_db(interval=300))  # Sync every 5 minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")



# Authentication endpoints
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    print(form_data.username)
    print(form_data.password)
    user = authenticate_user(db, form_data.username, form_data.password)
    print('user' ,user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    print('access_token_expires',access_token_expires)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    print('access_token',access_token)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user



# Product endpoints
@app.get("/products")
async def get_products(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    skip = (page - 1) * limit
    product_service = ProductService(db)
    products = product_service.get_products(skip, limit)
    total = db.query(Product).count()
    return {"products": products, "total": total, "page": page, "limit": limit}

@app.get("/products/{product_id}")
async def get_product(product_id: int, db: Session = Depends(get_db)):
    product_service = ProductService(db)
    product = product_service.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# WordPress endpoints
@app.get("/wordpress/")
async def get_wordpress_products(page: int = 1, limit: int = 100, db: Session = Depends(get_db)):
    skip = (page - 1) * limit
    products = db.query(WordPressProduct).offset(skip).limit(limit).all()
    total = db.query(WordPressProduct).count()
    return {"data": products, "total": total, "page": page, "limit": limit}

@app.get("/wordpress/{wp_id}")
async def get_wordpress_product(wp_id: int, db: Session = Depends(get_db)):
    product = db.query(WordPressProduct).filter(WordPressProduct.id == wp_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="WordPress product not found")
    return product

@app.post("/wordpress/sync")
async def sync_wordpress_products(db: Session = Depends(get_db)):
    result = periodic_sync(db)
    return {"message": "WordPress products synced successfully", "success": result}

@app.delete("/wordpress/{wp_id}")
async def delete_wordpress_product(wp_id: int, db: Session = Depends(get_db)):
    success = db.query(WordPressProduct).filter(WordPressProduct.id == wp_id).delete()
    if not success:
        raise HTTPException(status_code=404, detail="WordPress product not found")
    return {"message": "WordPress product deleted successfully"}
