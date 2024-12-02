from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from . import models
from .routers import chores
from loguru import logger
import sys

# Configure Loguru
logger.remove()
logger.add(
    sys.stdout,
    format="{time} {level} {message}",
    level="INFO",
    serialize=True  # JSON format for better integration with Loki
)

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Chores Tracker API")

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router
app.include_router(chores.router)

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}