from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from database.db import init_db
from api.routes import auth, ads, search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting API server...")
    await init_db()
    yield
    logger.info("Shutting down API server...")

app = FastAPI(
    title="Auto Ads API",
    description="API для Telegram Mini App по продаже автомобилей",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(ads.router, prefix="/api/ads", tags=["ads"])
app.include_router(search.router, prefix="/api/search", tags=["search"])

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "API is running"}

@app.get("/api/version")
async def version():
    return {"version": "1.0.0", "name": "Auto Ads API"}