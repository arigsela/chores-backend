from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_admin: bool = False

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: str | None = None

class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str