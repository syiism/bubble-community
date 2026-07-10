from sqlalchemy import Column, BigInteger, String

from .database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(32), nullable=False, unique=True)
    description = Column(String(255), nullable=False, default="")
