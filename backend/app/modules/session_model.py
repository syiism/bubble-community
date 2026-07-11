from sqlalchemy import Column, BigInteger, String, DateTime, Index
from sqlalchemy.sql import func

from .database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    username = Column(String(64), nullable=False)
    device_info = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())
    last_seen_at = Column(DateTime, nullable=True, default=func.current_timestamp())

    __table_args__ = (
        Index("idx_sessions_user", "user_id"),
        Index("idx_sessions_expires", "expires_at"),
    )
