from datetime import datetime
from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, TIMESTAMP
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import DeclarativeBase

from config import DB_HOST, DB_NAME, DB_PASS, DB_PORT, DB_USER
from models.models import user

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
Base: DeclarativeMeta = declarative_base()

class Base(DeclarativeBase):
    pass


class User(SQLAlchemyBaseUserTable[int], Base):
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    username = Column(String, nullable=False)
    hashed_password: str = Column(String(length=1024), nullable=False)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    is_superuser: bool = Column(Boolean, default=False, nullable=False)
    is_verified: bool = Column(Boolean, default=False, nullable=False)

class Board(Base):
    __tablename__ = "board"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    public = Column(Boolean, default=True, nullable=False)
    creator_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

class Post(Base):
    __tablename__ = "post"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    content = Column(String, nullable=False)
    creator_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    board_id = Column(Integer, ForeignKey("board.id"), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

engine = create_async_engine(DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)


async def create_db_and_tables():
    async with engine.begin() as conn:
        print("creating tables.....")
        await conn.run_sync(Base.metadata.create_all)
        print("tables created!")


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
