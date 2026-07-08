from contextlib import contextmanager
import pymysql

from .config import DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME


def open_connection(database: str = DB_NAME):
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=database,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )


@contextmanager
def get_conn(database: str = DB_NAME):
    conn = open_connection(database)
    try:
        yield conn
    finally:
        conn.close()
