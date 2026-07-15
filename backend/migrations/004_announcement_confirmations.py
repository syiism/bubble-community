"""004: Create announcement_confirmations table."""
from sqlalchemy import text


def upgrade(engine):
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS announcement_confirmations (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT NOT NULL,
                announcement_id INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uq_user_announcement (user_id, announcement_id),
                INDEX idx_user_id (user_id),
                INDEX idx_announcement_id (announcement_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """))
        conn.commit()
