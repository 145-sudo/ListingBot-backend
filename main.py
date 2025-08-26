import asyncio
import logging
from datetime import timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_utils.tasks import repeat_every
from sqlalchemy.orm import Session

from auth import authenticate_user, create_access_token, get_current_active_user
from database import create_tables, get_db
from models.user import User
from routers import kroll, rothco, ssi, wp
from scheduler import run_tasks
from seeder import seed_user

# Create database tables
create_tables()
seed_user()

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

# from services.background_tasks import task_manager

# class Server(uvicorn.Server):
#     """Customized uvicorn.Server to handle Rocketry shutdown"""
#     def handle_exit(self, sig: int, frame) -> None:
#         # app_rocketry.session.shut_down()
#         return super().handle_exit(sig, frame)

# async def main():
#     """Run scheduler and the API"""
#     server = Server(config=uvicorn.Config(app, workers=1, loop="asyncio"))

#     api = asyncio.create_task(server.serve())
#     # scheduler = asyncio.create_task(app_rocketry.serve())

#     # await asyncio.wait([scheduler, api])
#     await asyncio.wait([api])


@app.on_event("startup")
@repeat_every(wait_first=15, seconds=60 * 60)  # 1 hour
async def schedules() -> None:
    logging.info("Tasks started")
    await asyncio.to_thread(run_tasks)
    logging.info("Tasks Finished")


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
