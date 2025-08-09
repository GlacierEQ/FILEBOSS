from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False

# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)

# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=8, max_length=100)

# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Properties to return to client
class User(UserInDBBase):
    pass

# Properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str

# Item schemas
class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None

class ItemCreate(ItemBase):
    pass

class ItemUpdate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
