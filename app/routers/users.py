from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..dependencies import get_current_user, get_password_hash
from ..models.user import User
from ..schemas.user import UserCreate, UserResponse

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.get("/", response_model=List[UserResponse])
async def get_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    return db.query(User).all()

@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user)  # Changed this line
):
    # Check if this is the first user
    is_first_user = db.query(User).first() is None
    
    # If not first user, check authorization
    if not is_first_user and (not current_user or not current_user.is_admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already registered")
    
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_admin=user.is_admin if not is_first_user else True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user