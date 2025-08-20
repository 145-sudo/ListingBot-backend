import asyncio
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from database import get_db, create_tables
from sqlalchemy.orm import Session
from auth import create_access_token, get_current_active_user
from auth import authenticate_user
from legacy.config import SheetName
# from legacy.util.func import fetch_only_supplier_products
from models.user import User
from fastapi.middleware.cors import CORSMiddleware
from routers import wp

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
# from wordpress import get_wp_to_db
# import asyncio
# get_wp_to_db()
# asyncio.create_task(get_wp_to_db(interval=300))  # Sync every 5 minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Fetch Only Supplier Products
# asyncio.create_task(fetch_only_supplier_products(SheetName.KROLL.value))

# Authentication endpoints
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me")
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user

# Include WordPress router
app.include_router(wp.router, tags=["WordPress"])

