from sqlalchemy import Column, BigInteger, DateTime
from sqlalchemy.sql import func

from .database import Base


class UserCurrentBubble(Base):
    __tablename__ = "user_current_bubble"

    user_id = Column(BigInteger, primary_key=True)
    bubble_id = Column(BigInteger, nullable=False)
    set_at = Column(
        DateTime,
        nullable=False,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
