from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth_router, users_router, chores_router

app = FastAPI(
    root_path="/api",  
    title="Chores Tracker API",
    description="API for tracking children's chores and rewards",
    version="1.0.0",
    openapi_url="/openapi.json",  # Changed from /api/openapi.json
    docs_url="/docs",             # Changed from /api/docs
    redoc_url="/redoc"            # Changed from /api/redoc
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include routers
app.include_router(auth_router, prefix="")
app.include_router(users_router, prefix="")
app.include_router(chores_router, prefix="")
