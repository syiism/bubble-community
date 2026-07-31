from sqlalchemy import Column, BigInteger, DateTime, String
from sqlalchemy.sql import func

from .database import Base


class UserCurrentBubble(Base):
    __tablename__ = "user_current_bubble"

    user_id = Column(BigInteger, primary_key=True)
    bubble_id = Column(BigInteger, nullable=False)
    custom_color = Column(String(32), nullable=True)
    custom_text_color = Column(String(32), nullable=True)
    custom_font_family = Column(String(64), nullable=True)
    custom_text = Column(String(64), nullable=True)
    custom_size = Column(String(16), nullable=True)
    set_at = Column(
        DateTime,
        nullable=False,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
