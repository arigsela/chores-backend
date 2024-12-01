from fastapi import FastAPI
from loguru import logger
import sys

# Configure Loguru for JSON logging (works well with Loki)
logger.remove()
logger.add(
    sys.stdout,
    format="{time} {level} {message}",
    level="INFO",
    serialize=True
)

app = FastAPI(title="Chores Tracker API")

@app.get("/health")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"status": "healthy"}
