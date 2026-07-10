from sqlalchemy import Column, BigInteger, String, Text, Boolean, DateTime, Index
from sqlalchemy.sql import func

from .database import Base


class Bubble(Base):
    __tablename__ = "bubbles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=True)
    name = Column(String(64), nullable=False)
    description = Column(String(120), nullable=False, default="")
    svg_template = Column(Text, nullable=False)
    color = Column(String(32), nullable=False, default="")
    text_color = Column(String(32), nullable=False, default="")
    is_public = Column(Boolean, nullable=False, default=False)
    is_official = Column(Boolean, nullable=False, default=False)
    share_code = Column(String(32), nullable=True, unique=True)
    author_name = Column(String(32), nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    updated_at = Column(
        DateTime,
        nullable=False,
        default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    __table_args__ = (
        Index("idx_bubbles_user", "user_id"),
        Index("idx_bubbles_public", "is_public"),
        Index("idx_bubbles_official", "is_official"),
    )
