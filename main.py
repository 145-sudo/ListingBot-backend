import asyncio
from datetime import timedelta
import logging

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth import authenticate_user, create_access_token, get_current_active_user
from database import create_tables, get_db
from models.user import User
from routers import wp, kroll, ssi, rothco
from services.suppliers import scrape_save_supplier_products
from config import SheetName

# Create database tables
create_tables()

# Logging configuration
# Configure logging to file
logging.basicConfig(
    filename="inventory_sync.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Add logging to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logging.getLogger().addHandler(console)


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
from services.wordpress import get_wp_to_db, sync_and_update_products
# get_wp_to_db()
asyncio.create_task(get_wp_to_db(interval=300))  # Sync every 5 minutes 

# Fetch Only Supplier Products
# asyncio.create_task(scrape_save_supplier_products(SheetName.KROLL.value))
asyncio.create_task(scrape_save_supplier_products(SheetName.SSI.value))

# Start the new sync and update task
asyncio.create_task(sync_and_update_products(interval=300)) # Sync every 5 minutes

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Authentication endpoints
@app.post("/token")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
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
app.include_router(kroll.router, tags=["Kroll"])
app.include_router(ssi.router, tags=["Ssi"])
app.include_router(rothco.router, tags=["Rothco"])
