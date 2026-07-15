"""002: Create all tables from ORM metadata."""
from app.modules.database import Base


def upgrade(engine):
    Base.metadata.create_all(engine)
