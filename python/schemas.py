from pydantic import BaseModel, EmailStr
from typing import Optional

class UserBase(BaseModel):
    login: str
    email: str

class CreateUser(UserBase):
    password: str

class UserResponse(UserBase):
    id_user: int

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    login: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None