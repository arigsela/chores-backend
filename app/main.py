from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth_router, users_router, chores_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Include routers
app.include_router(auth_router)
app.include_router(users_router, prefix="/api")
app.include_router(chores_router, prefix="/api")

