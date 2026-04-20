import sqlite3

DB_NAME = "bom_data.db"


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS recipes (
            parent_item TEXT,
            child_item TEXT,
            qty_per_unit REAL,
            PRIMARY KEY (parent_item, child_item)
        )
        """)
        self.conn.commit()

    def add_or_update(self, parent, child, qty):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO recipes (parent_item, child_item, qty_per_unit)
        VALUES (?, ?, ?)
        """, (parent, child, qty))
        self.conn.commit()

    def delete(self, parent, child):
        cursor = self.conn.cursor()
        cursor.execute("""
        DELETE FROM recipes WHERE parent_item=? AND child_item=?
        """, (parent, child))
        self.conn.commit()

    def get_all(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT parent_item, child_item, qty_per_unit FROM recipes")
        return cursor.fetchall()

    def get_children(self, parent):
        cursor = self.conn.cursor()
        cursor.execute("""
        SELECT child_item, qty_per_unit FROM recipes WHERE parent_item=?
        """, (parent,))
        return cursor.fetchall()

    def is_parent(self, item):
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM recipes WHERE parent_item=? LIMIT 1", (item,))
        return cursor.fetchone() is not None