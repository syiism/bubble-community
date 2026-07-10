from sqlalchemy import Column, BigInteger, DateTime
from sqlalchemy.sql import func

from .database import Base


class UserFavorite(Base):
    __tablename__ = "user_favorites"

    user_id = Column(BigInteger, primary_key=True)
    bubble_id = Column(BigInteger, primary_key=True)
    favorited_at = Column(DateTime, nullable=False, default=func.current_timestamp())
