from datetime import datetime
import uuid
from typing import Optional

from fastapi_users import schemas
from pydantic import BaseModel


class UserRead(schemas.BaseUser[int]):
    id: int
    email: str
    full_name: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False

    class Config:
        orm_mode = True


class UserCreate(schemas.BaseUserCreate):
    full_name: str
    email: str
    username: str
    password: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False

class BoardBase(BaseModel):
    name: str
    public: bool


class BoardCreate(BoardBase):
    pass


class BoardRead(BoardBase):
    id: int
    creator_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class PostBase(BaseModel):
    title: str
    content: str


class PostCreate(PostBase):
    pass


class PostRead(PostBase):
    id: int
    creator_id: int
    board_id: int
    created_at: datetime

    class Config:
        orm_mode = True