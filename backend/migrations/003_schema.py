"""003: Schema v1 — historical additive column migrations.

Includes all columns that were added to existing tables over time,
merged from seed.py migrate_schema() and database.py _COLUMN_MIGRATIONS.
"""
from sqlalchemy import text


def upgrade(engine):
    with engine.connect() as conn:
        # password
        r = conn.execute(text("SHOW COLUMNS FROM users LIKE 'password'"))
        if not r.fetchone():
            conn.execute(text("ALTER TABLE users ADD COLUMN password VARCHAR(255) DEFAULT NULL AFTER avatar_url"))

        # role
        r = conn.execute(text("SHOW COLUMNS FROM users LIKE 'role'"))
        if not r.fetchone():
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'user' AFTER password"))

        # username_updated_at
        r = conn.execute(text("SHOW COLUMNS FROM users LIKE 'username_updated_at'"))
        if not r.fetchone():
            conn.execute(text("ALTER TABLE users ADD COLUMN username_updated_at DATETIME DEFAULT NULL AFTER username"))

        # is_blocked + blocked_at
        r = conn.execute(text("SHOW COLUMNS FROM users LIKE 'is_blocked'"))
        if not r.fetchone():
            conn.execute(text("ALTER TABLE users ADD COLUMN is_blocked TINYINT(1) NOT NULL DEFAULT 0 AFTER role"))
            conn.execute(text("ALTER TABLE users ADD COLUMN blocked_at DATETIME DEFAULT NULL AFTER is_blocked"))

        # visibility_modified_by
        r = conn.execute(text("SHOW COLUMNS FROM bubbles LIKE 'visibility_modified_by'"))
        if not r.fetchone():
            conn.execute(text("ALTER TABLE bubbles ADD COLUMN visibility_modified_by INT DEFAULT NULL AFTER is_official"))

        # category
        r = conn.execute(text("SHOW COLUMNS FROM bubbles LIKE 'category'"))
        if not r.fetchone():
            conn.execute(text("ALTER TABLE bubbles ADD COLUMN category VARCHAR(32) NOT NULL DEFAULT 'original' AFTER is_official"))

        # share_code UNIQUE index
        r = conn.execute(text("SHOW INDEX FROM bubbles WHERE Column_name = 'share_code' AND Non_unique = 0"))
        if not r.fetchone():
            conn.execute(text("CREATE UNIQUE INDEX idx_bubbles_share_code ON bubbles(share_code)"))

        # category index
        r = conn.execute(text("SHOW INDEX FROM bubbles WHERE Column_name = 'category'"))
        if not r.fetchone():
            conn.execute(text("CREATE INDEX idx_bubbles_category ON bubbles(category)"))

        conn.commit()
