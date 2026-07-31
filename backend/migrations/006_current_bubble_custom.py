"""006: Per-user custom settings for the currently selected bubble.

Adds 4 nullable columns to user_current_bubble:
custom_color / custom_text_color / custom_font_family / custom_text.
Used by GET /api/bubbles/get-bubble to fill {c}/{t}/{n} placeholders
and font-family before returning the SVG to downstream platforms.
"""
from sqlalchemy import text


def upgrade(engine):
    with engine.connect() as conn:
        columns = [
            ("custom_color", "VARCHAR(32) DEFAULT NULL"),
            ("custom_text_color", "VARCHAR(32) DEFAULT NULL"),
            ("custom_font_family", "VARCHAR(64) DEFAULT NULL"),
            ("custom_text", "VARCHAR(64) DEFAULT NULL"),
        ]
        for name, ddl in columns:
            r = conn.execute(text(f"SHOW COLUMNS FROM user_current_bubble LIKE '{name}'"))
            if not r.fetchone():
                conn.execute(text(f"ALTER TABLE user_current_bubble ADD COLUMN {name} {ddl} AFTER bubble_id"))

        conn.commit()
