"""005: Hash usernames in SVG author signature comments.

Replaces `<!-- 创作者: {username} -->` with `<!-- 创作者: {sha256_hex_16} -->`
to avoid leaking plaintext usernames in exported SVGs.
"""
import hashlib
import re

from sqlalchemy import text

PATTERN = re.compile(r"<!--\s*创作者:\s*(\S+)\s*-->")


def _hash_username(username: str) -> str:
    return hashlib.sha256(username.encode()).hexdigest()[:16]


def upgrade(engine):
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT id, svg_template FROM bubbles WHERE svg_template LIKE '%<!-- 创作者:%'")
        ).fetchall()

    updated = 0
    for row in rows:
        bid, svg = row
        new_svg = PATTERN.sub(lambda m: f"<!-- 创作者: {_hash_username(m.group(1))} -->", svg)
        if new_svg != svg:
            with engine.connect() as conn2:
                conn2.execute(
                    text("UPDATE bubbles SET svg_template = :svg WHERE id = :id"),
                    {"svg": new_svg, "id": bid},
                )
                conn2.commit()
            updated += 1

    print(f"  Hashed usernames in {updated} bubble(s)")
