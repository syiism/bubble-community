from sqlalchemy import Column, BigInteger, String, DateTime
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    username = Column(String(64), nullable=False, unique=True)
    username_updated_at = Column(DateTime, nullable=True)
    author_name = Column(String(32), nullable=True, unique=True)
    avatar_url = Column(String(255), nullable=True)
    password = Column(String(255), nullable=True)
    role = Column(String(32), nullable=False, default="user")
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    updated_at = Column(
        DateTime,
        nullable=False,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
