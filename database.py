# database.py
import psycopg2
from psycopg2.extras import DictCursor
from config import DB_CONFIG

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.conn.autocommit = True
        self.cursor = self.conn.cursor(cursor_factory=DictCursor)

    def query(self, sql, params=None):
        self.cursor.execute(sql, params)
        return self.cursor

    def close(self):
        self.cursor.close()
        self.conn.close()
