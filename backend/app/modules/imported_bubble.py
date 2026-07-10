from sqlalchemy import Column, BigInteger, DateTime
from sqlalchemy.sql import func

from .database import Base


class ImportedBubble(Base):
    __tablename__ = "imported_bubbles"

    user_id = Column(BigInteger, primary_key=True)
    bubble_id = Column(BigInteger, primary_key=True)
    imported_at = Column(DateTime, nullable=False, default=func.current_timestamp())
