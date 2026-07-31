"""007: Per-user bubble size setting (large/small).

Adds custom_size VARCHAR(16) NULL to user_current_bubble.
'large' -> <TEXT> tags, 'small' -> <text> tags in get-bubble output.
"""
from sqlalchemy import text


def upgrade(engine):
    with engine.connect() as conn:
        r = conn.execute(text("SHOW COLUMNS FROM user_current_bubble LIKE 'custom_size'"))
        if not r.fetchone():
            conn.execute(text(
                "ALTER TABLE user_current_bubble ADD COLUMN custom_size VARCHAR(16) DEFAULT NULL AFTER custom_text"
            ))
        conn.commit()
