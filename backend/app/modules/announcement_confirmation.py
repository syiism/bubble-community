from sqlalchemy import Column, Integer, BigInteger, DateTime, UniqueConstraint
from sqlalchemy.sql import func

from .database import Base


class AnnouncementConfirmation(Base):
    __tablename__ = "announcement_confirmations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    announcement_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=func.current_timestamp())

    __table_args__ = (
        UniqueConstraint("user_id", "announcement_id", name="uq_user_announcement"),
    )
