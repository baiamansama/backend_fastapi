from datetime import datetime

from sqlalchemy import MetaData, Table, Column, Integer, String, TIMESTAMP, ForeignKey, JSON, Boolean

metadata = MetaData()

user = Table(
    "user",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, nullable=False),
    Column("username", String, nullable=False),
    Column("full_name", String, nullable=False),
    Column("hashed_password", String, nullable=False),
    Column("is_active", Boolean, default=True, nullable=False),
    Column("is_superuser", Boolean, default=False, nullable=False),
    Column("is_verified", Boolean, default=False, nullable=False),
)

board = Table(
    "board",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False, unique=True),
    Column("public", Boolean, default=True, nullable=False),
    Column("creator_id", Integer, ForeignKey("user.id"), nullable=False),
    Column("created_at", TIMESTAMP, default=datetime.utcnow, nullable=False),
)

post = Table(
    "post",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String, nullable=False),
    Column("content", String, nullable=False),
    Column("creator_id", Integer, ForeignKey("user.id"), nullable=False),
    Column("board_id", Integer, ForeignKey("board.id"), nullable=False),
    Column("created_at", TIMESTAMP, default=datetime.utcnow, nullable=False),
)