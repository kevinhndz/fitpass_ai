import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from database import Base, engine
from routers import auth, clientes, web
from scheduler import iniciar_scheduler
import tablas  # noqa: F401

BASE_DIR = Path(__file__).resolve().parent

@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    scheduler = iniciar_scheduler()
    yield
    scheduler.shutdown(wait=False)

app = FastAPI(title="FitPass API", version="2.0.0", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=os.getenv("FLASK_SECRET_KEY", "fitpass-dev-key"))
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(auth.router)
app.include_router(web.router)
app.include_router(clientes.router)
